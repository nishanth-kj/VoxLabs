# VoxLabs Master Release Build Script
$ErrorActionPreference = "Stop"

Write-Host "`n🚀 Starting VoxLabs Release Build...`n" -ForegroundColor Cyan

# Check for Administrator privileges
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (-not $isAdmin) {
    Write-Warning "⚠️  You are NOT running as Administrator."
    Write-Warning "   Electron build might fail with 'Cannot create symbolic link' errors."
    Write-Warning "   Recommendation: Right-click your terminal and select 'Run as Administrator'."
    Start-Sleep -Seconds 3
}

# Robustly find project root
if (Test-Path "api") {
    # Already in root
} elseif (Test-Path "../api") {
    Write-Host "Detected subdirectory, moving to project root..." -ForegroundColor Cyan
    Set-Location ..
} else {
    Write-Error "Could not find project root (looking for 'api' folder). Please run from c:\Projects\VoxLabs"
    exit 1
}

# 1. Build Python Sidecar
Write-Host " [1/3] Building Backend Sidecar..." -ForegroundColor Yellow
Set-Location "api"
try {
    if (Get-Command "uv" -ErrorAction SilentlyContinue) {
        ./build_sidecar.ps1
    } else {
        Write-Error "'uv' is not found. Please install uv from https://astral.sh/uv"
        exit 1
    }
} catch {
    Write-Error "Backend build failed: $_"
    exit 1
}
Set-Location ..

# 2. Build Frontend (Electron React UI)
Write-Host "`n🎨 [2/3] Building Frontend (React UI)..." -ForegroundColor Yellow
Set-Location "electron/ui"
try {
    npm install
    npm run build
} catch {
    Write-Error "Frontend build failed: $_"
    exit 1
}
Set-Location ../..

# 3. Build Desktop Installer (Electron)
Write-Host "`n [3/3] Building Desktop Installer (Electron)..." -ForegroundColor Yellow
Set-Location "electron"
try {
    npm install
    npm run dist
} catch {
    Write-Error "Desktop build failed: $_"
    exit 1
}
Set-Location ..

Write-Host "`nBuild Complete!" -ForegroundColor Green
Write-Host "Installer location: electron/dist/VoxLabs Setup 2.0.0.exe"
