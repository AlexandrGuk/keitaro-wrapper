#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
PYTHON="$BACKEND/.venv/bin/python"

if [ ! -x "$PYTHON" ]; then
  echo "Venv missing. Run ./scripts/install.sh first." >&2
  exit 1
fi

if [ ! -f "$BACKEND/.env" ]; then
  echo "backend/.env missing. Run ./scripts/install.sh and fill credentials." >&2
  exit 1
fi

cd "$BACKEND"
exec "$PYTHON" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
