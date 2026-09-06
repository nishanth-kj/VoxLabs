#include <iostream>
#include "api_server.h"
#include "utils/logger.h"
#include "repositories/voice_repository.h"
#include "services/voice_service.h"
#include "controllers/voice_controller.h"

int main(int argc, char** argv) {
    voxlabs::utils::Logger::info("VoxLabs API Server Initializing...");

    voxlabs::repositories::VoiceRepository voiceRepo;
    voiceRepo.initializeDatabase("voxlabs.db");

    voxlabs::services::VoiceService voiceService(voiceRepo);
    voxlabs::controllers::VoiceController voiceController(voiceService);

    voxlabs::app::ApiServer apiServer(voiceService, voiceController);
    apiServer.start(8080);

    return 0;
}
