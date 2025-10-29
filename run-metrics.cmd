@echo off
REM ============================================================
REM Vertex AI Gemini Performance Benchmarking Tool
REM ============================================================
REM This script runs the complete benchmarking workflow:
REM 1. Benchmarks Gemini models across European regions
REM 2. Generates a CSV file with raw results
REM 3. Creates an elegant PDF report
REM 4. Opens the PDF in your default browser
REM Note: US regions excluded due to slower performance
REM ============================================================

echo.
echo ============================================================
echo Vertex AI Gemini Performance Benchmarking
echo ============================================================
echo.

REM Step 0: Install required dependencies
echo [0/4] Installing required Python packages...
echo This only takes a moment if already installed.
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
echo [1/4] Running European regional benchmarks...
echo This may take 5-10 minutes to test all regions.
echo.
python benchmark_european_regions.py
if errorlevel 1 (
    echo.
    echo ERROR: Benchmark failed!
    echo Please check your GCP authentication and project configuration.
    pause
    exit /b 1
)

echo.
echo [2/4] Generating PDF report...
echo.
python csv_to_pdf_converter.py
if errorlevel 1 (
    echo.
    echo ERROR: PDF generation failed!
    pause
    exit /b 1
)

REM Step 3: Find and open the latest PDF
echo.
echo [3/4] Finding latest PDF report...
echo.

REM Find the latest PDF file in results directory
for /f "delims=" %%i in ('dir /b /o-d results\benchmark-report-*.pdf 2^>nul') do (
    set LATEST_PDF=%%i
    goto :found
)

:found
if not defined LATEST_PDF (
    echo ERROR: No PDF report found in results directory!
    pause
    exit /b 1
)

echo [4/4] Opening PDF report...

echo Opening: results\%LATEST_PDF%
echo.

REM Open PDF with default application
start "" "results\%LATEST_PDF%"

echo.
echo ============================================================
echo Benchmark Complete!
echo ============================================================
echo.
echo Results saved to:
echo - CSV: results\results-*.csv
echo - PDF: results\%LATEST_PDF%
echo.
echo The PDF report has been opened in your default PDF viewer.
echo ============================================================
echo.

REM Optional: Keep window open to view messages
timeout /t 5 /nobreak >nul
