# Build backend sidecar
Write-Host "Building backend sidecar..."

# Ensure we are in api directory
cd $PSScriptRoot

# Run PyInstaller via uv
# --onefile: bundle everything into one exe
# --name: set name (will need to match what Tauri expects, but we can rename later)
# --clean: clean cache
# --additional-hooks-dir: might be needed for hidden imports (e.g. uvicorn, engine)
# --collect-all: brute force collect problematic packages if needed

# We need to collect uvicorn and engine explicitly usually.
# Simple attempt first:

uv run pyinstaller --noconfirm --onefile --clean `
    --name "api-server" `
    --collect-all "uvicorn" `
    --collect-all "fastapi" `
    --collect-all "engine" `
    --hidden-import "uvicorn.logging" `
    --hidden-import "uvicorn.loops" `
    --hidden-import "uvicorn.loops.auto" `
    --hidden-import "uvicorn.protocols" `
    --hidden-import "uvicorn.protocols.http" `
    --hidden-import "uvicorn.protocols.http.auto" `
    --hidden-import "uvicorn.lifespan" `
    --hidden-import "uvicorn.lifespan.on" `
    --distpath "../desktop/src-tauri/bin" `
    main.py

# Rename for Tauri sidecar convention (windows x64)
# Target triple: x86_64-pc-windows-msvc
$target_triple = "x86_64-pc-windows-msvc"
$exe_path = "../desktop/src-tauri/bin/api-server.exe" 

# For Electron, we put it in electron/resources/bin
# Setup Electron dir
$electron_bin = "../electron/resources/bin"
If (!(Test-Path $electron_bin)) {
    New-Item -ItemType Directory -Force -Path $electron_bin
}
$target_path = Join-Path $electron_bin "api-server.exe"

if (Test-Path $exe_path) {
    Move-Item -Path $exe_path -Destination $target_path -Force
    Write-Host "Sidecar built successfully: $target_path"
} else {
    Write-Host "Error: PyInstaller failed to produce executable."
    exit 1
}
