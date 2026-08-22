#!/bin/bash
set -e

TARGET="core"
MODE="api"
ENV="debug"

while [[ $# -gt 0 ]]; do
  case $1 in
    --target)
      TARGET="$2"
      shift 2
      ;;
    --mode)
      MODE="$2"
      shift 2
      ;;
    --env)
      ENV="$2"
      shift 2
      ;;
    *)
      echo "Unknown option $1"
      exit 1
      ;;
  esac
done

EXE_PATH=""
if [ "$TARGET" == "api" ]; then
    EXE_PATH="build/voxlabs_api"
elif [ "$TARGET" == "gui" ]; then
    EXE_PATH="build/voxlabs_gui"
else
    EXE_PATH="build/voxlabs_core"
fi

# Fallback for Windows environments running under Git Bash
if [ ! -f "$EXE_PATH" ] && [ -f "${EXE_PATH}.exe" ]; then
    EXE_PATH="${EXE_PATH}.exe"
fi
# Fallback for CMake Release/Debug folders
if [ ! -f "$EXE_PATH" ]; then
    if [ -f "build/Release/$(basename $EXE_PATH)" ]; then
        EXE_PATH="build/Release/$(basename $EXE_PATH)"
    elif [ -f "build/Debug/$(basename $EXE_PATH)" ]; then
        EXE_PATH="build/Debug/$(basename $EXE_PATH)"
    fi
fi

if [ ! -f "$EXE_PATH" ]; then
    echo "Executable not found at $EXE_PATH. Please run scripts/build.sh first."
    exit 1
fi

echo "Running $EXE_PATH..."
if [ "$TARGET" == "core" ]; then
    ./"$EXE_PATH" --mode="$MODE" --env="$ENV"
else
    ./"$EXE_PATH"
fi
