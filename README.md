# Vertex AI Performance Benchmarking

This project provides tools for testing and benchmarking Google Cloud Vertex AI Gemini models across different regions.
It helps developers and data scientists measure response times, model availability, and generate professional
performance reports.

## Description

The project offers automated benchmarking tools for Vertex AI Gemini models:

- **Regional Performance Testing:** Measure response times for Gemini 2.5 Pro and Flash across European regions
- **Multi-Cycle Testing:** Run multiple different prompts per region for comprehensive, averaged results
- **Model Availability Tracking:** Identify which regions support specific Gemini models
- **Automated PDF Reports:** Generate elegant, professional PDF reports with color-coded performance metrics
- **Easy-to-Use Scripts:** Simple command-line tools to run benchmarks and generate reports

The framework uses the latest Google GenAI SDK and provides real-world performance metrics to help you choose the
optimal European region for your Gemini deployments. US regions are excluded due to significantly slower performance.

## Getting Started

### Prerequisites

- Python 3.13 or higher
- Google Cloud SDK with authentication configured
- A GCP project with Vertex AI API enabled

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/vertex-ai-tests.git
   cd vertex-ai-tests
   ```

2. **Configure your GCP project:**

   Edit the `PROJECT_ID` in `benchmark_european_regions.py`:
   ```python
   PROJECT_ID = "your-project-id"
   ```

3. **Authenticate with Google Cloud:**
   ```bash
   gcloud auth application-default login
   ```

**Note:** Dependencies are automatically installed when you run `run-metrics.cmd`. For manual installation, use:

```bash
pip install -r requirements.txt
```

## Usage

### Quick Start - Run Complete Benchmark

**Windows:**

```cmd
run-metrics.cmd
```

This automated script will:

1. **Auto-install dependencies** (if not already installed)
2. Run benchmarks across all European regions
3. Generate a CSV file with raw results
4. Create an elegant PDF report
5. Automatically open the PDF in your default browser

### Manual Usage

#### 1. Run Regional Benchmarks

Test all European regions:

```bash
python benchmark_european_regions.py
```

Results are saved to `./results/results-DD-MM-YYYY_HH-MM.csv`

#### 2. Generate PDF Reports

Convert the latest CSV to an elegant PDF report:

```bash
python csv_to_pdf_converter.py
```

The PDF includes:

- Executive summary with statistics
- Color-coded performance table
- Region codes and city names
- Key insights and recommendations

## Project Structure

```
vertex-ai-tests/
├── benchmark_european_regions.py  # Main benchmarking script
├── csv_to_pdf_converter.py       # PDF report generator
├── test_pdf_generation.py         # Test script for PDF generation
├── run-metrics.cmd                # Windows automation script
├── requirements.txt               # Python dependencies
├── results/                       # Generated CSV and PDF reports
│   ├── results-*.csv
│   └── benchmark-report-*.pdf
├── test_results/                  # Test output directory (gitignored)
│   ├── test_*.csv
│   └── test_report_*.pdf
├── README.md                      # This file
└── AGENTS.md                      # AI agent guidelines
```

## Features

### Regional Benchmarking

Automatically tests Gemini 2.5 Pro and Flash models across **10 European Regions:**

- Belgium (europe-west1)
- United Kingdom (europe-west2)
- Germany (europe-west3)
- Netherlands (europe-west4)
- Switzerland (europe-west6)
- Italy (europe-west8)
- France (europe-west9)
- Finland (europe-north1)
- Poland (europe-central2)
- Spain (europe-southwest1)

**Note:** US regions are not tested as they show significantly slower performance compared to European regions.

### PDF Report Features

- **Executive Summary:** Fastest, average, and slowest response times
- **Color-Coded Performance:** Green (fast), Yellow (medium), Red (slow)
- **Regional Details:** City names and region codes
- **Model Availability:** Track which regions support each model
- **Professional Design:** Clean, corporate-ready formatting

## Example Output

### CSV Format

The CSV includes all individual measurements with cycle numbers:

```csv
#Cycle,region,Pro,Flash,Garden Models
1,europe-west1,2757.05ms,957.13ms,0
2,europe-west1,2801.23ms,945.67ms,0
...
N,europe-west1,2723.45ms,963.89ms,0
1,europe-west4,3785.89ms,816.24ms,0
...
```

Each region is tested multiple times with different prompts (currently 10), resulting in N records per region where N =
number of test prompts.

### PDF Report

The PDF report shows **averaged results** across all test cycles:

- Title: "Vertex AI Gemini 2.5 Performance Benchmark - Averaged Results"
- Summary statistics table (based on averages)
- Detailed performance table with color coding (averaged values)
- Key insights and fastest regions
- Professional styling with timestamps
- Footer note: "Performance measured as averaged end-to-end response time across N test prompts"

## Configuration

### Customizing Regions

Edit `benchmark_european_regions.py` to add or remove regions:

```python
EUROPEAN_LOCATIONS = [
    "europe-west1",  # Belgium
    # Add more regions...
]
```

### Customizing Models

Update the models to test:

```python
MODELS = {
    "Pro": ["gemini-2.5-pro", "gemini-2.5-pro-exp"],
    "Flash": ["gemini-2.5-flash", "gemini-2.5-flash-exp"]
}
```

## Troubleshooting

### Authentication Issues
```bash
gcloud auth application-default login
```

### Project Not Found

Update `PROJECT_ID` in the script files with your actual GCP project ID.

### Model Not Available

Some regions may not support all Gemini models. The script will mark these as "Not Available" in the results.

### API Not Enabled

Enable the Vertex AI API in your GCP project:

```bash
gcloud services enable aiplatform.googleapis.com
```

## Testing

### Test PDF Generation

Run the test script to verify PDF generation with different cycle counts:

```bash
python test_pdf_generation.py
```

This will create test CSV files and generate PDFs with:

- 10 cycles (standard)
- 5 cycles (custom)
- 1 cycle (edge case)
- 20 cycles (extended)

Test results are saved to `./test_results/` directory.

## Contributing

See [AGENTS.md](AGENTS.md) for AI agent guidelines and contribution standards.
