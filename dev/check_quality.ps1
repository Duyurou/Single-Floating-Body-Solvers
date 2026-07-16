[CmdletBinding()]
param(
    [switch]$Fix
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptRoot
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

Set-Location $ProjectRoot

if (Test-Path -LiteralPath $VenvPython) {
    $Python = $VenvPython
} else {
    $Python = "python"
}

function Invoke-QualityCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    & $Python @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed: $Python $($Arguments -join ' ')"
    }
}

if ($Fix) {
    Invoke-QualityCommand -Arguments @(
        "-m",
        "black",
        "app",
        "core",
        "ui",
        "tests"
    )
    Invoke-QualityCommand -Arguments @(
        "-m",
        "isort",
        "app",
        "core",
        "ui",
        "tests"
    )
    Invoke-QualityCommand -Arguments @(
        "-m",
        "ruff",
        "check",
        "--fix",
        "app",
        "core",
        "ui",
        "tests"
    )
} else {
    Invoke-QualityCommand -Arguments @(
        "-m",
        "black",
        "--check",
        "app",
        "core",
        "ui",
        "tests"
    )
    Invoke-QualityCommand -Arguments @(
        "-m",
        "isort",
        "--check-only",
        "app",
        "core",
        "ui",
        "tests"
    )
    Invoke-QualityCommand -Arguments @(
        "-m",
        "ruff",
        "check",
        "app",
        "core",
        "ui",
        "tests"
    )
}

Invoke-QualityCommand -Arguments @("-m", "pytest")
