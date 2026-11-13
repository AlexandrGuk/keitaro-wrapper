$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$Venv = Join-Path $Backend ".venv"
$Python = Join-Path $Venv "Scripts\python.exe"
$EnvFile = Join-Path $Backend ".env"
$EnvExample = Join-Path $Backend ".env.example"

Set-Location $Backend

if (-not (Test-Path $Venv)) {
    python -m venv .venv
}

& $Python -m pip install --upgrade pip
& $Python -m pip install -r requirements.txt

if (-not (Test-Path $EnvFile)) {
    Copy-Item $EnvExample $EnvFile
    Write-Host "Created backend\.env from .env.example — fill KEITARO_BASE_URL, KEITARO_API_KEY, APP_PASSWORD, SESSION_SECRET"
}

& $Python -m alembic upgrade head
Write-Host "Install done. Run: ./scripts/start.sh  (Windows: .\scripts\start.ps1)"
