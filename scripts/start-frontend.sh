#!/usr/bin/env bash
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/frontend"
echo "Starting frontend on http://localhost:3000 ..."
exec npm run dev
