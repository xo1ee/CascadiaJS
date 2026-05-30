#!/bin/bash
# SiteLens — start backend + frontend for demo
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Starting backend (port 8000)..."
"$DIR/geo_service/.venv/bin/python" -m uvicorn main:app --host 0.0.0.0 --port 8000 --app-dir "$DIR" &
PID_BACK=$!

echo "Starting frontend (port 3000)..."
cd "$DIR/web" && npm run dev &
PID_FRONT=$!

echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "Press Ctrl+C to stop both."

trap "kill $PID_BACK $PID_FRONT 2>/dev/null" EXIT
wait
