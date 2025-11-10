import csv
import os
import time
from datetime import datetime

import google.cloud.aiplatform as aiplatform
from google import genai

# --- Configuration ---
PROJECT_ID = "vertex-ai-project-skorec"

# European Vertex AI locations
EUROPEAN_LOCATIONS = [
    "europe-west1",  # Belgium
    "europe-west2",  # London
    "europe-west3",  # Frankfurt
    "europe-west4",  # Netherlands
    "europe-west6",  # Zurich
    "europe-west8",  # Milan
    "europe-west9",  # Paris
    "europe-north1",  # Finland
    "europe-central2",  # Warsaw
    "europe-southwest1"  # Madrid
]

# Note: US regions are excluded due to slower performance
# Only European regions are benchmarked

# Models to test - Gemini 2.5 Pro and Flash
MODELS = {
    "Pro": ["gemini-2.5-pro", "gemini-2.5-pro-exp", "gemini-2.5-pro-002", "gemini-pro-2.5"],
    "Flash": ["gemini-2.5-flash", "gemini-2.5-flash-exp", "gemini-2.5-flash-002", "gemini-flash-2.5"]
}

# Test prompts - 10 different prompts for comprehensive benchmarking
TEST_PROMPTS = [
    "Hello, respond with just 'OK'",
    "What is 2+2? Answer briefly.",
    "Name one color.",
    "Say 'test' in response.",
    "What day comes after Monday?",
    "Count from 1 to 3.",
    "What is the capital of France?",
    "Translate 'hello' to Spanish.",
    "What is the opposite of hot?",
    "Name one programming language."
]

# Calculate number of cycles based on prompts
NUM_CYCLES = len(TEST_PROMPTS)

print("=" * 60)
print("Vertex AI European Regions Benchmark")
print("=" * 60)
print(f"Project: {PROJECT_ID}")
print(f"Testing {len(EUROPEAN_LOCATIONS)} European locations")
print(f"Running {NUM_CYCLES} cycles per region")
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)
print()

results = []

for location in EUROPEAN_LOCATIONS:
    print(f"\n[{location}] Starting tests...")

    # Create client once per region
    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=location
    )

    try:
        # Count Garden Models once per region (not per cycle)
        garden_model_count = 0
        try:
            print(f"  Counting models...")
            aiplatform.init(project=PROJECT_ID, location=location)
            models = aiplatform.Model.list()
            garden_model_count = len(models)
            print(f"    ✓ Models: {garden_model_count}")
        except Exception as e:
            garden_model_count = -1  # Use -1 to indicate error (keeps type as integer)
            print(f"    ✗ Model count failed: {str(e)[:100]}")

        # Run all prompt cycles for this region
        for cycle_num, test_prompt in enumerate(TEST_PROMPTS, start=1):
            print(f"\n  [Cycle {cycle_num}/{NUM_CYCLES}] Testing with prompt: '{test_prompt[:50]}...'")

            result = {
                "#Cycle": cycle_num,
                "region": location,
                "Pro": "Not Available",
                "Flash": "Not Available",
                "Garden Models": garden_model_count
            }

            # Test Gemini Pro response time - try multiple model names
            pro_success = False
            pro_tried_models = []
            for model_name in MODELS["Pro"]:
                try:
                    pro_tried_models.append(model_name)
                    start_time = time.time()
                    response = client.models.generate_content(
                        model=model_name,
                        contents=test_prompt
                    )
                    end_time = time.time()

                    # Validate response has content
                    if not response or not hasattr(response, 'text'):
                        continue

                    # Verify response text is not empty (at least try to access it)
                    _ = response.text  # This will raise if response is invalid

                    pro_time = round((end_time - start_time) * 1000, 2)  # Convert to ms
                    result["Pro"] = f"{pro_time}ms"
                    print(f"    ✓ Pro ({model_name}): {pro_time}ms")
                    pro_success = True
                    break

                except Exception as e:
                    continue

            if not pro_success:
                result["Pro"] = "Not Available"
                print(f"    ✗ Pro: No models available (tried: {', '.join(pro_tried_models)})")

            # Test Gemini Flash response time - try multiple model names
            flash_success = False
            flash_tried_models = []
            for model_name in MODELS["Flash"]:
                try:
                    flash_tried_models.append(model_name)
                    start_time = time.time()
                    response = client.models.generate_content(
                        model=model_name,
                        contents=test_prompt
                    )
                    end_time = time.time()

                    # Validate response has content
                    if not response or not hasattr(response, 'text'):
                        continue

                    # Verify response text is not empty (at least try to access it)
                    _ = response.text  # This will raise if response is invalid

                    flash_time = round((end_time - start_time) * 1000, 2)  # Convert to ms
                    result["Flash"] = f"{flash_time}ms"
                    print(f"    ✓ Flash ({model_name}): {flash_time}ms")
                    flash_success = True
                    break

                except Exception as e:
                    continue

            if not flash_success:
                result["Flash"] = "Not Available"
                print(f"    ✗ Flash: No models available (tried: {', '.join(flash_tried_models)})")

            results.append(result)

        print(f"[{location}] Completed all {NUM_CYCLES} cycles")
    finally:
        # Clean up client resources
        if hasattr(client, 'close') and callable(getattr(client, 'close')):
            try:
                client.close()
            except:
                pass  # Ignore cleanup errors

# Generate CSV filename with timestamp
timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M")
csv_filename = f"./results/results-{timestamp}.csv"

# Ensure results directory exists
os.makedirs("./results", exist_ok=True)

# Write results to CSV
print("\n" + "=" * 60)
print(f"Writing results to {csv_filename}...")

with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['#Cycle', 'region', 'Pro', 'Flash', 'Garden Models']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    for result in results:
        writer.writerow(result)

print(f"✓ Results saved to {csv_filename}")
print(f"✓ Total records: {len(results)} ({len(EUROPEAN_LOCATIONS)} regions × {NUM_CYCLES} cycles)")
print("=" * 60)

# Display summary table (showing first cycle for each region)
print("\nSummary (Cycle 1 results):")
print("-" * 80)
print(f"{'Region':<20} {'Cycle':<8} {'Pro':<15} {'Flash':<15} {'Models':<10}")
print("-" * 80)
for result in results:
    if result['#Cycle'] == 1:
        print(
            f"{result['region']:<20} {result['#Cycle']:<8} {result['Pro']:<15} {result['Flash']:<15} {result['Garden Models']:<10}")
print("-" * 80)
print(f"\n✓ Benchmark complete! {len(results)} total measurements recorded.")
print(f"  ({len(EUROPEAN_LOCATIONS)} regions × {NUM_CYCLES} cycles)")
