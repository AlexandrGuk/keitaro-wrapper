#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND="$ROOT/backend"
cd "$BACKEND"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created backend/.env from .env.example — fill KEITARO_BASE_URL, KEITARO_API_KEY, APP_PASSWORD, SESSION_SECRET"
fi

.venv/bin/python -m alembic upgrade head
echo "Install done. Run: ./scripts/start.sh"
