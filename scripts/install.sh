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
  echo "Created backend/.env"
fi

.venv/bin/python -m alembic upgrade head

echo
echo "Install done."
echo "Login: guk / keitaro  (see APP_USERNAME / APP_PASSWORD in backend/.env)"
echo "Fill KEITARO_BASE_URL and KEITARO_API_KEY in backend/.env, then:"
echo "  ./scripts/start.sh"
echo "Open http://127.0.0.1:8000"
