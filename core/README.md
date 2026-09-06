# VoxLabs C++ Core

The `core` directory houses the high-performance backend engine for VoxLabs. Built entirely in modern C++17, it utilizes a strict, production-ready layered architecture to provide blazing-fast voice cloning and text-to-speech synthesis using GGML.

## Architecture

The architecture is divided into distinct layers to separate concerns, making it highly modular and testable. 
All header files are stored in `include/` and all implementation files in `src/`.

* **`app/`**: Contains the bootstrap logic for the entry points (e.g., `api_server`, `main_window`).
* **`controllers/`**: The HTTP interface layer. Bridges web requests to the underlying services.
* **`services/`**: The business logic layer. Handles AI model loading, GGML inference, and core processing (`voice_service`).
* **`repositories/`**: The data access layer. Interfaces directly with SQLite for data persistence (`voice_repository`).
* **`models/`**: Defines the fundamental data structures (`voice_model`).
* **`middleware/`**: Request interceptors for Drogon (Auth, Logging, Rate Limiting).
* **`database/`**: Handles SQLite connection pooling and migrations.
* **`common/`**: Shared utilities like `logger`, `error`, and `result` types.

## Executables

The CMake build system creates three distinct executables to allow running the engine in different contexts. All of them dynamically link to the underlying `voxlabs_lib` library that houses the core architecture.

1. **`voxlabs_api`** (`app/api/main.cpp`): A standalone, headless HTTP server using Drogon.
2. **`voxlabs_gui`** (`app/gui/main.cpp`): A standalone Graphical User Interface built with Raylib for local debugging.
3. **`voxlabs_core`** (`main.cpp`): A unified master entry point that can launch both the API and GUI on separate threads.

## Dependencies

The project relies on `vcpkg` for dependency management.
* **Drogon**: High-performance HTTP application framework.
* **Raylib**: Simple and easy-to-use library to enjoy videogames programming (used for local GUI).
* **GGML**: Tensor library for machine learning (used for fast, on-device AI inference).
* **SQLite3**: Lightweight, zero-configuration database.
* **FFMPEG**: Used for audio processing and conversion.

## Building and Running

We have provided convenient scripts for both Windows (PowerShell) and Linux/macOS (Bash) to streamline development.

### Building
To configure CMake and compile the project (Requires `vcpkg` to be installed and `VCPKG_ROOT` in your environment variables):

**Windows (PowerShell):**
```powershell
.\scripts\build.ps1
```
*(To perform a clean build, pass the `-Clean` flag).*

**Linux / macOS (Bash):**
```bash
./scripts/build.sh
```
*(To perform a clean build, pass the `--clean` flag).*

### Running
To execute the compiled binaries:

**Windows (PowerShell):**
```powershell
# Runs the unified voxlabs_core engine
.\scripts\run.ps1

# Runs the standalone API server
.\scripts\run.ps1 -Target api

# Runs the standalone GUI
.\scripts\run.ps1 -Target gui
```

**Linux / macOS (Bash):**
```bash
# Runs the unified voxlabs_core engine
./scripts/run.sh

# Runs the standalone API server
./scripts/run.sh --target api

# Runs the standalone GUI
./scripts/run.sh --target gui
```
