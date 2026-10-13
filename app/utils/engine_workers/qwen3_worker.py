"""Qwen3-TTS helper process. It runs with the Python of its own engine environment (data/engines/qwen3-tts),
never VoxLabs' own, so it must not import `app`.

    python qwen3_worker.py MODEL_DIR DEVICE [PRECISION]

MODEL_DIR holds the Base model (voice cloning) and custom_voice/ (the built-in speakers). Each is loaded the
first time a request needs it, so using only one kind of voice keeps only that model in memory. PRECISION is
"auto" (bfloat16 on a GPU that supports it), "full" (float32) or "half" (bfloat16, else float16).

Protocol, one JSON object per line: it answers {"ready": true, "device": ...} at start, then each request
{"texts": [...], "language", "ref_audio" or "speaker", "temperature", "seed"} gets {"audios": [base64 float32
mono, one per text], "sr": ...} or {"error": ...}. The texts are generated as one batch. It exits when stdin
closes. Library chatter goes to stderr, so stdout carries only these messages.
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
    precision = sys.argv[3] if len(sys.argv) > 3 else "auto"

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
    if device == "cpu" or precision == "full":
        dtype = torch.float32
    elif torch.cuda.is_bf16_supported():
        dtype = torch.bfloat16
    else:
        dtype = torch.float16 if precision == "half" else torch.float32
    models: dict = {}
    prompts: dict = {}  # (ref_audio, mtime) -> voice-clone prompt, so a sample is analysed once

    def model(kind: str):
        if kind not in models:
            path = model_dir if kind == "clone" else os.path.join(model_dir, "custom_voice")
            loaded = Qwen3TTSModel.from_pretrained(path, device_map=device, dtype=dtype)
            other = next(iter(models.values()), None)
            if other is not None:  # both models use the same speech tokenizer: keep one in memory
                loaded.model.load_speech_tokenizer(other.model.speech_tokenizer)
            models[kind] = loaded
        return models[kind]

    def clone_prompt(engine, ref_audio: str):
        key = (ref_audio, os.path.getmtime(ref_audio))
        if key not in prompts:
            prompts[key] = engine.create_voice_clone_prompt(ref_audio=ref_audio, x_vector_only_mode=True)
        return prompts[key]

    send({"ready": True, "device": device})
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            request = json.loads(line)
            texts = request.get("texts") or [request["text"]]
            if request.get("seed") is not None:
                torch.manual_seed(int(request["seed"]))
            options = {"temperature": request["temperature"]} if request.get("temperature") is not None else {}
            engine = model("clone" if request.get("ref_audio") else "voices")
            supported = {str(name).lower() for name in (engine.get_supported_languages() or [])}
            language = LANGUAGES.get(str(request.get("language") or "")[:2].lower(), "auto")
            language = language if language in supported else "auto"
            if request.get("ref_audio"):
                wavs, sr = engine.generate_voice_clone(text=texts, language=[language] * len(texts),
                                                       voice_clone_prompt=clone_prompt(engine, request["ref_audio"]),
                                                       **options)
            else:
                wavs, sr = engine.generate_custom_voice(text=texts, language=[language] * len(texts),
                                                        speaker=[request["speaker"]] * len(texts), **options)
            audios = [base64.b64encode(np.asarray(wav, dtype="<f4").reshape(-1).tobytes()).decode("ascii")
                      for wav in wavs]
            send({"audios": audios, "sr": int(sr)})
        except Exception as exc:
            send({"error": str(exc) or type(exc).__name__})


if __name__ == "__main__":
    main()
