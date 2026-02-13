#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

module load python

if [ ! -d _venv ]; then
  echo "Creating virtual environment _venv..."
  python -m venv _venv
fi

source _venv/bin/activate

echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
poetry install

echo "Starting server..."
poetry run main
