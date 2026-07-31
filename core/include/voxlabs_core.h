#ifndef VOXLABS_CORE_H
#define VOXLABS_CORE_H

#ifdef __cplusplus
extern "C" {
#endif

// Core API declarations for voice cloning and emotion processing
const char* process_voice(const char* input_voice, const char* emotion);

#ifdef __cplusplus
}
#endif

#endif // VOXLABS_CORE_H
