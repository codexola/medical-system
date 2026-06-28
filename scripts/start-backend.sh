#!/usr/bin/env bash
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
source .venv/bin/activate
set -a && source "$ROOT/.env" && set +a
cd backend
echo "Starting backend on http://localhost:8000 ..."
exec uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
