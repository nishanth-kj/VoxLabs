#pragma once
#include <vector>
#include <string>
#include "models/voice_model.h"

namespace voxlabs {
namespace repositories {

class VoiceRepository {
public:
    VoiceRepository();
    ~VoiceRepository();

    bool initializeDatabase(const std::string& dbPath);
    bool saveVoice(const models::VoiceModel& voice);
    std::vector<models::VoiceModel> getAllVoices();

private:
    bool isInitialized;
};

} // namespace repositories
} // namespace voxlabs
