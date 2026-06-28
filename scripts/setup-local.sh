#!/usr/bin/env bash
# Kenko AI — local startup (no Docker required)
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "==> Checking services..."

# Redis
if ! redis-cli ping &>/dev/null; then
  echo "Starting Redis..."
  sudo systemctl start redis-server 2>/dev/null || sudo service redis-server start
fi
echo "  Redis: OK"

# PostgreSQL
if ! sudo -u postgres psql -d kenko -c "SELECT 1" &>/dev/null; then
  echo "Creating database 'kenko'..."
  sudo -u postgres psql -c "CREATE USER kenko WITH PASSWORD 'kenko';" 2>/dev/null || true
  sudo -u postgres psql -c "CREATE DATABASE kenko OWNER kenko;" 2>/dev/null || true
  sudo -u postgres psql -d kenko -c "CREATE EXTENSION IF NOT EXISTS vector;"
fi
echo "  PostgreSQL: OK"

# Python venv
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q -r "$ROOT/backend/requirements.txt"

# Seed (idempotent)
echo "==> Seeding database..."
set -a && source "$ROOT/.env" && set +a
(cd "$ROOT/backend" && PYTHONPATH=. python scripts/seed_data.py) 2>/dev/null || true

# Frontend deps
if [ ! -d "frontend/node_modules" ]; then
  echo "==> Installing frontend dependencies..."
  (cd frontend && npm install)
fi

echo ""
echo "============================================"
echo "  Kenko AI — ready to start"
echo "============================================"
echo ""
echo "  Terminal 1 (backend):"
echo "    cd $ROOT && ./scripts/start-backend.sh"
echo ""
echo "  Terminal 2 (frontend):"
echo "    cd $ROOT/frontend && npm run dev"
echo ""
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:8000"
echo "  API docs:  http://localhost:8000/docs"
echo "  Admin:     admin@kenko-ai.jp / admin123"
echo ""
