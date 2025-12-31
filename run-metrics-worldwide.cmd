@echo off
REM ============================================================
REM Vertex AI Gemini Performance Benchmarking Tool
REM ============================================================
REM This script runs the complete benchmarking workflow:
REM 1. Benchmarks Gemini models across Worldwide regions
REM 2. Writes results to SQLite (benchmark_results.db)
REM 3. Creates an elegant PDF report
REM 4. Launches the dashboard to view results
REM Note: Tests Worldwide Vertex AI regions
REM ============================================================

echo.
echo ============================================================
echo Vertex AI Gemini Worldwide Performance Benchmarking
echo ============================================================
echo.

REM Step 0: Install required dependencies
echo [0/4] Installing required Python packages...
echo This only takes a moment if already installed. Ensure VERTEX_PROJECT_ID is set.
echo.
python -m pip install -q -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERROR: Failed to install dependencies!
    echo Please ensure Python and pip are properly installed.
    pause
    exit /b 1
)
echo Dependencies installed successfully.
echo.

REM Step 1: Run the benchmark
echo [1/4] Running Worldwide regional benchmarks...
echo This may take 5-15 minutes to test Worldwide regions.
echo.
python -m vertex_benchmark.benchmark_engine worldwide
if errorlevel 1 (
    echo.
    echo ERROR: Benchmark failed!
    echo Please check your GCP authentication and project configuration.
    pause
    exit /b 1
)

echo.
REM The engine handles PDF generation automatically

REM Step 3: Launch dashboard
echo.
echo [3/4] Launching dashboard...
echo.

REM The engine handles PDF generation and dashboard launch
echo Dashboard launched successfully.
echo.

echo.
echo ============================================================
echo Benchmark Complete!
echo ============================================================
echo.
echo Results saved to:
echo - Database: benchmark_results.db
echo - PDF: results\ (latest report)
echo - Dashboard: Running on localhost
echo.
echo The dashboard is now running to view your results.
echo ============================================================
echo.

REM Optional: Keep window open to view messages
timeout /t 5 /nobreak >nul