#pragma once
#include "services/voice_service.h"

namespace voxlabs {
namespace gui {

class MainWindow {
public:
    MainWindow(services::VoiceService& service);
    ~MainWindow();

    void show();

private:
    services::VoiceService& voiceService;
};

} // namespace gui
} // namespace voxlabs
