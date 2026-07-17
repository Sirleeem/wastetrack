# Build a clean academic/production zip without secrets or local junk.
# Usage: .\scripts\package-deliverable.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$stamp = Get-Date -Format "yyyyMMdd"
$outDir = Join-Path $root "dist"
$stage = Join-Path $outDir "wastetrack-deliverable"
$zipPath = Join-Path $outDir "WasteTrack-Production-Deliverable-$stamp.zip"

if (Test-Path $stage) { Remove-Item -Recurse -Force $stage }
New-Item -ItemType Directory -Path $stage | Out-Null

$excludeDirs = @(".venv", "venv", "__pycache__", ".git", "instance", "dist", ".pytest_cache", ".mypy_cache", ".idea", ".vscode")
$excludeFiles = @(".env", "*.pyc", "*.db")

function ShouldSkip($fullPath) {
    $rel = $fullPath.Substring($root.Length).TrimStart("\", "/")
    foreach ($d in $excludeDirs) {
        if ($rel -eq $d -or $rel.StartsWith("$d\") -or $rel.StartsWith("$d/")) { return $true }
        if ($rel -match [regex]::Escape("\$d\") -or $rel -match "/$d/") { return $true }
    }
    if ($rel -eq ".env") { return $true }
    if ($rel -like "*.pyc") { return $true }
    if ($rel -like "*.db") { return $true }
    return $false
}

Get-ChildItem -Path $root -Recurse -Force | Where-Object {
    -not $_.PSIsContainer -and -not (ShouldSkip $_.FullName)
} | ForEach-Object {
    $rel = $_.FullName.Substring($root.Length).TrimStart("\", "/")
    # skip nested __pycache__ files
    if ($rel -match "__pycache__") { return }
    $dest = Join-Path $stage $rel
    $destParent = Split-Path $dest -Parent
    if (-not (Test-Path $destParent)) {
        New-Item -ItemType Directory -Path $destParent -Force | Out-Null
    }
    Copy-Item $_.FullName $dest -Force
}

# Ensure empty runtime dirs exist in package
New-Item -ItemType Directory -Force -Path (Join-Path $stage "instance") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $stage "app\static\uploads") | Out-Null
Set-Content -Path (Join-Path $stage "instance\.gitkeep") -Value ""
if (-not (Test-Path (Join-Path $stage "app\static\uploads\.gitkeep"))) {
    Set-Content -Path (Join-Path $stage "app\static\uploads\.gitkeep") -Value ""
}

if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
Compress-Archive -Path (Join-Path $stage "*") -DestinationPath $zipPath -Force

Write-Host "Deliverable ready:"
Write-Host "  $zipPath"
Write-Host "Includes DEPLOY.md, Docker, wsgi, .env.example (no secrets)."
