@echo off
title Bitget Trader Analysis

:: Located inside bitget_trader_analysis/

:: Ensure we are in the script's directory
cd /d "%~dp0"

:: Ensure .venv exists
if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
)

:: Activate
call .venv\Scripts\activate

:: Use python -m pip to be safe
echo Checking dependencies...
python -m pip install --upgrade pip -q
python -m pip install -q pandas rich jinja2 requests python-dotenv

:: Run the analysis
cd ..
set PYTHONPATH=%PYTHONPATH%;.
python -m bitget_trader_analysis.main --limit 100

echo.
echo Done. Dashboard generated as dashboard.html
pause
