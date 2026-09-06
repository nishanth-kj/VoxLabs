#pragma once
#include "services/voice_service.h"
#include <string>

namespace voxlabs {
namespace controllers {

class VoiceController {
public:
    VoiceController(services::VoiceService& service);
    ~VoiceController();

    std::string handleCloneVoiceRequest(const std::string& requestBody);
    std::string handleSynthesizeRequest(const std::string& requestBody);
    std::string handleTestRequest(const std::string& requestBody);

private:
    services::VoiceService& voiceService;
};

} // namespace controllers
} // namespace voxlabs
