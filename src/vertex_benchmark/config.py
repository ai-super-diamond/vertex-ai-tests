import os

# --- Configuration ---
APP_VERSION = "1.0.0"
# Prefer env override to avoid hard-coding project IDs
PROJECT_ID = os.getenv("VERTEX_PROJECT_ID", "your-project-id")

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

# Worldwide Vertex AI locations (includes European regions)
WORLDWIDE_LOCATIONS = [
    "asia-east1",      # Taiwan
    "asia-east2",      # Hong Kong
    "asia-northeast1", # Tokyo
    "asia-northeast2", # Osaka
    "asia-northeast3", # Seoul
    "asia-south1",     # Mumbai
    "asia-south2",     # Delhi
    "asia-southeast1", # Singapore
    "asia-southeast2", # Jakarta
    "australia-southeast1", # Sydney
    "australia-southeast2", # Melbourne
    "europe-central2", # Warsaw
    "europe-north1",   # Finland
    "europe-southwest1", # Madrid
    "europe-west1",    # Belgium
    "europe-west2",    # London
    "europe-west3",    # Frankfurt
    "europe-west4",    # Netherlands
    "europe-west6",    # Zurich
    "europe-west8",    # Milan
    "europe-west9",    # Paris
    "europe-west10",   # Berlin
    "europe-west12",   # Turin
    "me-central1",     # Doha
    "me-central2",     # Dammam
    "me-west1",        # Tel Aviv
    "northamerica-northeast1", # Montreal
    "northamerica-northeast2", # Toronto
    "southamerica-east1", # Sao Paulo
    "southamerica-west1", # Santiago
    "us-central1",     # Iowa
    "us-east1",        # South Carolina
    "us-east4",        # Northern Virginia
    "us-east5",        # Columbus
    "us-south1",       # Dallas
    "us-west1",        # Oregon
    "us-west2",        # Los Angeles
    "us-west3",        # Salt Lake City
    "us-west4",        # Las Vegas
]

# Models to test - Gemini Pro and Flash
MODELS = {
    "Pro": ["gemini-3.1-pro-preview"],
    "Flash": ["gemini-3.5-flash"]
}

# Test prompts - 2 prompts for faster benchmarking
TEST_PROMPTS = [
    "Hello, respond with just 'OK'",
    "What is 2+2? Answer briefly."
]

# Region to City Name Mapping
REGION_TO_CITY = {
    # European regions (original)
    "europe-west1": "Belgium (Brussels)",
    "europe-west2": "United Kingdom (London)",
    "europe-west3": "Germany (Frankfurt)",
    "europe-west4": "Netherlands (Amsterdam)",
    "europe-west6": "Switzerland (Zurich)",
    "europe-west8": "Italy (Milan)",
    "europe-west9": "France (Paris)",
    "europe-north1": "Finland (Helsinki)",
    "europe-central2": "Poland (Warsaw)",
    "europe-southwest1": "Spain (Madrid)",
    # Worldwide regions (additional)
    "asia-east1": "Taiwan (Changhua)",
    "asia-east2": "Hong Kong",
    "asia-northeast1": "Japan (Tokyo)",
    "asia-northeast2": "Japan (Osaka)",
    "asia-northeast3": "South Korea (Seoul)",
    "asia-south1": "India (Mumbai)",
    "asia-south2": "India (Delhi)",
    "asia-southeast1": "Singapore",
    "asia-southeast2": "Indonesia (Jakarta)",
    "australia-southeast1": "Australia (Sydney)",
    "australia-southeast2": "Australia (Melbourne)",
    "europe-west10": "Germany (Berlin)",
    "europe-west12": "Italy (Turin)",
    "me-central1": "Qatar (Doha)",
    "me-central2": "Saudi Arabia (Dammam)",
    "me-west1": "Israel (Tel Aviv)",
    "northamerica-northeast1": "Canada (Montreal)",
    "northamerica-northeast2": "Canada (Toronto)",
    "southamerica-east1": "Brazil (Sao Paulo)",
    "southamerica-west1": "Chile (Santiago)",
    "us-central1": "United States (Iowa)",
    "us-east1": "United States (South Carolina)",
    "us-east4": "United States (Northern Virginia)",
    "us-east5": "United States (Columbus)",
    "us-south1": "United States (Dallas)",
    "us-west1": "United States (Oregon)",
    "us-west2": "United States (Los Angeles)",
    "us-west3": "United States (Salt Lake City)",
    "us-west4": "United States (Las Vegas)"
}

# Delay between requests to simulate human-like behavior
MIN_DELAY_SECONDS = 1
MAX_DELAY_SECONDS = 5