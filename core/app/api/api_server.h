#pragma once
#include "services/voice_service.h"
#include "controllers/voice_controller.h"

namespace voxlabs {
namespace app {

class ApiServer {
public:
    ApiServer(services::VoiceService& service, controllers::VoiceController& controller);
    ~ApiServer();

    void start(int port);
    static void stop();

private:
    services::VoiceService& voiceService;
    controllers::VoiceController& voiceController;
};

} // namespace app
} // namespace voxlabs
