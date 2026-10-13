"""Performance presets. Choosing one (Settings, or `PUT /api/settings`) copies its values into the
individual settings below, which stay editable; the code only ever reads the individual settings.

- max_loaded_models        models kept in memory at once (0 = no limit). The least recently used one is
                           unloaded first. Models on the GPU also make room for each other when VRAM runs out.
- gpu_memory_budget_mb     VRAM VoxLabs' models may use together (0 = whatever is free).
- gpu_memory_reserve_mb    VRAM left free for other programs when deciding whether a model fits on the GPU.
- precision                "auto" (each engine's own default), "full" (float32 everywhere) or "half"
                           (float16/bfloat16 where the engine supports it; see docs/performance.md).
- batch_size               text chunks sent to an engine in one call, for engines that batch (Qwen3-TTS).
- job_workers              background jobs that run at the same time.
- preload_default_model    load the default speech model in the background when VoxLabs starts.
- release_memory_after_job hand cached GPU memory back to the system after every job.
"""

PERFORMANCE_PRESETS = {
    "quality": {
        "max_loaded_models": 0,
        "gpu_memory_budget_mb": 0,
        "gpu_memory_reserve_mb": 0,
        "precision": "full",
        "batch_size": 1,
        "job_workers": 2,
        "preload_default_model": False,
        "release_memory_after_job": False,
    },
    "balanced": {
        "max_loaded_models": 3,
        "gpu_memory_budget_mb": 0,
        "gpu_memory_reserve_mb": 0,
        "precision": "auto",
        "batch_size": 4,
        "job_workers": 2,
        "preload_default_model": False,
        "release_memory_after_job": False,
    },
    "fast": {
        "max_loaded_models": 0,
        "gpu_memory_budget_mb": 0,
        "gpu_memory_reserve_mb": 0,
        "precision": "half",
        "batch_size": 8,
        "job_workers": 2,
        "preload_default_model": True,
        "release_memory_after_job": False,
    },
    "low_memory": {
        "max_loaded_models": 1,
        "gpu_memory_budget_mb": 0,
        "gpu_memory_reserve_mb": 1024,
        "precision": "auto",
        "batch_size": 1,
        "job_workers": 1,
        "preload_default_model": False,
        "release_memory_after_job": True,
    },
}
PERFORMANCE_PRESET_LABELS = {"quality": "Quality", "balanced": "Balanced", "fast": "Fast", "low_memory": "Low Memory"}
DEFAULT_PERFORMANCE_PRESET = "balanced"
PRECISIONS = ("auto", "full", "half")

# Pending jobs allowed at once; submitting more fails with a clear message instead of queueing forever.
JOB_QUEUE_LIMIT = 32
JOB_WORKERS_MAX = 4
BATCH_SIZE_MAX = 16
