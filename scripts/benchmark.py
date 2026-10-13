"""Reproducible generation benchmarks on this computer's hardware:

    uv run benchmark                                   (every installed local engine, default scenarios)
    uv run benchmark --engines kokoro-82m,chatterbox --device cpu --out results.json
    uv run benchmark --dsp                             (post-processing only, no models)
    uv run benchmark --switch chatterbox,chatterbox-turbo,kokoro-82m,chatterbox
                                                       (models used in turn in one process)

Each engine runs in a fresh process, so the first numbers are a real cold start (imports, model load,
first generation). Generation goes through the same TTSService/JobService code the desktop app and
the API use. The benchmark works on a temporary data folder that links to the installed models
(data/models, data/engines), so it never touches the library or database.

Scenarios (same text, seed and settings on every run):
    short       one sentence, warm, repeated (median reported)
    paragraph   eight sentences as one generation
    sentences   the same paragraph per sentence (the Generate page's default mode)
    queue       three jobs submitted at once through JobService

--switch generates the short sentence with each model in turn, the way someone moves between engines,
and reports where each model ended up (GPU or CPU), what stayed loaded and how long each step took.

Reported per scenario: wall time, audio duration, real-time factor (wall / audio; under 1 is faster than
real time), and the time spent in inference, post-processing, file writes and database registration.
Peak VRAM is the device-wide maximum seen by nvidia-smi minus the use before the run, so it includes
helper processes (Qwen3-TTS) and other programs. Peak RAM is this process only.
"""

import argparse
import json
import os
import platform
import shutil
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINES = ("piper-en-us-lessac-medium", "kokoro-82m", "chatterbox", "chatterbox-turbo", "qwen3-tts-0.6b")
SCENARIOS = ("short", "paragraph", "sentences", "queue")
SEED = 1234
SHORT = "The quick brown fox jumps over the lazy dog near the quiet riverbank this morning."
PARAGRAPH = (
    "Welcome to the first lesson of the course. Today we look at how sound travels through the air. "
    "Every voice starts as a small vibration in the throat. That vibration pushes on the air around it. "
    "The air carries the pattern outward as a wave of pressure. When the wave reaches your ear, the eardrum "
    "moves in the same pattern. Your brain turns that movement into words and meaning. By the end of this "
    "lesson you will be able to explain each of these steps in your own words."
)
QUEUE_TEXTS = (
    "The first job reads a short welcome message to the listener.",
    "The second job describes the weather for the coming weekend.",
    "The third job announces that the meeting has moved to Thursday.",
)


# ---------------------------------------------------------------- measurement helpers

def peak_rss_mb() -> float:
    """Peak resident memory of this process."""
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]

        counters = Counters()
        counters.cb = ctypes.sizeof(Counters)
        psapi = ctypes.WinDLL("psapi")
        kernel32 = ctypes.WinDLL("kernel32")
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
        psapi.GetProcessMemoryInfo(kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb)
        return counters.PeakWorkingSetSize / (1 << 20)
    import resource

    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return peak / (1 << 20) if sys.platform == "darwin" else peak / 1024


class GpuSampler:
    """Device-wide used VRAM from nvidia-smi, sampled on a thread."""

    def __init__(self, interval: float = 0.5):
        self.exe = shutil.which("nvidia-smi")
        self.interval = interval
        self.baseline = self.peak = self._used()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _used(self) -> int | None:
        if not self.exe:
            return None
        try:
            out = subprocess.run([self.exe, "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                                 capture_output=True, text=True, timeout=5,
                                 creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            return int(out.stdout.strip().splitlines()[0])
        except Exception:
            return None

    def _run(self):
        while not self._stop.wait(self.interval):
            used = self._used()
            if used is not None and (self.peak is None or used > self.peak):
                self.peak = used

    def start(self):
        if self.exe:
            self._thread.start()
        return self

    def stop(self) -> int | None:
        self._stop.set()
        if self._thread.is_alive():
            self._thread.join(timeout=5)
        if self.baseline is None or self.peak is None:
            return None
        return max(0, self.peak - self.baseline)


class Stages:
    """Wraps the pipeline's stage functions and adds up the time spent in each."""

    def __init__(self):
        self.totals: dict[str, float] = {}
        self.counts: dict[str, int] = {}
        self._lock = threading.Lock()
        self._depth = threading.local()  # a wrapped call inside another of the same stage counts once

    def reset(self):
        with self._lock:
            self.totals, self.counts = {}, {}

    def wrap(self, owner, name: str, stage: str):
        original = getattr(owner, name)

        def timed(*args, **kwargs):
            depth = getattr(self._depth, stage, 0)
            setattr(self._depth, stage, depth + 1)
            start = time.perf_counter()
            try:
                return original(*args, **kwargs)
            finally:
                setattr(self._depth, stage, depth)
                if depth == 0:
                    with self._lock:
                        self.totals[stage] = self.totals.get(stage, 0.0) + time.perf_counter() - start
                        self.counts[stage] = self.counts.get(stage, 0) + 1

        setattr(owner, name, timed)

    def snapshot(self) -> dict:
        with self._lock:
            return {**{f"{k}_s": round(v, 3) for k, v in self.totals.items()},
                    "engine_calls": self.counts.get("inference", 0)}


def link_dir(target: Path, link: Path) -> None:
    """A directory junction on Windows (no admin rights needed), a symlink elsewhere."""
    if sys.platform == "win32":
        import _winapi

        _winapi.CreateJunction(str(target), str(link))
    else:
        link.symlink_to(target, target_is_directory=True)


def unlink_dir(link: Path) -> None:
    if link.is_symlink() or (sys.platform == "win32" and link.exists()):
        os.rmdir(link) if sys.platform == "win32" else link.unlink()


# ---------------------------------------------------------------- one engine (child process)

def run_engine(args) -> dict:
    process_start = time.perf_counter()
    source = Path(args.source).resolve()
    workdir = Path(tempfile.mkdtemp(prefix="voxlabs-bench-"))
    for name in ("models", "engines"):
        (source / name).mkdir(parents=True, exist_ok=True)
        link_dir(source / name, workdir / name)
    os.environ["VOXLABS_DATA_DIR"] = str(workdir)
    sampler = GpuSampler().start()
    try:
        if args.switch:
            return _switch(args, sampler)
        return _measure(args, process_start, sampler)
    finally:
        sampler.stop()
        from app.services.job_service import job_service
        from app.services.model_service import model_service
        from app.utils.database import reset_engine

        job_service.shutdown(wait=True)
        model_service.unload_all()
        reset_engine()
        for name in ("models", "engines"):
            unlink_dir(workdir / name)
        shutil.rmtree(workdir, ignore_errors=True)


def _measure(args, process_start: float, sampler: GpuSampler) -> dict:
    from app.models.request import TTSRequest
    from app.services import audio_service as audio_service_module
    from app.services.job_service import job_service
    from app.services.model_service import model_service
    from app.services.system_service import system_service
    from app.services.tts_service import tts_service
    from app.utils import audio as au

    key = args.engine
    system_service.initialize()
    system_service.update_settings(device=args.device, **(json.loads(args.settings) if args.settings else {}))
    model = model_service.get(key)
    result: dict = {"engine": key, "device_requested": args.device, "scenarios": {}}
    if not model["installed"]:
        result["skipped"] = model["install_label"]
        return result

    stages = Stages()
    audio = audio_service_module.audio_service
    stages.wrap(audio, "process_array", "post")
    stages.wrap(audio, "register", "register")
    stages.wrap(au, "save", "save")
    result["import_init_s"] = round(time.perf_counter() - process_start, 3)

    start = time.perf_counter()
    model_service.load(key)
    result["load_s"] = round(time.perf_counter() - start, 3)
    backend = model_service.backend_for(key)
    result["device"] = backend.device
    for name in ("synthesize", "synthesize_batch"):
        if hasattr(backend, name):
            stages.wrap(backend, name, "inference")

    def request(text: str, **extra) -> TTSRequest:
        return TTSRequest(text=text, model_key=key, seed=SEED, **extra)

    def timed(fn) -> dict:
        stages.reset()
        start = time.perf_counter()
        out = fn()
        wall = time.perf_counter() - start
        duration = out["duration"] if "duration" in out else out["combined"]["duration"]
        row = {"wall_s": round(wall, 3), "audio_s": round(duration, 2), "rtf": round(wall / duration, 3),
               **stages.snapshot()}
        known = sum(v for k, v in row.items() if k.endswith("_s") and k not in ("wall_s", "audio_s"))
        row["other_s"] = round(max(0.0, wall - known), 3)
        return row

    result["first_generate"] = timed(lambda: tts_service.generate(request(SHORT)))
    result["cold_total_s"] = round(time.perf_counter() - process_start, 3)

    for scenario in args.scenarios:
        if scenario == "short":
            runs = [timed(lambda: tts_service.generate(request(SHORT))) for _ in range(args.repeat)]
            best = sorted(runs, key=lambda r: r["wall_s"])[len(runs) // 2]
            result["scenarios"]["short"] = {**best, "runs": [r["wall_s"] for r in runs],
                                            "median_wall_s": round(statistics.median(r["wall_s"] for r in runs), 3)}
        elif scenario == "paragraph":
            result["scenarios"]["paragraph"] = timed(lambda: tts_service.generate(request(PARAGRAPH)))
        elif scenario == "sentences":
            result["scenarios"]["sentences"] = timed(lambda: tts_service.generate_sentences(request(PARAGRAPH)))
        elif scenario == "queue":
            stages.reset()
            start = time.perf_counter()
            jobs = [tts_service.generate_async(request(text)) for text in QUEUE_TEXTS]
            finished = [job_service.wait(job["jobs_id"], timeout=3600) for job in jobs]
            wall = time.perf_counter() - start
            failed = [job["error"] for job in finished if job["status_label"] != "Completed"]
            audio_s = sum(job["result"]["audio"]["duration"] for job in finished if not job["error"])
            result["scenarios"]["queue"] = {
                "wall_s": round(wall, 3), "audio_s": round(audio_s, 2), "rtf": round(wall / audio_s, 3) if audio_s else None,
                "jobs": len(jobs), "failed": failed, **stages.snapshot(),
                "job_timings": [job["result"].get("timings") for job in finished if job.get("result")],
            }
    result["peak_rss_mb"] = round(peak_rss_mb())
    try:
        import torch  # pyright: ignore[reportMissingImports]

        if torch.cuda.is_available() and torch.cuda.is_initialized():
            result["torch_peak_allocated_mb"] = round(torch.cuda.max_memory_allocated() / (1 << 20))
    except ImportError:
        pass
    result["peak_vram_mb"] = sampler.stop()
    return result


def _switch(args, sampler: GpuSampler) -> dict:
    from app.models.request import TTSRequest
    from app.services.model_service import model_service
    from app.services.system_service import system_service
    from app.services.tts_service import tts_service

    system_service.initialize()
    system_service.update_settings(device=args.device, **(json.loads(args.settings) if args.settings else {}))
    steps = []
    for key in [k for k in args.switch.split(",") if k]:
        start = time.perf_counter()
        audio = tts_service.generate(TTSRequest(text=SHORT, model_key=key, seed=SEED))
        wall = time.perf_counter() - start
        loaded = [m["key"] for m in model_service.list_models() if m["loaded"]]
        steps.append({"model": key, "device": model_service.get(key)["loaded_device"], "wall_s": round(wall, 3),
                      "audio_s": round(audio["duration"], 2), "loaded_after": loaded})
    return {"engine": "switch", "steps": steps, "peak_vram_mb": sampler.stop(), "peak_rss_mb": round(peak_rss_mb())}


# ---------------------------------------------------------------- post-processing (no models)

def run_dsp(args) -> dict:
    """Each enhancement step, preset, loudness measurement and file write on speech-like audio."""
    import numpy as np

    from app.constants.audio import ENHANCE_PRESETS, PROCESS_STEPS
    from app.services.audio_service import audio_service
    from app.utils import audio as au

    sr = 24000
    results: dict = {}
    for seconds in args.dsp_seconds:
        rng = np.random.default_rng(0)
        t = np.arange(int(seconds * sr)) / sr
        voiced = sum(np.sin(2 * np.pi * 140 * k * t) / k for k in range(1, 6))
        syllables = 0.5 + 0.5 * np.sin(2 * np.pi * 4 * t)
        y = (0.2 * voiced * syllables + 0.01 * rng.standard_normal(t.size)).astype(np.float32)
        y[: sr // 2] = 0.002 * rng.standard_normal(sr // 2)  # leading near-silence for trim_silence

        def best(fn, repeat=3) -> float:
            times = []
            for _ in range(repeat):
                start = time.perf_counter()
                fn()
                times.append(time.perf_counter() - start)
            return round(min(times), 4)

        row: dict = {}
        for step in PROCESS_STEPS:
            row[f"step_{step}"] = best(lambda s=step: audio_service.process_array(y, sr, {s: {}}))
        for preset, steps in ENHANCE_PRESETS.items():
            if steps:
                row[f"preset_{preset}"] = best(lambda s=steps: audio_service.process_array(y, sr, s))
        row["loudness_lufs"] = best(lambda: au.loudness_lufs(y, sr))
        row["waveform_peaks_2000"] = best(lambda: au.waveform_peaks(y, 2000))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "out.wav"
            row["save_wav"] = best(lambda: au.save(path, y, sr, ai_generated=True))
            row["load_wav"] = best(lambda: au.load(path))
        results[f"{seconds}s"] = row
    return results


# ---------------------------------------------------------------- report

def markdown(report: dict) -> str:
    lines = [f"# VoxLabs benchmark: {report['label']}", "",
             f"{report['machine']['cpu']} · {report['machine'].get('gpu') or 'no GPU'} · "
             f"{report['machine']['platform']} · device={report['device']}", ""]
    if report.get("engines"):
        lines += ["| Engine | Device | Cold total (s) | Load (s) | Scenario | Wall (s) | Audio (s) | RTF | "
                  "Inference (s) | Post (s) | Save (s) | Register (s) | Other (s) | Peak VRAM (MB) |",
                  "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for engine in report["engines"]:
            if engine.get("skipped") or engine.get("error"):
                lines.append(f"| {engine['engine']} | – | – | – | {engine.get('skipped') or engine.get('error')} "
                             "| | | | | | | | | |")
                continue
            rows = [("first", engine["first_generate"]), *engine["scenarios"].items()]
            for index, (name, row) in enumerate(rows):
                head = (f"| {engine['engine']} | {engine['device']} | {engine['cold_total_s']} | {engine['load_s']} "
                        if index == 0 else "| | | | ")
                tail = f" {engine.get('peak_vram_mb') if index == 0 else ''} |"
                lines.append(head + f"| {name} | {row['wall_s']} | {row['audio_s']} | {row['rtf']} | "
                             f"{row.get('inference_s', '')} | {row.get('post_s', '')} | {row.get('save_s', '')} | "
                             f"{row.get('register_s', '')} | {row.get('other_s', '')} |" + tail)
    if report.get("switch"):
        lines += ["| Step | Model | Device | Wall (s) | Audio (s) | Loaded afterwards |", "|---|---|---|---|---|---|"]
        for index, step in enumerate(report["switch"].get("steps", []), 1):
            lines.append(f"| {index} | {step['model']} | {step['device']} | {step['wall_s']} | {step['audio_s']} | "
                         f"{', '.join(step['loaded_after'])} |")
        if report["switch"].get("error"):
            lines.append(f"| | {report['switch']['error']} | | | | |")
    if report.get("dsp"):
        lines += ["", "| Post-processing (s) | " + " | ".join(report["dsp"]) + " |",
                  "|---|" + "---|" * len(report["dsp"])]
        names = next(iter(report["dsp"].values()))
        for name in names:
            lines.append(f"| {name} | " + " | ".join(str(row[name]) for row in report["dsp"].values()) + " |")
    return "\n".join(lines) + "\n"


def machine() -> dict:
    info = {"platform": platform.platform(), "python": platform.python_version(),
            "cpu": platform.processor() or platform.machine(), "cores": os.cpu_count()}
    exe = shutil.which("nvidia-smi")
    if exe:
        try:
            out = subprocess.run([exe, "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
                                 capture_output=True, text=True, timeout=5)
            info["gpu"] = out.stdout.strip().splitlines()[0]
        except Exception:
            pass
    return info


def _child(args, engine: str) -> dict:
    """Run one engine (or the --switch sequence) in a fresh process and read its result file."""
    print(f"Benchmarking {engine} ...", file=sys.stderr, flush=True)
    with tempfile.TemporaryDirectory() as folder:
        out = Path(folder) / "result.json"
        command = [sys.executable, "-m", "scripts.benchmark", "--child", str(out), "--engine", engine,
                   "--device", args.device, "--scenarios", ",".join(args.scenarios),
                   "--repeat", str(args.repeat), "--source", args.source]
        if args.settings:
            command += ["--settings", args.settings]
        if args.switch:
            command += ["--switch", args.switch]
        subprocess.run(command, cwd=ROOT, check=False)
        return json.loads(out.read_text(encoding="utf-8")) if out.exists() else \
            {"engine": engine, "error": "the benchmark process crashed"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Benchmark VoxLabs speech generation on this computer.")
    parser.add_argument("--engines", default=",".join(ENGINES), help="comma-separated model keys")
    parser.add_argument("--scenarios", default=",".join(SCENARIOS), help="comma-separated: " + ", ".join(SCENARIOS))
    parser.add_argument("--device", default="auto", help="auto, cpu or cuda:N (the Settings device)")
    parser.add_argument("--settings", default="", help="extra settings as JSON, e.g. '{\"performance_preset\": \"fast\"}'")
    parser.add_argument("--repeat", type=int, default=3, help="runs of the short scenario")
    parser.add_argument("--source", default=None, help="data folder with the installed models (default: VoxLabs' own)")
    parser.add_argument("--label", default="run")
    parser.add_argument("--out", default=None, help="write the JSON report here (a .md summary goes next to it)")
    parser.add_argument("--dsp", action="store_true", help="benchmark post-processing only")
    parser.add_argument("--dsp-seconds", default="60,600", help="audio lengths for --dsp")
    parser.add_argument("--switch", default="", help="comma-separated models to use in turn in one process")
    parser.add_argument("--child", default=None, help=argparse.SUPPRESS)
    parser.add_argument("--engine", default=None, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    args.scenarios = [s for s in args.scenarios.split(",") if s]
    args.dsp_seconds = [int(s) for s in args.dsp_seconds.split(",") if s]
    if args.source is None:
        from app.utils.files import default_data_dir

        args.source = str(default_data_dir())

    if args.child:  # one engine, in its own process; the result goes to a file (engines print to stdout)
        try:
            result = run_engine(args)
        except Exception as exc:
            import traceback

            traceback.print_exc()
            result = {"engine": args.engine, "error": f"{type(exc).__name__}: {exc}"}
        Path(args.child).write_text(json.dumps(result, indent=2), encoding="utf-8")
        return 0

    report: dict = {"label": args.label, "device": args.device, "machine": machine(),
                    "date": time.strftime("%Y-%m-%d %H:%M:%S")}
    if args.dsp:
        report["dsp"] = run_dsp(args)
    elif args.switch:
        report["switch"] = _child(args, "switch")
    else:
        report["engines"] = [_child(args, engine) for engine in args.engines.split(",") if engine]
    summary = markdown(report)
    print(summary)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        out.with_suffix(".md").write_text(summary, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
