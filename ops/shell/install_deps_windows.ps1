#!/usr/bin/env pwsh
Write-Host "[windows] Checking prerequisites" -ForegroundColor Cyan

function Test-Command($cmd) {
    $null -ne (Get-Command $cmd -ErrorAction SilentlyContinue)
}

if (-not (Test-Command "choco")) {
    Write-Host "Chocolatey not found. Install it from https://chocolatey.org/install then re-run." -ForegroundColor Yellow
    exit 0
}

Write-Host "[windows] Installing tools via Chocolatey" -ForegroundColor Cyan
choco install -y python nodejs-lts redis-64 postgresql --ignore-checksums

Write-Host "[windows] Dependency installation complete" -ForegroundColor Green
