cmake_minimum_required(VERSION 3.20)
project(VoxLabsCore VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Include directories
include_directories(include)

# Source files
set(SOURCES
    src/main.cpp
)

# If compiling with Emscripten for WebAssembly
if(EMSCRIPTEN)
    add_executable(voxlabs_core ${SOURCES})
    
    # WebAssembly specific flags
    set_target_properties(voxlabs_core PROPERTIES LINK_FLAGS "-s WASM=1 -s EXPORTED_RUNTIME_METHODS='[\"ccall\", \"cwrap\"]' -s MODULARIZE=1 -s EXPORT_NAME='VoxLabsCore'")
else()
    # Standard desktop/server build
    add_executable(voxlabs_core ${SOURCES})

    # Find and link FFmpeg (provided by vcpkg)
    find_package(PkgConfig QUIET)
    if(PKG_CONFIG_FOUND)
        pkg_check_modules(FFMPEG IMPORTED_TARGET libavcodec libavformat libavutil)
        if(TARGET PkgConfig::FFMPEG)
            target_link_libraries(voxlabs_core PkgConfig::FFMPEG)
        endif()
    endif()
endif()
