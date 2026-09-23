#!/usr/bin/env bash
# macOS / Linux interviewer path. On Windows use .\run.ps1 instead.
# Headed + slowmo so the reviewer can watch each click.
set -euo pipefail
cd "$(dirname "$0")"
# 500 ms between Playwright actions; omit --slowmo for a faster local rerun.
SLOWMO_MS=500
python -m pytest tests/test_acceptance.py -m acceptance --headed --slowmo "${SLOWMO_MS}" --reruns 0
