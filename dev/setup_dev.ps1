[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptRoot
$VenvDir = Join-Path $ProjectRoot ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$Requirements = Join-Path $ProjectRoot "requirements.txt"

Set-Location $ProjectRoot

if (-not (Test-Path -LiteralPath $VenvPython)) {
    python -m venv $VenvDir
}

& $VenvPython -m pip install --upgrade pip

if (Test-Path -LiteralPath $Requirements) {
    & $VenvPython -m pip install -r $Requirements
}

& $VenvPython -m pip install black isort ruff pytest pre-commit
& $VenvPython -m pre_commit install

Write-Host "Development environment is ready."
Write-Host "Use '.\.venv\Scripts\python.exe -m app.main' to start the app."
