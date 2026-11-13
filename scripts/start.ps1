$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$Python = Join-Path $Backend ".venv\Scripts\python.exe"
$EnvFile = Join-Path $Backend ".env"

if (-not (Test-Path $Python)) {
    Write-Error "Venv missing. Run .\scripts\install.ps1 first."
}

if (-not (Test-Path $EnvFile)) {
    Write-Error "backend\.env missing. Run .\scripts\install.ps1 and fill credentials."
}

Set-Location $Backend
& $Python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
