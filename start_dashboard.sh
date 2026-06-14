#!/usr/bin/env bash

LOG=/var/log/dashboard.log

echo "--- $(date): Starting dashboard ---" >> "$LOG"

cd /root/LumaLEDPiDashboard >> "$LOG" 2>&1 || {
    echo "ERROR: Failed to cd to /root/LumaLEDPiDashboard" >> "$LOG"
    exit 1
}

export PATH="/root/.local/bin:$PATH"

uv run python app.py >> "$LOG" 2>&1
echo "ERROR: dashboard exited with code $?" >> "$LOG"
