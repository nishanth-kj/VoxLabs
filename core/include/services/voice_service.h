#pragma once
#include <string>
#include "repositories/voice_repository.h"

namespace voxlabs {
namespace services {

class VoiceService {
public:
    VoiceService(repositories::VoiceRepository& repo);
    ~VoiceService();

    bool cloneVoice(const std::string& voiceName, const std::string& audioFilePath);
    void synthesizeGGUF(const std::string& text, const std::string& modelPath);

private:
    repositories::VoiceRepository& voiceRepo;
};

} // namespace services
} // namespace voxlabs
