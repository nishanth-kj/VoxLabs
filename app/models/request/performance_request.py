from pydantic import BaseModel


class PerformanceRequest(BaseModel):
    """Change performance settings: `preset` (quality, balanced, fast, low_memory) fills in every value, then
    any value given here replaces the preset's. Fields left out stay as they are."""

    preset: str | None = None
    max_loaded_models: int | None = None
    gpu_memory_budget_mb: int | None = None
    gpu_memory_reserve_mb: int | None = None
    precision: str | None = None
    batch_size: int | None = None
    job_workers: int | None = None
    preload_default_model: bool | None = None
    release_memory_after_job: bool | None = None
