#!/bin/bash
# DialLoopPro.command
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the application
python3 dialloop_mac.py