param(
    [string]$Target = "core", # Options: core, api, gui
    [string]$Mode = "api",    # Used if Target is 'core' (e.g. api, gui)
    [string]$Env = "debug"    # e.g. debug, prod
)

$ErrorActionPreference = "Stop"

$ExePath = ""
if ($Target -eq "api") {
    $ExePath = "build\Release\voxlabs_api.exe"
    if (-not (Test-Path $ExePath)) { $ExePath = "build\Debug\voxlabs_api.exe" }
} elseif ($Target -eq "gui") {
    $ExePath = "build\Release\voxlabs_gui.exe"
    if (-not (Test-Path $ExePath)) { $ExePath = "build\Debug\voxlabs_gui.exe" }
} else {
    $ExePath = "build\Release\voxlabs_core.exe"
    if (-not (Test-Path $ExePath)) { $ExePath = "build\Debug\voxlabs_core.exe" }
}

if (-not (Test-Path $ExePath)) {
    Write-Error "Executable not found at $ExePath. Please run scripts\build.ps1 first."
    exit 1
}

Write-Host "Running $ExePath..."
if ($Target -eq "core") {
    & $ExePath --mode=$Mode --env=$Env
} else {
    & $ExePath
}
