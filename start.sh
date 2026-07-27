#!/usr/bin/env bash
# Hinata Hyuga - Web Application Startup Script

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

echo "Launching Hinata Hyuga Web Application & Deep Search Engine..."
exec python3 app.py "$@"
