"""Qwen3-TTS helper process. It runs with the Python of its own engine environment (data/engines/qwen3-tts),
never VoxLabs' own, so it must not import `app`.

    python qwen3_worker.py MODEL_DIR DEVICE

MODEL_DIR holds the Base model (voice cloning) and custom_voice/ (the built-in speakers). Each is loaded the
first time a request needs it, so using only one kind of voice keeps only that model in memory.

Protocol, one JSON object per line: it answers {"ready": true, "device": ...} at start, then each request
{"text", "language", "ref_audio" or "speaker", "temperature", "seed"} gets {"audio": base64 float32 mono,
"sr": ...} or {"error": ...}. It exits when stdin closes. Library chatter goes to stderr, so stdout carries
only these messages.
"""

import base64
import json
import os
import sys

# ISO codes VoxLabs uses -> Qwen3-TTS language names. Anything else is detected ("auto").
LANGUAGES = {"en": "english", "zh": "chinese", "ja": "japanese", "ko": "korean", "de": "german", "fr": "french",
             "ru": "russian", "pt": "portuguese", "es": "spanish", "it": "italian"}


def main() -> None:
    reply = sys.stdout
    sys.stdout = sys.stderr
    model_dir, device = sys.argv[1], sys.argv[2]

    def send(message: dict) -> None:
        reply.write(json.dumps(message) + "\n")
        reply.flush()

    try:
        import numpy as np
        import torch  # pyright: ignore[reportMissingImports]
        from qwen_tts import Qwen3TTSModel  # pyright: ignore[reportMissingImports]
    except Exception as exc:
        send({"error": f"Qwen3-TTS could not start: {exc}"})
        return
    if not (device.startswith("cuda") and torch.cuda.is_available()):
        device = "cpu"
    dtype = torch.bfloat16 if device.startswith("cuda") else torch.float32
    models: dict = {}

    def model(kind: str):
        if kind not in models:
            path = model_dir if kind == "clone" else os.path.join(model_dir, "custom_voice")
            loaded = Qwen3TTSModel.from_pretrained(path, device_map=device, dtype=dtype)
            other = next(iter(models.values()), None)
            if other is not None:  # both models use the same speech tokenizer: keep one in memory
                loaded.model.load_speech_tokenizer(other.model.speech_tokenizer)
            models[kind] = loaded
        return models[kind]

    send({"ready": True, "device": device})
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            request = json.loads(line)
            if request.get("seed") is not None:
                torch.manual_seed(int(request["seed"]))
            options = {"temperature": request["temperature"]} if request.get("temperature") is not None else {}
            engine = model("clone" if request.get("ref_audio") else "voices")
            supported = {str(name).lower() for name in (engine.get_supported_languages() or [])}
            language = LANGUAGES.get(str(request.get("language") or "")[:2].lower(), "auto")
            language = language if language in supported else "auto"
            if request.get("ref_audio"):
                wavs, sr = engine.generate_voice_clone(text=request["text"], language=language,
                                                       ref_audio=request["ref_audio"], x_vector_only_mode=True,
                                                       **options)
            else:
                wavs, sr = engine.generate_custom_voice(text=request["text"], language=language,
                                                        speaker=request["speaker"], **options)
            audio = np.asarray(wavs[0], dtype="<f4").reshape(-1)
            send({"audio": base64.b64encode(audio.tobytes()).decode("ascii"), "sr": int(sr)})
        except Exception as exc:
            send({"error": str(exc) or type(exc).__name__})


if __name__ == "__main__":
    main()
