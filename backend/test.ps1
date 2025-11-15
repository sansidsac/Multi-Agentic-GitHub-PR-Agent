# Test script - runs the test suite

Write-Host "Running test suite..." -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "✗ Virtual environment not found. Run setup.ps1 first." -ForegroundColor Red
    exit 1
}

# Activate virtual environment
& ".\venv\Scripts\Activate.ps1"

# Run tests
Write-Host "Executing pytest..." -ForegroundColor Yellow
Write-Host ""

pytest tests/ -v --cov=app --cov-report=term-missing

Write-Host ""
Write-Host "Test run complete!" -ForegroundColor Green
