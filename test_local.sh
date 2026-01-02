#!/bin/bash
# Quick test script for data_updater.py

cd /home/ankitdwij/Ankit/stationx/prediction_markets_test

echo "=== Setting up environment ==="
# Activate venv if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "Virtual environment activated"
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "WARNING: .env file not found. Create it with PK and SPREADSHEET_URL"
    echo "Example:"
    echo "  PK=your_private_key"
    echo "  SPREADSHEET_URL=your_spreadsheet_url"
fi

echo ""
echo "=== Running data_updater.py ==="
python data_updater.py

echo ""
echo "=== Checking output files ==="
if [ -d "data" ]; then
    echo "CSV files in data/:"
    ls -lh data/*.csv 2>/dev/null || echo "No CSV files found"
    echo ""
    echo "First few lines of all_markets.csv:"
    head -5 data/all_markets.csv 2>/dev/null || echo "all_markets.csv not found"
else
    echo "data/ directory not found"
fi

