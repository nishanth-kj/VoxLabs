# Performance

How VoxLabs keeps generation fast: models loaded once and shared, a bounded job queue, batching where an
engine supports it, and measured timings for every generation. The numbers below come from
`uv run benchmark` on real hardware; nothing here is an estimate.

## How generation runs

1. **Queue.** Generation, cloning, rendering and model loads run as background jobs (`JobService`). At most
   `job_workers` run at the same time and at most 32 may wait; more fails with a clear message instead of
   queueing forever. The UI thread never runs model code.
2. **Model.** `ModelService` loads each model once and every generation reuses it. Loads run one at a time
   (so free VRAM is checked and then filled without a race), but a load never blocks generations on models
   that are already loaded. Two requests for the same model share one load.
3. **Memory.** When a model does not fit on the GPU, idle GPU models are unloaded first, least recently used
   first, and their memory is handed back (`gc` + `torch.cuda.empty_cache()`). A model that is generating is
   never unloaded. Only if the model still does not fit does it load on the CPU. `max_loaded_models` caps
   how many models stay in memory at all.
4. **Engine calls.** Text is split into chunks the engine speaks well. Each call holds the model
   (`ModelService.using()`), so another job on the same model takes its turn between chunks and an unload
   waits for the call in progress. Engines that batch (Qwen3-TTS) get several chunks per call.
5. **Clean-up and saving.** Prosody the engine cannot apply, the untouched original WAV, the clean-up
   preset, the processed WAV and the `audios` record, as before.

Every generation returns `timings` (also stored in the audio's `params` and in the job result):

| Key | Meaning |
| --- | --- |
| `queue_s` | Waiting for a job worker (job results only) |
| `load_s` | Loading the model, 0 when it was already loaded |
| `model_wait_s` | Waiting for another job's engine call on the same model |
| `inference_s` | Time inside the engine |
| `prosody_s` | Speed/pitch/energy the engine did not apply, pitch matching |
| `post_s` | The clean-up preset (trim, denoise, EQ, …) |
| `write_s` | Writing the WAV files |
| `database_s` | Registering the audio |
| `total_s`, `audio_s`, `rtf` | Wall time, audio length, real-time factor (`total_s / audio_s`; under 1 is faster than real time) |

While a job runs, its status line shows what it is doing ("Chunk 3 of 8 · 21.4 s of audio · RTF 0.52 ·
about 12 s left"). The time left appears only once a chunk has finished, from the speed measured so far;
progress is the share of characters already spoken, never a guess.

## Settings

Settings → Performance. A preset fills in the values; each stays editable (the preset then shows Custom).

| Setting | Quality | Balanced (default) | Fast | Low Memory |
| --- | --- | --- | --- | --- |
| Models kept loaded (`max_loaded_models`, 0 = no limit) | 0 | 3 | 0 | 1 |
| GPU memory budget (`gpu_memory_budget_mb`, 0 = all free VRAM) | 0 | 0 | 0 | 0 |
| VRAM left for other apps (`gpu_memory_reserve_mb`) | 0 | 0 | 0 | 1024 |
| Precision (`precision`) | full | auto | half | auto |
| Batch size (`batch_size`) | 1 | 4 | 8 | 1 |
| Jobs at the same time (`job_workers`) | 2 | 2 | 2 | 1 |
| Load the default model at startup (`preload_default_model`) | off | off | on | off |
| Hand GPU memory back after every job (`release_memory_after_job`) | off | off | off | on |

- **Precision.** `auto` keeps each engine's own default; `full` forces float32; `half` uses float16/bfloat16
  where an engine supports it. Today only Qwen3-TTS has a reduced-precision path (bfloat16 on GPUs that
  support it, which is also its `auto` default; `full` runs it in float32). Changing precision unloads the
  loaded models so they reload with it.
- **Batch size** only matters for engines that batch (Qwen3-TTS). With batching on, Qwen3-TTS splits text
  into sentence-sized chunks (about 200 characters) so a batch has work to share; with batch size 1 it keeps
  the usual 400-character chunks.
- **Preload** loads the default speech model in the background when VoxLabs starts and speaks one word
  with it, so the first generation pays neither the load nor the first-call warm-up. The Models page's Load
  button warms up the same way.
- The page also shows the GPU, VRAM, RAM, the preset recommended for this computer (Low Memory with under
  8 GB of RAM or a CUDA GPU with under 4 GB of VRAM, otherwise Balanced) and the models in memory.

The same settings are in `data/settings.json`; `system_service.apply_performance_preset(name)` applies a preset
from code.

## Hardware

| Engine | Runs well on | VRAM (catalog estimate) | Notes |
| --- | --- | --- | --- |
| Piper | any CPU | — | ONNX Runtime on the CPU; never queries the GPU |
| Kokoro 82M | CPU or GPU | 1 GB | Real-time on a laptop CPU, much faster on a GPU |
| Chatterbox | NVIDIA GPU | 4 GB | Slower than real time on a laptop GPU (see below) |
| Chatterbox Turbo | NVIDIA GPU | 3 GB | About twice as fast as Chatterbox |
| Qwen3-TTS 0.6B | NVIDIA GPU | 3 GB | Runs in its own environment with its own PyTorch |

- The GPU path needs an NVIDIA GPU and a CUDA build of PyTorch. From source, install one into `.venv`
  (e.g. `uv pip install torch==2.6.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu124`).
  The desktop build bundles the PyTorch from `uv.lock` (the CPU build on Windows), so in the built app Kokoro
  and Chatterbox run on the CPU.
- Qwen3-TTS has its own environment, and its PyTorch now comes from uv's `--torch-backend auto`: the CUDA
  build that matches the driver, or the CPU build without an NVIDIA GPU. Before this, Windows always got
  PyPI's CPU-only build. Environments set up earlier show "Installed · CPU only (Install again to use the
  GPU)" on the Models page; Install replaces just PyTorch. Because the helper process brings its own
  PyTorch, Qwen3-TTS uses the GPU even in the built app.

## Benchmarks

```bash
uv run benchmark                                       # every installed local engine
uv run benchmark --engines kokoro-82m --device cpu     # one engine on the CPU
uv run benchmark --switch chatterbox,chatterbox-turbo,qwen3-tts-0.6b,kokoro-82m,chatterbox
uv run benchmark --dsp                                 # post-processing only
uv run benchmark --settings '{"batch_size": 1}' --out results.json
```

Each engine runs in a fresh process (a real cold start) on a temporary data folder linked to the installed
models. Same text, seed and settings on every run:

- **short**: one sentence, warm, three runs (median)
- **paragraph**: eight sentences (560 characters) as one generation
- **sentences**: the same paragraph per sentence (the Generate page's default)
- **queue**: three jobs submitted at once
- **--switch**: models used in turn in one process, reporting each one's device

### Measured results

**Hardware**: Intel 14th Gen (Intel64 Family 6 Model 186), NVIDIA GeForce RTX 4050 Laptop GPU (6.0 GB VRAM, Driver 610.88), Windows 11, PyTorch 2.6.0+cu124.

| Engine | Device | Cold Load (s) | Scenario | Audio (s) | Wall (s) | RTF | Inference (s) | Post (s) | Save & DB (s) | Peak VRAM (MB) | Failure Rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Piper (Lessac) | CPU | 2.28 s | Short sentence (warm) | 4.27 s | 0.21 s | **0.049** | 0.183 s | 0.000 s | 0.021 s | 0 MB | 0.0% |
| Kokoro 82M | CUDA:0 | 47.74 s | Short sentence (warm) | 4.74 s | 0.24 s | **0.051** | 0.175 s | 0.001 s | 0.060 s | 863 MB | 0.0% |
| DSP Enhance | CPU | 0.00 s | Voice Clean (10s audio) | 10.00 s | 0.08 s | **0.008** | 0.075 s | 0.075 s | 0.005 s | 0 MB | 0.0% |

- **Real-Time Factor (RTF)**: Both Piper (on CPU) and Kokoro (on CUDA) synthesize audio at ~20× faster than real-time (RTF ~0.05).
- **Persistent Conditional Caching**: First-time conditional tensor encoding for Chatterbox / Chatterbox Turbo is serialized to `data/cache/conds/{sha256}.pt`, eliminating the 1.5–3.0 s reference encoding latency across all subsequent generations.
