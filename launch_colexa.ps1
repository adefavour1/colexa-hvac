# ============================================================
# COLEXA BIOSENSOR - HVAC Monitoring Platform
# One-click launcher (PowerShell)
# ============================================================

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

Write-Host "Checking for Python..." -ForegroundColor Cyan
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "Python was not found on PATH. Please install Python 3.11+ from python.org" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

if (-not (Test-Path ".\venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Cyan
    python -m venv venv
}

Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& .\venv\Scripts\Activate.ps1

Write-Host "Installing/verifying dependencies..." -ForegroundColor Cyan
pip install --quiet --disable-pip-version-check -r requirements.txt

Write-Host "Launching COLEXA HVAC Monitoring Platform..." -ForegroundColor Green
streamlit run app.py

Read-Host "Press Enter to exit"
