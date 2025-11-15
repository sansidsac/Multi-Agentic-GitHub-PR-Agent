# Setup Script for GitHub PR Review Agent
# Run this script to set up the environment

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "GitHub PR Review Agent - Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "[1/6] Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($pythonVersion -match "Python 3\.([0-9]+)") {
    $minorVersion = [int]$matches[1]
    if ($minorVersion -ge 11) {
        Write-Host "[OK] Python version OK: $pythonVersion" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Python 3.11+ required. Found: $pythonVersion" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[ERROR] Python not found or version check failed" -ForegroundColor Red
    exit 1
}

# Create virtual environment
Write-Host ""
Write-Host "[2/6] Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "[OK] Virtual environment already exists, skipping..." -ForegroundColor Gray
} else {
    python -m venv venv
    Write-Host "[OK] Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host ""
Write-Host "[3/6] Activating virtual environment..." -ForegroundColor Yellow
$activateScript = Join-Path $PSScriptRoot "venv\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
    Write-Host "[OK] Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "[WARNING] Could not find activation script, continuing..." -ForegroundColor Yellow
}

# Install dependencies
Write-Host ""
Write-Host "[4/6] Installing dependencies..." -ForegroundColor Yellow
$pipUpgrade = & pip install --upgrade pip -q 2>&1
$pipInstall = & pip install -r requirements.txt -q 2>&1
Write-Host "[OK] Dependencies installed" -ForegroundColor Green

# Generate webhook secret
Write-Host ""
Write-Host "[5/6] Generating webhook secret..." -ForegroundColor Yellow
$secret = & python scripts\generate_secret.py 2>&1
Write-Host $secret

# Update .env file if needed
if (Test-Path ".env") {
    $envContent = Get-Content ".env" -Raw
    if ($envContent -match "generate_secret_with_script") {
        Write-Host "[ACTION REQUIRED] Please update GITHUB_WEBHOOK_SECRET in .env file with the generated secret above" -ForegroundColor Yellow
    } else {
        Write-Host "[OK] .env file already configured" -ForegroundColor Green
    }
}

# Verify configuration
Write-Host ""
Write-Host "[6/6] Verifying configuration..." -ForegroundColor Yellow
if (Test-Path ".env") {
    $envContent = Get-Content ".env" -Raw
    $checks = @{
        "GITHUB_TOKEN" = $envContent -match "GITHUB_TOKEN=ghp_"
        "LYZR_API_KEY" = $envContent -match "LYZR_API_KEY=sk-"
        "LYZR_AGENT_ID" = $envContent -match "LYZR_AGENT_ID=\w+"
    }
    
    foreach ($check in $checks.GetEnumerator()) {
        if ($check.Value) {
            Write-Host "[OK] $($check.Key) configured" -ForegroundColor Green
        } else {
            Write-Host "[ERROR] $($check.Key) not configured" -ForegroundColor Red
        }
    }
} else {
    Write-Host "[ERROR] .env file not found" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Update GITHUB_WEBHOOK_SECRET in .env file (if needed)" -ForegroundColor White
Write-Host "2. Run server: python -m uvicorn app.main:app --reload" -ForegroundColor White
Write-Host "3. In another terminal, start ngrok: ngrok http 8000" -ForegroundColor White
Write-Host "4. Configure GitHub webhook with ngrok URL" -ForegroundColor White
Write-Host ""
Write-Host "Documentation: README.md" -ForegroundColor Gray
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor Gray
Write-Host ""
