#!/usr/bin/env bash
# macOS / Linux interviewer path. On Windows use .\run.ps1 instead.
# Headed + slowmo so the reviewer can watch each click.
set -euo pipefail
cd "$(dirname "$0")"

# Usage lives in one place so the error and the comment stay aligned.
USAGE="Usage: ./run.sh [username] [password]"
MSG_NEED_USERNAME="Pass a username, or pass neither argument for the homework account."
MSG_NEED_PASSWORD="Password is empty. Type it at the prompt, or pass it in single quotes."
MSG_PASSWORD_PROMPT="Password: "
MSG_NEED_PYTHON="Python 3.11 or newer is required. On macOS: python3 -m pip install -r requirements.txt"

# Optional reviewer login. Project id and folder stay in .env.
# One argument (username) prompts for the password so zsh does not expand ! or &.
if [ "$#" -eq 0 ]; then
  :
elif [ "$#" -eq 1 ]; then
  export ACC_USERNAME="$1"
  printf "%s" "${MSG_PASSWORD_PROMPT}" >&2
  read -r -s ACC_PASSWORD
  echo >&2
  export ACC_PASSWORD
  if [ -z "${ACC_PASSWORD}" ]; then
    echo "${MSG_NEED_PASSWORD}" >&2
    exit 1
  fi
elif [ "$#" -eq 2 ]; then
  export ACC_USERNAME="$1"
  export ACC_PASSWORD="$2"
else
  echo "${USAGE}" >&2
  echo "${MSG_NEED_USERNAME}" >&2
  exit 1
fi

# macOS has python3, not python. Prefer a local venv when the reviewer created one.
if [ -x ".venv/bin/python" ]; then
  PYTHON=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON="python"
else
  echo "${MSG_NEED_PYTHON}" >&2
  exit 1
fi
# 500 ms between Playwright actions; omit --slowmo for a faster local rerun.
SLOWMO_MS=500
"${PYTHON}" -m pytest tests/test_acceptance.py -m acceptance --headed --slowmo "${SLOWMO_MS}" --reruns 0
