#!/usr/bin/env bash
# Hinata Hyuga - Web Application Startup Script

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

echo "Launching Hinata FastAPI Companion Backend..."
exec python3 -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 2027 "$@"
