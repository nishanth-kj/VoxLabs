#include <iostream>
#include <string>
#include <thread>
#include <atomic>
#include <windows.h>

#include "utils/logger.h"
#include "repositories/voice_repository.h"
#include "services/voice_service.h"
#include "app/api/api_server.h"
#include "controllers/voice_controller.h"
#include "app/gui/main_window.h"

using namespace voxlabs;

int main(int argc, char** argv) {

    // Disable QuickEdit mode to prevent the console from freezing the GUI when clicked
    HANDLE hInput = GetStdHandle(STD_INPUT_HANDLE);
    DWORD prev_mode;
    if (GetConsoleMode(hInput, &prev_mode)) {
        SetConsoleMode(hInput, prev_mode & ~ENABLE_QUICK_EDIT_MODE);
    }

    utils::Logger::info("VoxLabs Unified C++ Core Initializing...");

    repositories::VoiceRepository voiceRepo;
    voiceRepo.initializeDatabase("voxlabs.db");

    services::VoiceService voiceService(voiceRepo);
    controllers::VoiceController voiceController(voiceService);

    utils::Logger::info("VoxLabs Architecture Wired Successfully.");

    // Start the Drogon API Server in a background thread
    // Drogon blocks the thread it runs on, while Raylib must run on the main thread.
    std::thread apiThread([&voiceService, &voiceController]() {
        utils::Logger::info("Launching API Server on port 8080 (Background Thread)...");
        app::ApiServer apiServer(voiceService, voiceController);
        apiServer.start(8080);
    });

    // Start Raylib GUI on the main thread
    utils::Logger::info("Launching Graphical User Interface (Main Thread)...");
    gui::MainWindow mainWindow(voiceService);
    mainWindow.show();

    utils::Logger::info("GUI closed. Shutting down VoxLabs Engine...");
    
    // We tell the API server to quit safely and join the thread so the program can gracefully exit without crashing
    app::ApiServer::stop();
    apiThread.join(); 

    return 0;
}
