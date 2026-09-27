class Backend:
    """Engine ids understood by app/utils/model.py."""

    EMOTIONAL = "emotional"  # gTTS + librosa DSP (online, opt-in)
    EDGE = "edge"  # Microsoft Edge neural TTS (online, opt-in)
    PIPER = "piper"
    KOKORO = "kokoro"
    CHATTERBOX = "chatterbox"
    CHATTERBOX_TURBO = "chatterbox-turbo"
    QWEN3 = "qwen3-tts"  # runs in its own engine environment (see ENGINE_ENVIRONMENTS)
    MFCC = "mfcc"  # built-in voice profile extractor (local, no downloads)
    DSP = "dsp"  # built-in scipy enhancement (local)
