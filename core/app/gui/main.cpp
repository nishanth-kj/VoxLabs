#include <iostream>
#include "main_window.h"
#include "utils/logger.h"
#include "repositories/voice_repository.h"
#include "services/voice_service.h"
#include <windows.h>

int main(int argc, char** argv) {
    // Disable QuickEdit mode to prevent the console from freezing the GUI when clicked
    HANDLE hInput = GetStdHandle(STD_INPUT_HANDLE);
    DWORD prev_mode;
    if (GetConsoleMode(hInput, &prev_mode)) {
        SetConsoleMode(hInput, prev_mode & ~ENABLE_QUICK_EDIT_MODE);
    }

    voxlabs::utils::Logger::info("VoxLabs GUI Initializing...");

    voxlabs::repositories::VoiceRepository voiceRepo;
    voiceRepo.initializeDatabase("voxlabs.db");

    voxlabs::services::VoiceService voiceService(voiceRepo);

    voxlabs::gui::MainWindow mainWindow(voiceService);
    mainWindow.show();

    return 0;
}
