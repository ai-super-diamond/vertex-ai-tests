import csv
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

# Simple test prompt
TEST_PROMPT = "Hello, respond with just 'OK'"

print("=" * 60)
print("Vertex AI European Regions Benchmark")
print("=" * 60)
print(f"Project: {PROJECT_ID}")
print(f"Testing {len(EUROPEAN_LOCATIONS)} European locations")
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)
print()

results = []

for location in EUROPEAN_LOCATIONS:
    print(f"\n[{location}] Starting tests...")

    result = {
        "region": location,
        "Pro": "N/A",
        "Flash": "N/A",
        "Garden Models": 0
    }

    # Test Gemini Pro response time - try multiple model names
    pro_success = False
    for model_name in MODELS["Pro"]:
        try:
            print(f"  Testing Gemini Pro ({model_name})...")
            client = genai.Client(
                vertexai=True,
                project=PROJECT_ID,
                location=location
            )

            start_time = time.time()
            response = client.models.generate_content(
                model=model_name,
                contents=TEST_PROMPT
            )
            end_time = time.time()

            pro_time = round((end_time - start_time) * 1000, 2)  # Convert to ms
            result["Pro"] = f"{pro_time}ms"
            print(f"    ✓ Pro ({model_name}): {pro_time}ms")
            pro_success = True
            break

        except Exception as e:
            print(f"    ✗ {model_name} not available")
            continue

    if not pro_success:
        result["Pro"] = "Not Available"
        print(f"    ✗ Pro: No models available")

    # Test Gemini Flash response time - try multiple model names
    flash_success = False
    for model_name in MODELS["Flash"]:
        try:
            print(f"  Testing Gemini Flash ({model_name})...")
            client = genai.Client(
                vertexai=True,
                project=PROJECT_ID,
                location=location
            )

            start_time = time.time()
            response = client.models.generate_content(
                model=model_name,
                contents=TEST_PROMPT
            )
            end_time = time.time()

            flash_time = round((end_time - start_time) * 1000, 2)  # Convert to ms
            result["Flash"] = f"{flash_time}ms"
            print(f"    ✓ Flash ({model_name}): {flash_time}ms")
            flash_success = True
            break

        except Exception as e:
            print(f"    ✗ {model_name} not available")
            continue

    if not flash_success:
        result["Flash"] = "Not Available"
        print(f"    ✗ Flash: No models available")

    # Count Garden Models (registered models in the project)
    try:
        print(f"  Counting models...")
        aiplatform.init(project=PROJECT_ID, location=location)
        models = aiplatform.Model.list()
        model_count = len(models)
        result["Garden Models"] = model_count
        print(f"    ✓ Models: {model_count}")

    except Exception as e:
        result["Garden Models"] = "Error"
        print(f"    ✗ Model count failed: {str(e)[:100]}")

    results.append(result)
    print(f"[{location}] Completed")

# Generate CSV filename with timestamp
timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M")
csv_filename = f"./results/results-{timestamp}.csv"

# Write results to CSV
print("\n" + "=" * 60)
print(f"Writing results to {csv_filename}...")

with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['region', 'Pro', 'Flash', 'Garden Models']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    for result in results:
        writer.writerow(result)

print(f"✓ Results saved to {csv_filename}")
print("=" * 60)

# Display summary table
print("\nSummary:")
print("-" * 60)
print(f"{'Region':<20} {'Pro':<15} {'Flash':<15} {'Models':<10}")
print("-" * 60)
for result in results:
    print(f"{result['region']:<20} {result['Pro']:<15} {result['Flash']:<15} {result['Garden Models']:<10}")
print("-" * 60)
print("\n✓ Benchmark complete!")
