"""Qwen3-TTS helper process. It runs with the Python of its own engine environment (data/engines/qwen3-tts),
never VoxLabs' own, so it must not import `app`.

    python qwen3_worker.py MODEL_DIR DEVICE

Protocol, one JSON object per line: it answers {"ready": true, "device": ...} once the model is loaded, then
each request {"text", "language", "ref_audio", "temperature", "seed"} gets {"audio": base64 float32 mono,
"sr": ...} or {"error": ...}. It exits when stdin closes. Library chatter goes to stderr, so stdout carries
only these messages.
"""

import base64
import json
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

        if not (device.startswith("cuda") and torch.cuda.is_available()):
            device = "cpu"
        dtype = torch.bfloat16 if device.startswith("cuda") else torch.float32
        model = Qwen3TTSModel.from_pretrained(model_dir, device_map=device, dtype=dtype)
        supported = {str(name).lower() for name in (model.get_supported_languages() or [])}
    except Exception as exc:
        send({"error": f"Qwen3-TTS could not load: {exc}"})
        return
    send({"ready": True, "device": device})

    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            request = json.loads(line)
            if request.get("seed") is not None:
                torch.manual_seed(int(request["seed"]))
            language = LANGUAGES.get(str(request.get("language") or "")[:2].lower(), "auto")
            options = {"temperature": request["temperature"]} if request.get("temperature") is not None else {}
            wavs, sr = model.generate_voice_clone(
                text=request["text"], language=language if language in supported else "auto",
                ref_audio=request["ref_audio"], x_vector_only_mode=True, **options,
            )
            audio = np.asarray(wavs[0], dtype="<f4").reshape(-1)
            send({"audio": base64.b64encode(audio.tobytes()).decode("ascii"), "sr": int(sr)})
        except Exception as exc:
            send({"error": str(exc) or type(exc).__name__})


if __name__ == "__main__":
    main()
