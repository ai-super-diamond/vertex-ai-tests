# AGENTS.md

This document provides instructions for AI agents working on this Vertex AI Performance Benchmarking project. By
following these guidelines, you can ensure that your contributions are consistent with the project's standards and best
practices.

## Project Overview

This is a benchmarking tool for Google Cloud Vertex AI Gemini models. The project measures performance across different
regions and generates professional PDF reports. It is NOT a traditional testing framework.

### Repository Layout (high level)

```text
src/vertex_benchmark/           # Core application modules (source of truth)
  benchmark_engine.py           # Runs benchmarks and writes to SQLite
  generate_report.py            # Builds averaged PDF report
  dashboard.py                  # Streamlit dashboard (optional)
  database_utils.py             # SQLite helpers (batches + results)
  config.py                     # Configuration (project, regions, models, prompts, version)
  report_utils.py               # Stats/percentile helpers

tests/                          # Pytest suites (unit/integration/e2e wrappers)
.github/workflows/ci.yml        # CI: run pytest, upload PDFs as artifacts
.pre-commit-config.yaml         # black, isort, flake8 hooks
pyproject.toml                  # Tooling configuration (black/isort/flake8)
requirements.txt                # Runtime dependencies
requirements-dev.txt            # Dev/test/tooling deps (pytest, pre-commit, etc.)
```

## Key Components

## Architectural Source of Truth

**IMPORTANT:** This project follows a standard `src` layout. All core Python modules are located within the `src/vertex_benchmark` package.

The `ARCHITECTURE.md` file is the single source of truth for the project's structure, components, and workflow. Before making any changes, you **must** review it to understand how the components interact. All file paths and module locations in this `AGENTS.md` document are derived from the architecture defined therein.

If you make any changes to the project's structure (e.g., adding, moving, or renaming files), you must update `ARCHITECTURE.md` first.

All Python source code is located in the `src/vertex_benchmark` package. For a visual overview of the project structure, please refer to `ARCHITECTURE.md`.

### 1. Core Modules (`src/vertex_benchmark/`)

- **benchmark_engine.py**: Main benchmarking logic.
- **generate_report.py**: Generates PDF reports from database results.
- **dashboard.py**: Interactive Streamlit web dashboard.

### 2. Utility Modules (`src/vertex_benchmark/`)

- **database_utils.py**: Handles all SQLite database interactions.
- **config.py**: Configuration settings (project ID, regions, models, etc.).
- **report_utils.py**: Helper functions for PDF report generation.

### 3. Automation & Configuration

- **run-metrics-european.cmd**: Windows batch script that automates the complete workflow. Provide analogous PowerShell/Bash scripts if cross‑platform runs are desired.
- **run-metrics-worldwide.cmd**: Windows batch script to run the worldwide set of regions.
- **pyproject.toml**: Modern Python package configuration and dependencies.
- **requirements.txt**: List of dependencies.
- **requirements-dev.txt**: Development and test dependencies (pytest, pre‑commit, black, flake8, isort).

### 4. Output

- **benchmark_results.db**: SQLite database storing all benchmark results.
- **results/**: Contains generated PDF reports with timestamps.

Metadata per run is stored in a `batches` table (see Architecture). Reports include conditional footer metadata (batch id, version, started/ended, config summary) when available.

### Utilities (optional)

- `check_all_batches.py`: List and inspect batches and counts.
- `check_db_regions.py`: Verify region coverage in DB.
- `generate_pdf_for_batch.py`: Regenerate a report for a specific batch id.

## Coding Conventions

- **Style Guide:** Python code should follow [PEP 8 style guide](https://www.python.org/dev/peps/pep-0008/). Pre‑commit enforces black, isort, and flake8.
- **Naming Conventions:**
  - Use descriptive variable names (e.g., `EUROPEAN_LOCATIONS`, `flash_time`).
  - Constants in UPPERCASE with underscores.
  - Functions in lowercase with underscores.
- **Comments:** Add clear comments explaining regional configurations and performance calculations.
- **Error Handling:** Always include try-except blocks for API calls with informative error messages.

## Dependencies

Runtime dependencies are in `requirements.txt`. Tooling/dev/test dependencies are in `requirements-dev.txt`. Formatting/lint settings live in `pyproject.toml`.

To install for development:

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
pre-commit install
```

### Authentication

The benchmark uses Application Default Credentials (ADC):

```bash
gcloud auth application-default login
```
Alternatively, set `GOOGLE_APPLICATION_CREDENTIALS` to a service account JSON.


## Testing Workflow

### Automated Workflow (Recommended)

**Windows:**

```cmd
run-metrics-european.cmd
```

This automated script:

1. Installs dependencies from `requirements.txt`.
2. Runs the full benchmark across all European regions.
3. Generates the PDF report.
4. Opens the PDF automatically.

### Manual Testing

1. **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    pre-commit install
    ```

2. **Run Full Benchmark:**
    ```bash
    python -m vertex_benchmark.benchmark_engine
    ```

3. **Generate PDF Report:**
    ```bash
    python -m vertex_benchmark.generate_report
    ```

4. **Test the dashboard:**
    ```bash
    streamlit run src/vertex_benchmark/dashboard.py
    ```

5. **Run Tests:**

    ```bash
    # Run all tests
    pytest -q

    # Run specific test types
    pytest tests/unit          # Run unit tests only
    pytest tests/integration   # Run integration tests only
    pytest tests/e2e           # Run end-to-end tests only
    ```

The project uses a structured testing approach with three distinct test categories organized in the `tests/` directory:

 - **`tests/unit/`**: Contains isolated unit tests that test individual functions and modules in isolation.
 - **`tests/integration/`**: Contains integration tests that verify the interaction between different components and modules.
 - **`tests/e2e/`**: Contains end-to-end tests that simulate real user scenarios, testing the complete application workflow.
 - **`tests/conftest.py`**: A configuration file that provides shared fixtures and setup code used across all test categories.

## Verifying Your Work

Before submitting changes, ensure all checks pass locally and in CI:
- Pre‑commit passes locally (black/isort/flake8 on staged files).
- `pytest -q` passes locally.
- CI (GitHub Actions) runs pytest and uploads PDF artifacts from `results/` and `test_results/`.

## Configuration Guidelines

Key configuration entries in `src/vertex_benchmark/config.py`:
- `APP_VERSION`: string version for the app; stored in `batches` and shown in report footer.
- `PROJECT_ID`: GCP project id.
- `EUROPEAN_LOCATIONS`: list of region codes.
- `MODELS`: dict with Pro/Flash variants.
- `TEST_PROMPTS`: list of prompts; number of cycles derived from its length.
- `MIN_DELAY_SECONDS` / `MAX_DELAY_SECONDS`: pacing between calls.

## Error Handling & Performance Practices

- Use retries with exponential backoff and reasonable timeouts.
- Treat region/model unavailability as partial success; continue other tests.
- Database: use a single connection per run, `journal_mode=WAL`, `synchronous=NORMAL`, and composite index on `(batch_id, region)`.
- Record batch metadata (`batches` table) with `begin_batch` and `end_batch`.
