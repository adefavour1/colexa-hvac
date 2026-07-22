@echo off
REM ============================================================
REM COLEXA BIOSENSOR - HVAC Monitoring Platform
REM One-click launcher (Windows Batch)
REM ============================================================

setlocal

cd /d "%~dp0"

echo Checking for Python...
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Python was not found on PATH. Please install Python 3.11+ from python.org
    pause
    exit /b 1
)

if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo Installing/verifying dependencies...
pip install --quiet --disable-pip-version-check -r requirements.txt

echo Launching COLEXA HVAC Monitoring Platform...
streamlit run app.py

pause
endlocal
