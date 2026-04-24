#!/bin/bash

# Bitget Trader Analysis - Startup Script
# Located inside bitget_trader_analysis/

# Ensure we are in the script's directory
cd "$(dirname "$0")"

# Ensure .venv exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment in $(pwd)/.venv..."
    python3 -m venv .venv
fi

# Activate
source .venv/bin/activate

# Use python -m pip to be safe
echo "Checking dependencies..."
python3 -m pip install --upgrade pip -q
python3 -m pip install -q pandas rich jinja2 requests python-dotenv

# Run the analysis
# Move up to the project root (CODE/) to run as a module
cd ..
export PYTHONPATH=$PYTHONPATH:.
python3 -m bitget_trader_analysis.main --limit 100

echo ""
echo "Done. Dashboard generated as dashboard.html"
read -p "Press enter to close..."
