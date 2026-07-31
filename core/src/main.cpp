#include <iostream>
#include <string>
#include "voxlabs_core.h"

#ifdef __EMSCRIPTEN__
#include <emscripten/emscripten.h>
#else
#define EMSCRIPTEN_KEEPALIVE
#endif

extern "C" {

EMSCRIPTEN_KEEPALIVE
const char* process_voice(const char* input_voice, const char* emotion) {
    // Placeholder for actual C++ voice declone/emotion processing logic
    static std::string result;
    result = std::string("Processed voice: ") + input_voice + " with emotion: " + emotion;
    
    std::cout << "C++ Core: " << result << std::endl;
    
    return result.c_str();
}

}

int main() {
    std::cout << "VoxLabs C++ Core Initialized." << std::endl;
    return 0;
}
