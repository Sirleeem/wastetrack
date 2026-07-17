# Production start script for Windows (Waitress)
# Usage (from project root):
#   .\scripts\start-prod.ps1
#   .\scripts\start-prod.ps1 -Port 8000

param(
    [int]$Port = 0
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
}

& .\.venv\Scripts\python -m pip install -q -r requirements.txt

if (-not (Test-Path ".env")) {
    Write-Warning ".env not found. Copy .env.example to .env and set SECRET_KEY + ADMIN_PASSWORD."
}

if ($Port -gt 0) {
    $env:PORT = "$Port"
}
if (-not $env:PORT) { $env:PORT = "8000" }
if (-not $env:FLASK_ENV) { $env:FLASK_ENV = "production" }
if (-not $env:BEHIND_PROXY) { $env:BEHIND_PROXY = "false" }

Write-Host "Starting WasteTrack (Waitress) on http://0.0.0.0:$($env:PORT)"
& .\.venv\Scripts\waitress-serve --listen="0.0.0.0:$($env:PORT)" wsgi:app
