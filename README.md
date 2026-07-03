# Vertex AI Performance Benchmarking

This project provides tools for testing and benchmarking Google Cloud Vertex AI Gemini models across different regions.
It helps developers and data scientists measure response times, model availability, and generate professional
performance reports.

## Description

The project offers automated benchmarking tools for Vertex AI Gemini models:

- **Regional Performance Testing:** Measure response times for Gemini Pro and Flash.
- **Multi-Cycle Testing:** Run multiple different prompts per region for comprehensive, averaged results.
- **Model Availability Tracking:** Identify which regions support specific Gemini models.
- **Automated PDF Reports:** Generate elegant, professional PDF reports with color-coded performance metrics.
- **Interactive Dashboard:** Visualize and explore results with a Streamlit web app.

The framework uses the latest Google GenAI SDK and provides real-world performance metrics to help you choose the
optimal region for your Gemini deployments.

## Getting Started

### Prerequisites

- Python 3.13 or higher
- Google Cloud SDK with authentication configured
- A GCP project with Vertex AI API enabled

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/vertex-ai-tests.git
    cd vertex-ai-tests
    ```

2.  **Configure your GCP project:**

    Edit the `PROJECT_ID` in `src/vertex_benchmark/config.py`:
    ```python
    PROJECT_ID = "your-project-id"
    ```

3.  **Install dependencies in editable mode:**
    ```bash
    pip install -e .
    ```
    *(This is the recommended method as it correctly handles the `src` layout)*

4.  **Authenticate with Google Cloud:**
    ```bash
    gcloud auth application-default login
    ```

## Usage

### Quick Start - Automated Workflow

**Windows:**

```cmd
run-metrics-european.cmd
```

This automated script will:

1. **Auto-install dependencies**
2. Run benchmarks across all specified regions
3. Store results in a SQLite database
4. Create an elegant PDF report
5. Automatically open the PDF in your default browser

### Manual Usage

#### 1. Run Regional Benchmarks

```bash
python -m vertex_benchmark.benchmark_engine
```*Results are saved to `benchmark_results.db`*

#### 2. Generate PDF Reports

```bash
python -m vertex_benchmark.generate_report
```
*The PDF will be saved in the `results/` directory.*

#### 3. Run the Interactive Dashboard

```bash
streamlit run src/vertex_benchmark/dashboard.py
```

## Project Structure

```
vertex-ai-tests/
├── src/
│   └── vertex_benchmark/
│       ├── __init__.py
│       ├── benchmark_engine.py   # Main benchmarking script
│       ├── generate_report.py      # PDF report generator
│       ├── dashboard.py            # Interactive web dashboard
│       ├── database_utils.py       # Database utility functions
│       └── ...                     # Other modules
├── tests/
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   └── e2e/                      # End-to-end tests
├── .gitignore
├── pyproject.toml                # Project configuration and dependencies
├── run-metrics-european.cmd      # Windows automation script
├── benchmark_results.db          # SQLite database with benchmark results
├── results/                      # Generated PDF reports
└── README.md                     # This file
```

## Testing

The project uses a structured testing approach with `pytest`.

### Running Tests

1.  **Install development dependencies:**
    ```bash
    pip install -e ".[dev]"
    ```

2.  **Run all tests:**
    ```bash
    pytest
    ```

3.  **Run specific test types:**
    ```bash
    pytest tests/unit          # Run unit tests only
    pytest tests/integration   # Run integration tests only
    pytest tests/e2e           # Run end-to-end tests only
    ```

## Contributing

See [AGENTS.md](AGENTS.md) for AI agent guidelines and contribution standards.
