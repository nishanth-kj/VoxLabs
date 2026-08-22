#!/bin/bash
set -e

BUILD_DIR="build"
VCPKG_TOOLCHAIN="${VCPKG_ROOT}/scripts/buildsystems/vcpkg.cmake"

if [ "$1" == "--clean" ] || [ "$1" == "-c" ]; then
    echo "Cleaning build directory..."
    rm -rf "$BUILD_DIR"
fi

mkdir -p "$BUILD_DIR"
pushd "$BUILD_DIR" > /dev/null

echo "Configuring CMake project..."
if [ -f "$VCPKG_TOOLCHAIN" ]; then
    cmake .. -DCMAKE_TOOLCHAIN_FILE="$VCPKG_TOOLCHAIN" -DCMAKE_BUILD_TYPE=Release
else
    echo "WARNING: VCPKG_ROOT environment variable not set or toolchain not found at $VCPKG_TOOLCHAIN. Configuring without vcpkg toolchain..."
    cmake .. -DCMAKE_BUILD_TYPE=Release
fi

echo "Building project..."
cmake --build . --config Release

popd > /dev/null
echo "Build finished successfully!"
echo "Executables are located in the build/ directory."
