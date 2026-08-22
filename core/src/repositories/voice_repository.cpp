#include "repositories/voice_repository.h"
#include "utils/logger.h"

namespace voxlabs {
namespace repositories {

VoiceRepository::VoiceRepository() : isInitialized(false) {
}

VoiceRepository::~VoiceRepository() {
}

bool VoiceRepository::initializeDatabase(const std::string& dbPath) {
    utils::Logger::info("Initializing database at: " + dbPath);
    isInitialized = true;
    return true;
}

bool VoiceRepository::saveVoice(const models::VoiceModel& voice) {
    if (!isInitialized) return false;
    utils::Logger::info("Saving voice: " + voice.name);
    return true;
}

std::vector<models::VoiceModel> VoiceRepository::getAllVoices() {
    utils::Logger::info("Fetching all voices from DB");
    return std::vector<models::VoiceModel>();
}

} // namespace repositories
} // namespace voxlabs
