#include "controllers/voice_controller.h"
#include "utils/logger.h"

namespace voxlabs {
namespace controllers {

using namespace std;

VoiceController::VoiceController(services::VoiceService& service) : voiceService(service) {
    utils::Logger::info("VoiceController initialized");
}

VoiceController::~VoiceController() {
}

std::string VoiceController::handleCloneVoiceRequest(const std::string& requestBody) {
    utils::Logger::info("Handling clone voice request");
    std::string mockName = "test_voice";
    std::string mockPath = "/path/to/audio.wav";
    
    bool success = voiceService.cloneVoice(mockName, mockPath);
    return success ? "{\"status\":\"success\"}" : "{\"status\":\"error\"}";
}

std::string VoiceController::handleSynthesizeRequest(const std::string& requestBody) {
    utils::Logger::info("Handling synthesize request");
    voiceService.synthesizeGGUF("Hello world", "model.gguf");
    return "{\"status\":\"success\", \"audio\":\"mock_audio_data\"}";
}

std::string VoiceController::handleTestRequest(const std::string& requestBody) {
    utils::Logger::info("Handling test request");
    return "{\"status\":\"success\", \"message\":\"test route reached\"}";
}

} // namespace controllers
} // namespace voxlabs
