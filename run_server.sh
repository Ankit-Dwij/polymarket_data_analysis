#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${VENV_DIR:-.venv}"
VENV_PYTHON="${VENV_PYTHON:-$VENV_DIR/bin/python}"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "python executable '$PYTHON_BIN' not found in PATH" >&2
  exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtual environment at '$VENV_DIR'..."
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

echo "Upgrading pip inside virtual environment..."
"$VENV_PYTHON" -m pip install --upgrade pip >/dev/null

if [ -f requirements.txt ]; then
  echo "Installing dependencies from requirements.txt..."
  "$VENV_PYTHON" -m pip install -r requirements.txt
else
  echo "Warning: requirements.txt not found; skipping dependency install."
fi

export REFRESH_SECONDS="${REFRESH_SECONDS:-900}"
export SERVER_HOST="${SERVER_HOST:-0.0.0.0}"
export SERVER_PORT="${SERVER_PORT:-8000}"

echo "Starting scheduler server (refresh=${REFRESH_SECONDS}s, host=${SERVER_HOST}, port=${SERVER_PORT})"
exec "$VENV_PYTHON" server.py

