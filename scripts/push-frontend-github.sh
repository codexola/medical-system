#!/usr/bin/env bash
# Push frontend-only branch to GitHub (Vercel deployment repo)
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

GIT="git -c safe.directory=$ROOT"

if ! $GIT show-ref --verify --quiet refs/heads/frontend-only; then
  echo "Creating frontend-only branch..."
  $GIT subtree split --prefix=frontend -b frontend-only
fi

REMOTE="${1:-frontend-repo}"
URL="${2:-https://github.com/codexola/Japanese-medical-consultation.git}"

if ! $GIT remote get-url "$REMOTE" &>/dev/null; then
  $GIT remote add "$REMOTE" "$URL"
fi

echo "Pushing frontend to $URL (branch: main)..."
$GIT push "$REMOTE" frontend-only:main --force

echo "Done. Import https://github.com/codexola/Japanese-medical-consultation in Vercel."
