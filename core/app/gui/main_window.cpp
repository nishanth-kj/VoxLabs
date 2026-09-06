#include "main_window.h"
#include "utils/logger.h"
#include <raylib.h>

namespace voxlabs {
namespace gui {

MainWindow::MainWindow(services::VoiceService& service) : voiceService(service) {
    utils::Logger::info("GUI Main Window instantiated");
}

MainWindow::~MainWindow() {
}

void MainWindow::show() {
    utils::Logger::info("Showing GUI Main Window");
    
    const int screenWidth = 800;
    const int screenHeight = 450;
    
    // Enable V-Sync to prevent Raylib from busy-waiting and consuming 100% CPU on Windows
    SetConfigFlags(FLAG_VSYNC_HINT);
    InitWindow(screenWidth, screenHeight, "VoxLabs C++ Core GUI");
    SetTargetFPS(60);

    Rectangle btnClone = { 190, 250, 200, 40 };
    Rectangle btnSynth = { 410, 250, 200, 40 };
    std::string statusMessage = "Waiting for action...";

    while (!WindowShouldClose()) {
        // Update
        Vector2 mousePoint = GetMousePosition();
        bool btnCloneHover = CheckCollisionPointRec(mousePoint, btnClone);
        bool btnSynthHover = CheckCollisionPointRec(mousePoint, btnSynth);

        if (btnCloneHover && IsMouseButtonPressed(MOUSE_BUTTON_LEFT)) {
            bool success = voiceService.cloneVoice("GuiTestVoice", "/path/to/gui_audio.wav");
            statusMessage = success ? "Success: Voice Cloned!" : "Error: Cloning failed.";
        }
        if (btnSynthHover && IsMouseButtonPressed(MOUSE_BUTTON_LEFT)) {
            voiceService.synthesizeGGUF("Hello from GUI", "gui_model.gguf");
            statusMessage = "Success: Synthesis started!";
        }

        // Draw
        BeginDrawing();
        ClearBackground(RAYWHITE);
        
        DrawText("VoxLabs Core Engine Running...", 190, 150, 20, DARKGRAY);
        DrawText(statusMessage.c_str(), 190, 200, 16, MAROON);

        // Draw Clone Button
        DrawRectangleRec(btnClone, btnCloneHover ? LIGHTGRAY : GRAY);
        DrawText("Test Clone Voice", btnClone.x + 20, btnClone.y + 10, 20, BLACK);

        // Draw Synth Button
        DrawRectangleRec(btnSynth, btnSynthHover ? LIGHTGRAY : GRAY);
        DrawText("Test Synthesize", btnSynth.x + 25, btnSynth.y + 10, 20, BLACK);

        EndDrawing();

        // Workaround for known vcpkg Raylib bug on Windows where EndDrawing fails to process events properly
        PollInputEvents();
        SwapScreenBuffer();
    }

    CloseWindow();
}

} // namespace gui
} // namespace voxlabs
