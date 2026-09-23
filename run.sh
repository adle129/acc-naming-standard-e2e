#!/usr/bin/env bash
# macOS / Linux interviewer path. On Windows use .\run.ps1 instead.
# Headed + slowmo so the reviewer can watch each click.
set -euo pipefail
cd "$(dirname "$0")"
# macOS has python3, not python. Prefer a local venv when the reviewer created one.
if [ -x ".venv/bin/python" ]; then
  PYTHON=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON="python"
else
  echo "Python 3.11 or newer is required. On macOS: python3 -m pip install -r requirements.txt" >&2
  exit 1
fi
# 500 ms between Playwright actions; omit --slowmo for a faster local rerun.
SLOWMO_MS=500
"${PYTHON}" -m pytest tests/test_acceptance.py -m acceptance --headed --slowmo "${SLOWMO_MS}" --reruns 0
