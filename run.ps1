# Windows interviewer path. On macOS or Linux use ./run.sh instead.
# Headed + slowmo so the reviewer can watch each click.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
# 500 ms between Playwright actions; omit --slowmo for a faster local rerun.
$SlowmoMs = 500
python -m pytest tests/test_acceptance.py -m acceptance --headed --slowmo $SlowmoMs --reruns 0
