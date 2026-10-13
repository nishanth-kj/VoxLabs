"""Generation performance: model lifecycle and caching, the job queue, batching, timings and presets."""

import threading
import time

import numpy as np
import pytest

from app.constants.performance import PERFORMANCE_PRESETS
from app.constants.status import Status
from app.exceptions import JobError, ValidationError
from app.models.request import TTSRequest
from app.services import job_service as job_service_module
from app.services import model_service as model_service_module
from app.services.audio_service import audio_service
from app.services.job_service import job_service
from app.services.model_service import model_service
from app.services.system_service import system_service
from app.services.tts_service import tts_service
from app.utils import audio as au
from app.utils import device as device_utils
from app.utils.model import WorkerBackend, register_backend
from tests.conftest import FAKE_SR, FakeBackend

GPU_MB = 1000


class GpuBackend(FakeBackend):
    """A fake engine that 'uses' its catalog VRAM on cuda:0 while loaded."""

    backend_id = "fakegpu"
    loads: list[str] = []

    @classmethod
    def available_devices(cls):
        return ["cpu", "cuda:0"]

    def load(self):
        GpuBackend.loads.append(f"{self.model_dir.name}@{self.device}")
        super().load()


def _gpu_model(key: str, vram_mb: int) -> dict:
    return {"key": key, "name": key, "model_type": "tts", "backend": "fakegpu", "version": "1", "size_mb": 0,
            "vram_mb": vram_mb, "online": False, "package": None, "extra": None, "capabilities": ["tts"]}


@pytest.fixture
def gpu(monkeypatch):
    """A 1000 MB GPU whose free memory drops by each loaded GPU model's catalog VRAM."""
    models = [_gpu_model("gpu-a", 600), _gpu_model("gpu-b", 600), _gpu_model("gpu-c", 300)]
    catalog = model_service_module.MODEL_CATALOG + models
    monkeypatch.setattr(model_service_module, "MODEL_CATALOG", catalog)
    monkeypatch.setattr(model_service_module, "_CATALOG", {m["key"]: m for m in catalog})
    register_backend("fakegpu", GpuBackend)
    GpuBackend.loads = []

    def gpus():
        used = model_service._gpu_mb_in_use()
        return [{"index": 0, "name": "Fake GPU", "vram_total_mb": GPU_MB, "vram_free_mb": GPU_MB - used}]

    monkeypatch.setattr(device_utils, "gpus", gpus)
    monkeypatch.setattr(device_utils, "available_devices", lambda: ["cpu", "cuda:0"])
    model_service.sync_catalog()
    return models


# ---------------------------------------------------------------- model lifecycle

def test_a_model_loads_once_and_every_generation_reuses_it(gpu):
    for text in ("First generation.", "Second generation.", "Third one."):
        tts_service.generate(TTSRequest(text=text, model_key="gpu-a", post={}))
    assert GpuBackend.loads == ["gpu-a@cuda:0"]


def test_simultaneous_requests_share_one_load():
    loads, gate = [], threading.Event()

    class SlowBackend(FakeBackend):
        def load(self):
            loads.append(1)
            gate.wait(5)
            super().load()

    register_backend("fake", SlowBackend)
    results = []
    threads = [threading.Thread(target=lambda: results.append(model_service.backend_for("fake-tts"))) for _ in range(4)]
    for thread in threads:
        thread.start()
    time.sleep(0.2)
    gate.set()
    for thread in threads:
        thread.join(5)
    assert len(loads) == 1 and len(results) == 4 and len({id(backend) for backend in results}) == 1


def test_loading_one_model_does_not_block_a_loaded_one():
    model_service.load("fake-clone")
    gate, started = threading.Event(), threading.Event()

    class SlowBackend(FakeBackend):
        def load(self):
            started.set()
            gate.wait(5)
            super().load()

    register_backend("fake", SlowBackend)
    loader = threading.Thread(target=lambda: model_service.load("fake-tts"))
    loader.start()
    started.wait(5)
    begin = time.perf_counter()
    assert model_service.backend_for("fake-clone").loaded  # answered while fake-tts is still loading
    assert time.perf_counter() - begin < 1.0
    gate.set()
    loader.join(5)


def test_the_loaded_model_limit_unloads_the_least_recently_used(gpu):
    system_service.update_settings(max_loaded_models=2)
    model_service.load("fake-tts")
    model_service.load("fake-clone")
    model_service.backend_for("fake-tts")  # used most recently
    model_service.load("gpu-c")
    assert {m["key"] for m in model_service.loaded_models()} == {"fake-tts", "gpu-c"}


def test_gpu_models_make_room_for_each_other(gpu, monkeypatch):
    released = []
    monkeypatch.setattr(model_service_module, "release_memory", lambda device=None: released.append(device))
    assert model_service.load("gpu-a")["loaded_device"] == "cuda:0"
    # 600 + 600 MB does not fit in 1000 MB: the idle model is unloaded (and its memory released) first.
    assert model_service.load("gpu-b")["loaded_device"] == "cuda:0"
    assert not model_service.get("gpu-a")["loaded"] and "cuda:0" in released
    assert model_service.load("gpu-c")["loaded_device"] == "cuda:0"  # 300 MB fits next to it
    assert model_service.get("gpu-b")["loaded"]


def test_a_model_in_use_is_never_unloaded_to_make_room(gpu):
    model_service.load("gpu-a")
    with model_service.using("gpu-a"):  # a generation is running on it
        assert model_service.load("gpu-b")["loaded_device"] == "cpu"
    assert model_service.get("gpu-a")["loaded"]


def test_the_gpu_budget_and_reserve_limit_what_fits(gpu):
    system_service.update_settings(gpu_memory_budget_mb=500)
    assert model_service.load("gpu-a")["loaded_device"] == "cpu"  # 600 MB is over the 500 MB budget
    system_service.update_settings(gpu_memory_budget_mb=0, gpu_memory_reserve_mb=800)
    assert model_service.load("gpu-c")["loaded_device"] == "cpu"  # 1000 - 800 MB reserve leaves 200 MB


def test_a_model_unloaded_during_a_generation_is_loaded_again():
    model_service.load("fake-tts")
    first = model_service.backend_for("fake-tts")
    model_service.unload("fake-tts")
    assert not first.loaded
    with model_service.using("fake-tts") as backend:
        assert backend.loaded and backend is not first


def test_unload_waits_for_the_engine_call_in_progress():
    model_service.load("fake-tts")
    inside, release, finished = threading.Event(), threading.Event(), []

    def generate():
        with model_service.using("fake-tts") as backend:
            inside.set()
            release.wait(5)
            finished.append(backend.loaded)  # still loaded: unload waited for this call

    worker = threading.Thread(target=generate)
    worker.start()
    inside.wait(5)
    unloader = threading.Thread(target=lambda: model_service.unload("fake-tts"))
    unloader.start()
    time.sleep(0.2)
    release.set()
    worker.join(5)
    unloader.join(5)
    assert finished == [True] and not model_service.get("fake-tts")["loaded"]


def test_cpu_models_never_ask_about_gpus(monkeypatch):
    def refuse():
        raise AssertionError("a CPU model must not query the GPU (that imports torch)")

    monkeypatch.setattr(device_utils, "available_devices", refuse)
    monkeypatch.setattr(device_utils, "gpus", refuse)
    assert model_service.pick_device(model_service.get("fake-tts")) == "cpu"


def test_engines_in_their_own_process_use_gpus_the_driver_reports(monkeypatch):
    """Qwen3-TTS has its own PyTorch: VoxLabs' (a CPU-only build in the desktop app) must not decide for it."""
    monkeypatch.setattr(device_utils, "available_devices", lambda: ["cpu"])
    monkeypatch.setattr(device_utils, "gpus", lambda: [{"index": 0, "name": "GPU", "vram_total_mb": 8000,
                                                        "vram_free_mb": 7000}])
    assert WorkerBackend.available_devices() == ["cpu", "cuda:0"]
    assert model_service.pick_device(model_service.get("qwen3-tts-0.6b")) == "cuda:0"


def test_preload_loads_the_default_model_only_when_asked():
    assert model_service.preload_default() is None
    system_service.update_settings(preload_default_model=True)
    job = model_service.preload_default()
    assert job is not None
    assert job_service.wait(job["jobs_id"], timeout=10)["status"] == Status.COMPLETED.code
    assert model_service.get("fake-tts")["loaded"]


# ---------------------------------------------------------------- job queue

def test_job_results_carry_queue_and_run_times():
    job = job_service.submit("test", lambda ctx: {"value": 1})
    timings = job_service.wait(job["jobs_id"], timeout=10)["result"]["timings"]
    assert timings["queue_s"] >= 0 and timings["run_s"] >= 0


def test_the_queue_is_bounded(monkeypatch):
    monkeypatch.setattr(job_service_module, "JOB_QUEUE_LIMIT", 2)
    system_service.update_settings(job_workers=1)
    release = threading.Event()
    jobs = [job_service.submit("test", lambda ctx: (release.wait(5), {})[1]) for _ in range(3)]  # 1 running, 2 wait
    time.sleep(0.2)
    with pytest.raises(JobError, match="already waiting"):
        job_service.submit("test", lambda ctx: {})
    release.set()
    for job in jobs:
        assert job_service.wait(job["jobs_id"], timeout=10)["status"] == Status.COMPLETED.code


def test_job_workers_setting_controls_concurrency():
    running, peak, lock, release = [0], [0], threading.Lock(), threading.Event()

    def work(_ctx):
        with lock:
            running[0] += 1
            peak[0] = max(peak[0], running[0])
        release.wait(0.3)
        with lock:
            running[0] -= 1
        return {}

    for workers in (1, 3):
        system_service.update_settings(job_workers=workers)
        peak[0] = 0
        jobs = [job_service.submit("test", work) for _ in range(3)]
        for job in jobs:
            job_service.wait(job["jobs_id"], timeout=10)
        assert peak[0] == workers


def test_generation_jobs_report_progress_messages_and_timings():
    seen = []
    job_service.add_listener(lambda job: seen.append((job.get("result") or {}).get("message")))
    job = tts_service.generate_async(TTSRequest(text="One sentence here. And a second one for good measure."))
    result = job_service.wait(job["jobs_id"], timeout=30)["result"]
    assert any(message and message.startswith("Chunk 1 of") for message in seen)
    assert {"queue_s", "run_s", "inference_s", "total_s", "audio_s", "rtf"} <= set(result["timings"])


# ---------------------------------------------------------------- generation

def test_timings_are_returned_and_kept_with_the_audio():
    messages = []
    audio = tts_service.generate(TTSRequest(text="Measure me."), progress=lambda v, m=None: messages.append((v, m)))
    timings = audio["timings"]
    assert timings["audio_s"] == pytest.approx(audio["duration"], abs=0.01)
    assert timings["rtf"] == pytest.approx(timings["total_s"] / timings["audio_s"], abs=0.01)
    assert {"load_s", "inference_s", "write_s"} <= set(timings)
    assert audio["params"]["timings"]["inference_s"] >= 0
    values = [value for value, _ in messages]
    assert values == sorted(values) and values[-1] == 1.0  # real progress only moves forward
    assert "s of audio" in tts_service.describe(timings)


class BatchBackend(FakeBackend):
    """Batches up to 8 chunks; records the size of every engine call."""

    max_batch = 8
    max_chunk_chars = 30
    calls: list[int] = []

    def synthesize(self, request, voice):
        BatchBackend.calls.append(1)
        return super().synthesize(request, voice)

    def synthesize_batch(self, requests, voice) -> list[tuple[np.ndarray, int]]:
        BatchBackend.calls.append(len(requests))
        return [super(BatchBackend, self).synthesize(request, voice) for request in requests]


TEXT = "First sentence is here. Second sentence follows. Third sentence now. Fourth and last one."


def test_batching_engines_get_chunks_together_in_order():
    register_backend("fake", BatchBackend)
    BatchBackend.calls = []
    system_service.update_settings(batch_size=1)
    one_by_one, sr, _ = tts_service.synthesize(TTSRequest(text=TEXT))
    assert BatchBackend.calls == [1, 1, 1, 1]
    model_service.unload_all()
    BatchBackend.calls = []
    system_service.update_settings(batch_size=3)
    batched, _, info = tts_service.synthesize(TTSRequest(text=TEXT))
    assert BatchBackend.calls == [3, 1]
    assert np.array_equal(one_by_one, batched) and sr == FAKE_SR  # same audio, same order
    assert info["timings"]["inference_s"] >= 0


def test_per_sentence_generation_matches_separate_generations():
    """Planning once must not change what each sentence sounds like or how it is labelled."""
    text = "Hello there. How are you today? Fine, thanks."
    result = tts_service.generate_sentences(TTSRequest(text=text, speed=1.2, pause_ms=300))
    assert [a["params"]["text"] for a in result["sentences"]] == ["Hello there.", "How are you today?", "Fine, thanks."]
    for index, audio in enumerate(result["sentences"]):
        alone = tts_service.generate(TTSRequest(text=audio["params"]["text"], speed=1.2, name=f"Sentence {index + 1}"))
        assert audio["name"] == alone["name"] and audio["params"]["pause_ms"] is None
        assert np.array_equal(au.load(audio["path"])[0], au.load(alone["path"])[0])
        assert np.array_equal(au.load(audio["original_path"])[0], au.load(alone["original_path"])[0])
    gaps = 2 * 0.3
    assert result["combined"]["duration"] == pytest.approx(sum(a["duration"] for a in result["sentences"]) + gaps,
                                                           abs=0.01)
    assert result["timings"]["sentences"] == 3
    assert audio_service.get(result["combined"]["audios_id"])["source"] == "rendered"


def test_release_memory_after_job_setting(monkeypatch):
    calls = []
    monkeypatch.setattr(model_service, "release_cached_memory", lambda: calls.append(1))
    tts_service.generate(TTSRequest(text="Keep the cache."))
    assert calls == []
    system_service.update_settings(release_memory_after_job=True)
    tts_service.generate(TTSRequest(text="Hand it back."))
    assert calls == [1]


# ---------------------------------------------------------------- settings

def test_presets_fill_in_the_performance_settings():
    for name, values in PERFORMANCE_PRESETS.items():
        settings = system_service.apply_performance_preset(name)
        assert settings["performance_preset"] == name
        assert {key: settings[key] for key in values} == values
    with pytest.raises(ValidationError):
        system_service.apply_performance_preset("turbo")
    with pytest.raises(ValidationError):
        system_service.update_settings(batch_size=0)
    with pytest.raises(ValidationError):
        system_service.update_settings(precision="int4")


def test_recommended_preset_follows_the_hardware():
    small_gpu = [{"index": 0, "name": "GPU", "vram_total_mb": 2048, "vram_free_mb": 2000}]
    big_gpu = [{"index": 0, "name": "GPU", "vram_total_mb": 12288, "vram_free_mb": 12000}]
    plenty = {"total": 32768, "available": 20000}
    assert device_utils.recommended_preset(small_gpu, True, plenty) == "low_memory"
    assert device_utils.recommended_preset(big_gpu, True, plenty) == "balanced"
    assert device_utils.recommended_preset([], False, {"total": 4096, "available": 1000}) == "low_memory"
    assert device_utils.recommended_preset([], False, plenty) == "balanced"
