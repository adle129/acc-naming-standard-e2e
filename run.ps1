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
$MsgNeedUsername = "Pass a username, or pass neither argument for the homework account."
$MsgNeedPassword = "Password is empty. Type it at the prompt, or pass it in single quotes."
$PasswordPrompt = "Password"

# Optional reviewer login. Project id and folder stay in .env.
# Username only: prompt so !, &, and ( do not break the shell.
$HasUsername = -not [string]::IsNullOrWhiteSpace($Username)
$HasPassword = -not [string]::IsNullOrWhiteSpace($Password)
if ($HasPassword -and -not $HasUsername) {
    Write-Error "$Usage`n$MsgNeedUsername"
    exit 1
}
if ($HasUsername) {
    if (-not $HasPassword) {
        $Secure = Read-Host -Prompt $PasswordPrompt -AsSecureString
        $Bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($Secure)
        $Password = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($Bstr)
        [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($Bstr)
        if ([string]::IsNullOrWhiteSpace($Password)) {
            Write-Error $MsgNeedPassword
            exit 1
        }
    }
    $env:ACC_USERNAME = $Username
    $env:ACC_PASSWORD = $Password
}

# 500 ms between Playwright actions; omit --slowmo for a faster local rerun.
$SlowmoMs = 500
python -m pytest tests/test_acceptance.py -m acceptance --headed --slowmo $SlowmoMs --reruns 0
