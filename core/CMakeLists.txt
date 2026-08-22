cmake_minimum_required(VERSION 3.20)
project(VoxLabsCore VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Include directories
include_directories(include)
# Add vcpkg-installed headers so the IDE can locate Drogon when vcpkg is used
# (vcpkg installs into build/vcpkg_installed in this workspace)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/build/vcpkg_installed/x64-windows/include)

# Find packages
find_package(PkgConfig QUIET)
find_package(Drogon CONFIG REQUIRED)
find_package(ggml CONFIG REQUIRED)
find_package(unofficial-sqlite3 CONFIG REQUIRED)
find_package(raylib CONFIG REQUIRED)

# Core Library
file(GLOB_RECURSE LIB_SOURCES "src/*.cpp")
list(APPEND LIB_SOURCES "app/api/api_server.cpp" "app/gui/main_window.cpp")
add_library(voxlabs_lib ${LIB_SOURCES})

target_link_libraries(voxlabs_lib 
    PUBLIC
    Drogon::Drogon 
    ggml::ggml 
    unofficial::sqlite3::sqlite3
    raylib
)

if(PKG_CONFIG_FOUND)
    pkg_check_modules(FFMPEG IMPORTED_TARGET libavcodec libavformat libavutil)
    if(TARGET PkgConfig::FFMPEG)
        target_link_libraries(voxlabs_lib PUBLIC PkgConfig::FFMPEG)
    endif()
endif()

# API Executable
add_executable(voxlabs_api app/api/main.cpp)
target_link_libraries(voxlabs_api voxlabs_lib)

# GUI Executable
add_executable(voxlabs_gui app/gui/main.cpp)
target_link_libraries(voxlabs_gui voxlabs_lib)

# Unified Executable
add_executable(voxlabs_core main.cpp)
target_link_libraries(voxlabs_core voxlabs_lib)

# Hide terminal in Release mode for GUI executables
if(CMAKE_BUILD_TYPE STREQUAL "Release")
    set_target_properties(voxlabs_gui PROPERTIES WIN32_EXECUTABLE TRUE)
    set_target_properties(voxlabs_core PROPERTIES WIN32_EXECUTABLE TRUE)
    if(MSVC)
        target_link_options(voxlabs_gui PRIVATE "/ENTRY:mainCRTStartup")
        target_link_options(voxlabs_core PRIVATE "/ENTRY:mainCRTStartup")
    endif()
endif()
