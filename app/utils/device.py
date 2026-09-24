"""Hardware inspection: CPU, CUDA GPUs and VRAM. Policy lives in ModelService."""

import os
import platform
import shutil
import subprocess
from functools import lru_cache


def torch_available() -> bool:
    try:
        import torch  # noqa: F401  # pyright: ignore[reportMissingImports]

        return True
    except Exception:
        return False


def _nvidia_smi() -> list[dict]:
    exe = shutil.which("nvidia-smi")
    if not exe:
        return []
    try:
        out = subprocess.run(
            [exe, "--query-gpu=name,memory.total,memory.free", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except Exception:
        return []
    gpus = []
    for index, line in enumerate(out.stdout.strip().splitlines()):
        parts = [p.strip() for p in line.split(",")]
        if len(parts) == 3:
            gpus.append(
                {"index": index, "name": parts[0], "vram_total_mb": int(parts[1]), "vram_free_mb": int(parts[2])}
            )
    return gpus


def gpus() -> list[dict]:
    if torch_available():
        import torch  # pyright: ignore[reportMissingImports]

        if torch.cuda.is_available():
            result = []
            for i in range(torch.cuda.device_count()):
                free, total = torch.cuda.mem_get_info(i)
                result.append(
                    {
                        "index": i,
                        "name": torch.cuda.get_device_name(i),
                        "vram_total_mb": total // (1 << 20),
                        "vram_free_mb": free // (1 << 20),
                    }
                )
            return result
    return _nvidia_smi()


def cuda_usable() -> bool:
    """CUDA can actually run models (needs torch built with CUDA)."""
    if not torch_available():
        return False
    import torch  # pyright: ignore[reportMissingImports]

    return bool(torch.cuda.is_available())


@lru_cache(maxsize=1)
def cpu_info() -> dict:
    return {"name": platform.processor() or platform.machine(), "cores": os.cpu_count() or 1}


def summary() -> dict:
    return {
        "cpu": cpu_info(),
        "gpus": gpus(),
        "cuda": cuda_usable(),
        "torch": torch_available(),
    }


def available_devices() -> list[str]:
    devices = ["cpu"]
    if cuda_usable():
        import torch  # pyright: ignore[reportMissingImports]

        devices += [f"cuda:{i}" for i in range(torch.cuda.device_count())]
    return devices
