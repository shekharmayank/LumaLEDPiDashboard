#!/usr/bin/env bash
set -e

cd /root/LumaLEDPiDashboard

export PATH="/root/.local/bin:$PATH"

exec uv run python app.py >> /var/log/dashboard.log 2>&1
