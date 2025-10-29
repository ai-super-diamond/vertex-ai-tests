# AGENTS.md

This document provides instructions for AI agents working on this Vertex AI Performance Benchmarking project. By
following these guidelines, you can ensure that your contributions are consistent with the project's standards and best
practices.

## Project Overview

This is a benchmarking tool for Google Cloud Vertex AI Gemini models. The project measures performance across different
regions and generates professional PDF reports. It is NOT a traditional testing framework.

## Key Components

### 1. Core Scripts

- **benchmark_european_regions.py**: Main benchmarking script that tests Gemini models across European regions only (US
  regions excluded due to slower performance)
- **csv_to_pdf_converter.py**: Converts CSV benchmark results to elegant PDF reports

### 2. Automation & Configuration

- **run-metrics.cmd**: Windows batch script that automates the complete workflow (dependency installation, benchmarking,
  PDF generation, and viewing)
- **requirements.txt**: Python package dependencies

### 3. Output Directory

- **results/**: Contains CSV data files and PDF reports with timestamps

## Coding Conventions

- **Style Guide:** Python code should follow [PEP 8 style guide](https://www.python.org/dev/peps/pep-0008/)
- **Naming Conventions:**
    - Use descriptive variable names (e.g., `EUROPEAN_LOCATIONS`, `flash_time`)
    - Constants in UPPERCASE with underscores
    - Functions in lowercase with underscores
- **Comments:** Add clear comments explaining regional configurations and performance calculations
- **Error Handling:** Always include try-except blocks for API calls with informative error messages

## Dependencies

### Current Dependencies

All dependencies are defined in `requirements.txt`:

- **google-genai**: Google's GenAI SDK for Gemini models (v0.1.0+)
- **google-cloud-aiplatform**: Vertex AI SDK (v1.38.0+)
- **reportlab**: PDF generation library (v4.0.0+)

### Adding Dependencies

When adding new dependencies:

1. Add to `requirements.txt` with minimum version
2. Test with the latest stable version
3. Update README.md if installation process changes
4. Ensure compatibility with Python 3.13+
5. Run `pip install -r requirements.txt` to verify

## Configuration Standards

### Project Configuration

All scripts should include a clearly marked configuration section:

```python
# --- Configuration ---
PROJECT_ID = "your-project-id"
LOCATION = "us-central1"
# ---------------------
```

### Region Management

- **EUROPEAN_LOCATIONS**: List of 10 European Vertex AI regions with city comments
- **REGION_TO_CITY**: Mapping dictionary for human-readable city names (CSV to PDF converter)

**Note:** US regions are intentionally excluded from testing due to significantly slower performance.

When adding new European regions:

1. Add to EUROPEAN_LOCATIONS list with format: `"region-code"  # City`
2. Update REGION_TO_CITY mapping in csv_to_pdf_converter.py with format: `"Country (City)"`
3. Test availability before committing

## Output Standards

### CSV Files

Format: `results-DD-MM-YYYY_HH-MM.csv`

Required columns:

- `region`: Technical region code (e.g., "europe-west1")
- `Pro`: Gemini 2.5 Pro response time or "Not Available"
- `Flash`: Gemini 2.5 Flash response time or "Not Available"
- `Garden Models`: Count of custom models (integer)

### PDF Reports

Format: `benchmark-report-DD-MM-YYYY_HH-MM.pdf`

Required sections:

1. Title and timestamp
2. Executive Summary table
3. Detailed Regional Performance table with color coding
4. Key Insights section
5. Footer with generation info

### Filename Conventions

Always use this timestamp format: `DD-MM-YYYY_HH-MM`

```python
timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M")
```

## Performance Measurement

### Timing Method

Use `time.time()` for end-to-end measurements:

```python
start_time = time.time()
response = client.models.generate_content(...)
end_time = time.time()
response_time = round((end_time - start_time) * 1000, 2)  # Convert to ms
```

### Test Prompt

Always use a consistent, minimal prompt:

```python
TEST_PROMPT = "Hello, respond with just 'OK'"
```

This ensures consistent, comparable results across regions.

## Testing Workflow

### Automated Workflow (Recommended)

**Windows:**

```cmd
run-metrics.cmd
```

This automated script:

1. Installs dependencies from `requirements.txt`
2. Runs the full benchmark across all European regions
3. Generates the PDF report
4. Opens the PDF automatically

### Manual Testing

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Full Benchmark:**
   ```bash
   python benchmark_european_regions.py
   ```

3. **Generate PDF Report:**
   ```bash
   python csv_to_pdf_converter.py
   ```

## Error Handling Best Practices

### Model Availability

Always try multiple model name variations:

```python
for model_name in MODELS["Pro"]:
    try:
        response = client.models.generate_content(...)
        # Success - break
        break
    except Exception:
        # Try next variant
        continue
```

### Regional Errors

- Catch and log region-specific failures
- Mark unavailable models as "Not Available"
- Continue processing other regions
- Don't fail entire benchmark due to single region

## PDF Styling Guidelines

### Colors

- **Headers**: `#1a73e8` (Google Blue)
- **Performance Indicators**:
    - Green: `Color(0.8, 1, 0.8)` - Top 33%
    - Yellow: `Color(1, 1, 0.8)` - Middle 33%
    - Red: `Color(1, 0.9, 0.9)` - Bottom 33%

### Typography

- **Title**: Helvetica-Bold, 24pt
- **Headers**: Helvetica-Bold, 14pt
- **Table Headers**: Helvetica-Bold, 10-11pt
- **Table Data**: Helvetica, 8-9pt
- **Region Codes**: Courier, 7pt (monospace)

## Verifying Your Work

Before submitting changes:

1. **Test automated workflow (Windows):**
   ```cmd
   run-metrics.cmd
   ```
   Verify it:
    - Installs dependencies successfully
    - Completes benchmark without errors
    - Generates PDF correctly
    - Opens PDF in browser

2. **Check output files:**
    - CSV has all expected columns (region, Pro, Flash, Garden Models)
    - PDF has proper formatting and colors
    - Timestamps are consistent (DD-MM-YYYY_HH-MM format)
    - Region codes match city names

3. **Verify dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   Ensure all packages install without conflicts

## Common Tasks for AI Agents

### Adding a New Region

1. Identify the region code from [GCP documentation](https://cloud.google.com/vertex-ai/docs/general/locations)
2. Add to appropriate location list (EUROPEAN_LOCATIONS or US_LOCATIONS)
3. Add mapping to REGION_TO_CITY dictionary
4. Test the region before committing

### Adding a New Model

1. Add model name variants to MODELS dictionary
2. Test availability across regions
3. Update README.md with model information
4. Consider updating PDF column headers if needed

### Improving Performance Metrics

1. Maintain backward compatibility with existing CSV format
2. Update both CSV output and PDF generation
3. Document any new metrics in README.md
4. Update Executive Summary calculations

## Git Workflow

### Commit Messages

Follow conventional commits format:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation updates
- `refactor:` Code refactoring
- `style:` Formatting changes

Examples:

- `feat: Add Asia-Pacific regions to benchmark`
- `fix: Correct PDF color coding for edge cases`
- `docs: Update README with new regions`

### Branch Naming

- `feature/region-asia-pacific`
- `fix/pdf-color-bug`
- `docs/update-readme`

Make sure all checks pass before requesting a review.
