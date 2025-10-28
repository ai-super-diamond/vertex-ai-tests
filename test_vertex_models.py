import traceback
import google.cloud.aiplatform as aiplatform
from google.cloud.aiplatform import v1 as aiplatform_v1
from google.api_core.client_options import ClientOptions

# --- Configuration ---
# Your project and location.
# aiplatform.init() will try to infer these from your gcloud config.
PROJECT_ID = "YOUR_PROJECT_ID"  # ---------------------> UPDATE THIS
LOCATION = "us-central1"        # ---------------------> UPDATE THIS
# ---------------------

print("--- Listing Available Publisher Models ---")

try:
    # Initialize the main SDK. This handles auth and project/location.
    aiplatform.init(project=PROJECT_ID, location=LOCATION)

    # The ModelGardenService client is regional.
    # We must explicitly set the endpoint for the client.
    client_options = ClientOptions(
        api_endpoint=f"{LOCATION}-aiplatform.googleapis.com"
    )

    # This is the correct client for the Model Garden Service
    client = aiplatform_v1.ModelGardenServiceClient(
        client_options=client_options
    )

    # Create the request. The parent path is "publishers/google"
    # to list Google's publisher models.
    request = aiplatform_v1.ListPublisherModelsRequest(
        parent=f"publishers/google"
    )

    print(f"Fetching models for publisher 'google' in {LOCATION}...\n")

    # Call the API
    # This returns a paginated result. We'll just list the first page.
    page_result = client.list_publisher_models(request=request)

    model_count = 0
    for model in page_result:
        model_count += 1
        print(f"Model Name: {model.name.split('/')[-1]}")
        print(f"Display Name: {model.display_name}")
        print(f"Resource Name: {model.name}\n")
    
    if model_count == 0:
        print("No publisher models found.")
    else:
        print(f"--- Found {model_count} models ---")


except Exception as e:
    print(f"\n--- An Error Occurred ---")
    print(f"Error: {e}")
    traceback.print_exc()