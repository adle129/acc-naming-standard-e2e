# Windows interviewer path. On macOS or Linux use ./run.sh instead.
# Headed + slowmo so the reviewer can watch each click.
param(
    [Parameter(Position = 0)]
    [string]$Username = "",
    [Parameter(Position = 1)]
    [string]$Password = ""
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# Usage lives in one place so the error and the comment stay aligned.
$Usage = "Usage: .\run.ps1 [[-Username] user] [[-Password] pass]"
$MsgNeedBoth = "Pass both username and password, or pass neither for the homework account."

# Optional reviewer login. Project id and folder stay in .env.
$HasUsername = -not [string]::IsNullOrWhiteSpace($Username)
$HasPassword = -not [string]::IsNullOrWhiteSpace($Password)
if ($HasUsername -or $HasPassword) {
    if (-not $HasUsername -or -not $HasPassword) {
        Write-Error "$Usage`n$MsgNeedBoth"
        exit 1
    }
    $env:ACC_USERNAME = $Username
    $env:ACC_PASSWORD = $Password
}

# 500 ms between Playwright actions; omit --slowmo for a faster local rerun.
$SlowmoMs = 500
python -m pytest tests/test_acceptance.py -m acceptance --headed --slowmo $SlowmoMs --reruns 0
