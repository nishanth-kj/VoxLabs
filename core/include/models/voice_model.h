#pragma once
#include <string>

namespace voxlabs {
namespace models {

struct VoiceModel {
    std::string voiceId;
    std::string name;
    std::string filePath;
    bool hasConsent;
};

} // namespace models
} // namespace voxlabs
