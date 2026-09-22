"""One-click FR-15 gate: ruff, collect-only, then pytest -m framework."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str]) -> None:
    print(f"+ {' '.join(command)}")
    completed = subprocess.run(command, cwd=ROOT, check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify the ACC naming-standard e2e test framework.")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Layer A only. Reserved for T11+; T1 has no canary so this is the default path.",
    )
    parser.parse_args()

    python = sys.executable
    run([python, "-m", "ruff", "check", "."])
    run([python, "-m", "pytest", "--collect-only", "-q"])
    run([python, "-m", "pytest", "-m", "framework", "-q"])


if __name__ == "__main__":
    main()
