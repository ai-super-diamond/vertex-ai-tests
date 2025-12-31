import time
import random
import logging
import uuid
from datetime import datetime
import sys
import argparse
import subprocess
import os

import google.cloud.aiplatform as aiplatform
from google import genai

# --- Configuration ---
import json
from vertex_benchmark.config import PROJECT_ID, EUROPEAN_LOCATIONS, WORLDWIDE_LOCATIONS, MODELS, TEST_PROMPTS, MIN_DELAY_SECONDS, MAX_DELAY_SECONDS, APP_VERSION
from vertex_benchmark.database_utils import create_tables, insert_benchmark_result, DB_FILE, get_db_connection, begin_batch, end_batch

# --- Logger Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("benchmark.log"),
        logging.StreamHandler()
    ]
)

# Calculate number of cycles based on prompts
NUM_CYCLES = len(TEST_PROMPTS)

# Retry and timeout settings for model calls
MAX_RETRIES = 3
REQUEST_TIMEOUT_SECONDS = 30
RETRY_BACKOFF_SECONDS = 2

def _generate_with_retries(client, model_name, prompt):
    """Call generate_content with retries and a timeout; returns (time_ms, error)."""
    call_kwargs = {"model": model_name, "contents": prompt}
    # Add request_options timeout when supported by the SDK
    call_kwargs_with_timeout = dict(call_kwargs)
    call_kwargs_with_timeout["request_options"] = {"timeout": REQUEST_TIMEOUT_SECONDS}

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            start_time = time.time()
            try:
                response = client.models.generate_content(**call_kwargs_with_timeout)
            except TypeError:
                # SDK may not accept request_options; retry without it
                response = client.models.generate_content(**call_kwargs)
            end_time = time.time()
            elapsed_ms = round((end_time - start_time) * 1000, 2)
            return elapsed_ms, None
        except Exception as e:
            if attempt == MAX_RETRIES:
                return None, e
            backoff = RETRY_BACKOFF_SECONDS * attempt
            logging.warning(f"      Retry {attempt}/{MAX_RETRIES} for model '{model_name}' after error: {e}")
            time.sleep(backoff)


def validate_configuration(locations):
    """Validate the configuration settings."""
    errors = []

    # Check PROJECT_ID
    if not PROJECT_ID or PROJECT_ID == "your-project-id":
        errors.append("PROJECT_ID is not set or is using the default placeholder value")

    # Check locations
    if not locations or len(locations) == 0:
        errors.append("LOCATIONS is empty or not defined")

    # Check MODELS
    if not MODELS or "Pro" not in MODELS or "Flash" not in MODELS:
        errors.append("MODELS configuration is missing Pro or Flash model lists")

    # Check TEST_PROMPTS
    if not TEST_PROMPTS or len(TEST_PROMPTS) == 0:
        errors.append("TEST_PROMPTS is empty or not defined")

    # Check delay settings
    if MIN_DELAY_SECONDS < 0 or MAX_DELAY_SECONDS < 0:
        errors.append("Delay settings cannot be negative")
    if MIN_DELAY_SECONDS > MAX_DELAY_SECONDS:
        errors.append("MIN_DELAY_SECONDS cannot be greater than MAX_DELAY_SECONDS")

    return errors

def run_benchmark(mode, locations, include_model_counts=False):
    """Run the benchmark for the given mode and locations."""

    # Validate configuration
    config_errors = validate_configuration(locations)
    if config_errors:
        logging.error("Configuration validation failed:")
        for error in config_errors:
            logging.error(f"  - {error}")
        sys.exit(1)

    logging.info("=" * 60)
    logging.info(f"Vertex AI {mode.title()} Regions Benchmark")
    logging.info("=" * 60)
    logging.info(f"Project: {PROJECT_ID}")
    logging.info(f"Testing {len(locations)} {mode.lower()} locations")
    logging.info(f"Running {NUM_CYCLES} cycles per region")
    logging.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info("=" * 60)
    logging.info("")

    # Ensure database tables exist
    create_tables()

    # Generate a unique batch ID for this benchmark run
    BATCH_ID = str(uuid.uuid4())
    logging.info(f"Benchmark Batch ID: {BATCH_ID}")
    logging.info(f"Include model counts: {include_model_counts}")

    # Snapshot config for metadata
    config_snapshot = {
        "project_id": PROJECT_ID,
        "regions": locations,
        "models": MODELS,
        "test_prompts": TEST_PROMPTS,
        "min_delay_seconds": MIN_DELAY_SECONDS,
        "max_delay_seconds": MAX_DELAY_SECONDS,
    }
    config_json = json.dumps(config_snapshot)

    # Initialize database connection and batch
    try:
        # Open one DB connection and begin batch metadata
        conn = get_db_connection()
        begin_batch(BATCH_ID, APP_VERSION, config_json, conn=conn)
    except Exception as e:
        logging.error(f"Failed to initialize database: {e}")
        sys.exit(1)

    results = [] # Keep for in-memory summary, but actual storage is DB

    # Track overall statistics
    stats = {
        "total_requests": 0,
        "successful_requests": 0,
        "failed_requests": 0,
        "pro_success": 0,
        "flash_success": 0,
        "regions_completed": 0
    }

    for location in locations:
        logging.info(f"\n[{location}] Starting tests...")

        # Create client once per region
        client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location=location
        )

        # Count Garden Models once per region (not per cycle)
        garden_model_count = None
        if include_model_counts:
            try:
                logging.info("  Counting models...")
                aiplatform.init(project=PROJECT_ID, location=location)
                models = aiplatform.Model.list()
                garden_model_count = len(models)
                logging.info(f"    ✓ Models: {garden_model_count}")
            except Exception as e:
                garden_model_count = None
                logging.error(f"    ✗ Model count failed: {str(e)[:100]}")
        else:
            logging.info("  Model counting skipped (default)")

        # Run all prompt cycles for this region
        region_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "pro_success": 0,
            "flash_success": 0
        }

        for cycle_num, test_prompt in enumerate(TEST_PROMPTS, start=1):
            # Add a random delay
            delay = random.uniform(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS)
            logging.info(f"Waiting for {delay:.2f} seconds before next request...")
            time.sleep(delay)

            logging.info(f"\n  [Cycle {cycle_num}/{NUM_CYCLES}] Testing with prompt: '{test_prompt[:50]}...'")

            # Initialize result for in-memory summary and database insertion
            pro_time_ms = None
            flash_time_ms = None
            pro_error_text = None
            flash_error_text = None

            result = {
                "#Cycle": cycle_num,
                "region": location,
                "Pro": "N/A", # For in-memory summary
                "Flash": "N/A", # For in-memory summary
                "Garden Models": garden_model_count if garden_model_count is not None else "Error"
            }

            # Update stats
            stats["total_requests"] += 2  # One for Pro, one for Flash
            region_stats["total_requests"] += 2

            # Test Gemini Pro response time - try multiple model names
            pro_success = False
            for model_name in MODELS["Pro"]:
                pro_time_ms, error = _generate_with_retries(client, model_name, test_prompt)
                if pro_time_ms is not None:
                    result["Pro"] = f"{pro_time_ms}ms" # For in-memory summary
                    logging.info(f"    ✓ Pro ({model_name}): {pro_time_ms}ms")

                    # Update stats
                    stats["successful_requests"] += 1
                    stats["pro_success"] += 1
                    region_stats["successful_requests"] += 1
                    region_stats["pro_success"] += 1
                    pro_success = True
                    break
                else:
                    pro_error_text = str(error)
                    logging.warning(f"    Pro model '{model_name}' failed: {error}")
                    continue

            if not pro_success:
                result["Pro"] = "Not Available" # For in-memory summary
                logging.warning(f"    ✗ Pro: No models available")
                stats["failed_requests"] += 1
                region_stats["failed_requests"] += 1

            # Test Gemini Flash response time - try multiple model names
            flash_success = False
            for model_name in MODELS["Flash"]:
                flash_time_ms, error = _generate_with_retries(client, model_name, test_prompt)
                if flash_time_ms is not None:
                    result["Flash"] = f"{flash_time_ms}ms" # For in-memory summary
                    logging.info(f"    ✓ Flash ({model_name}): {flash_time_ms}ms")

                    # Update stats
                    stats["successful_requests"] += 1
                    stats["flash_success"] += 1
                    region_stats["successful_requests"] += 1
                    region_stats["flash_success"] += 1
                    flash_success = True
                    break
                else:
                    flash_error_text = str(error)
                    logging.warning(f"    Flash model '{model_name}' failed: {error}")
                    continue

            if not flash_success:
                result["Flash"] = "Not Available" # For in-memory summary
                logging.warning(f"    ✗ Flash: No models available")
                stats["failed_requests"] += 1
                region_stats["failed_requests"] += 1

            # Insert result into the database
            insert_benchmark_result(
                BATCH_ID,
                datetime.now(),
                cycle_num,
                location,
                pro_time_ms,
                flash_time_ms,
                garden_model_count,
                test_prompt,
                pro_error_text,
                flash_error_text,
                conn=conn
            )
            results.append(result) # Still append to results for the in-memory summary at the end

        logging.info(f"[{location}] Completed all {NUM_CYCLES} cycles")
        logging.info(f"  Region Stats - Success: {region_stats['successful_requests']}/{region_stats['total_requests']}, "
                        f"Pro: {region_stats['pro_success']}, Flash: {region_stats['flash_success']}")
        stats["regions_completed"] += 1

    # Finalize batch: set end timestamp and commit
    try:
        end_batch(BATCH_ID, conn=conn)
        conn.commit()
    except Exception as e:
        logging.error(f"Failed to finalize batch: {e}")
        conn.rollback()
    finally:
        if conn:
            conn.close()

    logging.info("\n" + "=" * 60)
    logging.info(f"Benchmark results saved to database: {DB_FILE}")
    logging.info(f"✓ Total records: {len(results)} ({len(locations)} regions × {NUM_CYCLES} cycles)")
    logging.info(f"Overall Stats - Success: {stats['successful_requests']}/{stats['total_requests']}, "
                    f"Pro: {stats['pro_success']}, Flash: {stats['flash_success']}, "
                    f"Regions: {stats['regions_completed']}/{len(locations)}")
    logging.info("=" * 60)

    # Display summary table (showing first cycle for each region)
    logging.info("\nSummary (Cycle 1 results):")
    logging.info("-" * 80)
    logging.info(f"{'Region':<20} {'Cycle':<8} {'Pro':<15} {'Flash':<15} {'Models':<10}")
    logging.info("-" * 80)
    for result in results:
        if result['#Cycle'] == 1:
            logging.info(
                f"{result['region']:<20} {result['#Cycle']:<8} {result['Pro']:<15} {result['Flash']:<15} {result['Garden Models']:<10}")
    logging.info("-" * 80)
    logging.info(f"\n✓ Benchmark complete! {len(results)} total measurements recorded.")
    logging.info(f"  ({len(locations)} regions × {NUM_CYCLES} cycles)")

    return BATCH_ID

def generate_pdf():
    """Generate PDF report."""
    logging.info("\nGenerating PDF report...")
    try:
        # Use module invocation so it works regardless of CWD
        subprocess.run([sys.executable, "-m", "vertex_benchmark.generate_report"], check=True)
        logging.info("PDF report generated successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to generate PDF: {e}")
        sys.exit(1)

def launch_dashboard():
    """Launch the dashboard."""
    logging.info("\nLaunching dashboard...")
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard.py")
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", dashboard_path, "--server.headless", "true"], check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to launch dashboard: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Vertex AI Benchmark Engine")
    parser.add_argument("mode", choices=["european", "worldwide"], help="Benchmark mode: european or worldwide")
    parser.add_argument("--skip-pdf", action="store_true", help="Skip PDF generation after benchmark")
    parser.add_argument("--skip-dashboard", action="store_true", help="Skip launching dashboard after benchmark")
    parser.add_argument("--include-model-counts", action="store_true", help="List models per region to record counts (slower, higher quota)")
    args = parser.parse_args()

    mode = args.mode
    if mode == "european":
        locations = EUROPEAN_LOCATIONS
        logging.info(f"Using European locations: {len(locations)} regions")
    elif mode == "worldwide":
        locations = WORLDWIDE_LOCATIONS
        logging.info(f"Using Worldwide locations: {len(locations)} regions")

    # Run benchmark
    batch_id = run_benchmark(mode, locations, include_model_counts=args.include_model_counts)

    # Generate PDF unless skipped
    if args.skip_pdf:
        logging.info("PDF generation skipped by flag")
    else:
        generate_pdf()

    # Launch dashboard unless skipped
    if args.skip_dashboard:
        logging.info("Dashboard launch skipped by flag")
    else:
        launch_dashboard()

if __name__ == "__main__":
    main()