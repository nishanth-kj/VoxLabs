param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

$BuildDir = "build"

# Load .env file if it exists
$envFile = Join-Path $PSScriptRoot "..\.env"
if (Test-Path $envFile) {
    Get-Content $envFile | Where-Object { -not [string]::IsNullOrWhiteSpace($_) -and -not $_.TrimStart().StartsWith([char]35) } | ForEach-Object {
        $name, $value = $_.Split('=', 2)
        [Environment]::SetEnvironmentVariable($name.Trim(), $value.Trim())
    }
}

# Use VCPKG_TOOLCHAIN from environment, or fallback to default
$VcpkgToolchain = $env:VCPKG_TOOLCHAIN
if ([string]::IsNullOrWhiteSpace($VcpkgToolchain)) {
    $VcpkgToolchain = "C:\vcpkg\scripts\buildsystems\vcpkg.cmake"
}

# Ensure the toolchain path is absolute so CMake finds it from the build dir
if (-not [System.IO.Path]::IsPathRooted($VcpkgToolchain)) {
    $VcpkgToolchain = Join-Path $PSScriptRoot "..\$VcpkgToolchain"
}
$VcpkgToolchain = [System.IO.Path]::GetFullPath($VcpkgToolchain)

if ($Clean) {
    Write-Host "Cleaning build directory..."
    if (Test-Path $BuildDir) {
        Remove-Item -Path $BuildDir -Recurse -Force
    }
}

if (-not (Test-Path $BuildDir)) {
    New-Item -ItemType Directory -Path $BuildDir | Out-Null
}

Push-Location $BuildDir

Write-Host "Configuring CMake project..."
if (Test-Path $VcpkgToolchain) {
    cmake .. -DCMAKE_TOOLCHAIN_FILE="$VcpkgToolchain"
} else {
    Write-Warning "VCPKG_ROOT environment variable not set or toolchain not found at $VcpkgToolchain. Configuring without vcpkg toolchain..."
    cmake ..
}

Write-Host "Building project..."
cmake --build . --config Release

Pop-Location
Write-Host "Build finished successfully!"
Write-Host "Executables are located in the build/Release (or build/Debug) directory."
