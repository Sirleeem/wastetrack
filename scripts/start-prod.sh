#!/usr/bin/env bash
# Production start script for Linux/macOS (Gunicorn)
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -r requirements.txt

if [[ ! -f .env ]]; then
  echo "WARNING: .env not found. Copy .env.example to .env and set SECRET_KEY + ADMIN_PASSWORD."
fi

export FLASK_ENV="${FLASK_ENV:-production}"
export PORT="${PORT:-8000}"
export BEHIND_PROXY="${BEHIND_PROXY:-true}"

echo "Starting WasteTrack (Gunicorn) on 0.0.0.0:${PORT}"
exec gunicorn -c gunicorn.conf.py wsgi:app
