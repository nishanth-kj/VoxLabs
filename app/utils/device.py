"""Hardware inspection: CPU, CUDA GPUs and VRAM. Policy lives in ModelService."""

import os
import platform
import shutil
import subprocess
import sys
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


@lru_cache(maxsize=1)
def nvidia_gpu_present() -> bool:
    """An NVIDIA driver is installed (nvidia-smi answers), whether or not this Python's torch can use it."""
    return bool(_nvidia_smi())


def gpus() -> list[dict]:
    """NVIDIA GPUs with total and free VRAM. Asks PyTorch when it is already loaded (and sees CUDA), else
    nvidia-smi: importing torch takes seconds, and engines in their own process never need it here."""
    torch = sys.modules.get("torch")
    if torch is not None:
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


def ram_mb() -> dict:
    """Total and available system memory in MB (zeros when the platform does not say)."""
    try:
        if os.name == "nt":
            import ctypes

            class MemoryStatus(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]

            status = MemoryStatus()
            status.dwLength = ctypes.sizeof(MemoryStatus)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
            return {"total": status.ullTotalPhys >> 20, "available": status.ullAvailPhys >> 20}
        page = os.sysconf("SC_PAGE_SIZE")
        total = os.sysconf("SC_PHYS_PAGES") * page
        available = os.sysconf("SC_AVPHYS_PAGES") * page if "SC_AVPHYS_PAGES" in os.sysconf_names else 0
        return {"total": total >> 20, "available": available >> 20}
    except (AttributeError, OSError, ValueError):
        return {"total": 0, "available": 0}


def recommended_preset(gpu_list: list[dict] | None = None, cuda: bool | None = None, ram: dict | None = None) -> str:
    """A performance preset for this hardware: Low Memory on small machines, Balanced otherwise."""
    gpu_list = gpus() if gpu_list is None else gpu_list
    cuda = cuda_usable() if cuda is None else cuda
    ram = ram_mb() if ram is None else ram
    vram = max((g["vram_total_mb"] for g in gpu_list), default=0) if cuda else 0
    if (ram["total"] and ram["total"] < 8192) or (cuda and vram < 4096):
        return "low_memory"
    return "balanced"


def summary() -> dict:
    gpu_list, cuda, ram = gpus(), cuda_usable(), ram_mb()
    return {
        "cpu": cpu_info(),
        "ram_mb": ram,
        "gpus": gpu_list,
        "cuda": cuda,
        "torch": torch_available(),
        "recommended_preset": recommended_preset(gpu_list, cuda, ram),
    }


def available_devices() -> list[str]:
    devices = ["cpu"]
    if cuda_usable():
        import torch  # pyright: ignore[reportMissingImports]

        devices += [f"cuda:{i}" for i in range(torch.cuda.device_count())]
    return devices
