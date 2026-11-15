"""Cross-platform hardware inspection. Runtime policy remains in ModelService."""

import importlib.util
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


def _run(command: list[str], timeout: int = 5) -> str:
    """Run a bounded, read-only system hardware query; unavailable tools return empty output."""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def _memory_mb(value: str) -> int | None:
    try:
        return int(value.strip().split()[0])
    except (AttributeError, IndexError, TypeError, ValueError):
        return None


def _nvidia_smi() -> list[dict]:
    exe = shutil.which("nvidia-smi")
    if not exe:
        return []
    output = _run(
        [exe, "--query-gpu=driver_version,name,memory.total,memory.free", "--format=csv,noheader,nounits"]
    )
    if not output:
        output = _run([exe, "--query-gpu=name,memory.total,memory.free", "--format=csv,noheader,nounits"])
    gpus = []
    for index, line in enumerate(output.splitlines()):
        parts = [part.strip() for part in line.split(",")]
        if len(parts) == 4:
            driver, name, total, free = parts
        elif len(parts) == 3:
            driver, (name, total, free) = None, parts
        else:
            continue
        total_mb, free_mb = _memory_mb(total), _memory_mb(free)
        item = {"index": index, "vendor": "NVIDIA", "name": name}
        if driver:
            item["driver_version"] = driver
        if total_mb is not None:
            item["vram_total_mb"] = total_mb
        if free_mb is not None:
            item["vram_free_mb"] = free_mb
        gpus.append(item)
    return gpus


def _other_gpus() -> list[dict]:
    """Best-effort GPU inventory for systems without nvidia-smi; VRAM may be unknown."""
    system = platform.system()
    output = ""
    if system == "Windows":
        output = _run([
            "powershell", "-NoProfile", "-NonInteractive", "-Command",
            "Get-CimInstance Win32_VideoController | Select-Object Name,AdapterRAM,DriverVersion | ConvertTo-Csv -NoTypeInformation",
        ])
        rows = output.splitlines()[1:]
        result = []
        for index, row in enumerate(rows):
            fields = [field.strip().strip('"') for field in row.split(",")]
            if not fields or not fields[0]:
                continue
            item = {"index": index, "name": fields[0], "vendor": _vendor(fields[0])}
            if len(fields) > 1:
                try:
                    item["vram_total_mb"] = int(fields[1]) // (1 << 20)
                except ValueError:
                    pass
            if len(fields) > 2 and fields[2]:
                item["driver_version"] = fields[2]
            result.append(item)
        return result
    if system == "Darwin":
        output = _run(["system_profiler", "SPDisplaysDataType", "-json"], timeout=10)
        if output:
            try:
                import json

                displays = json.loads(output).get("SPDisplaysDataType", [])
                result = []
                for index, display in enumerate(displays):
                    name = display.get("sppci_model") or display.get("_name")
                    if name:
                        item = {"index": index, "name": name, "vendor": _vendor(name)}
                        vram = display.get("spdisplays_vram")
                        if vram:
                            digits = "".join(ch for ch in str(vram) if ch.isdigit())
                            if digits:
                                item["vram_total_mb"] = int(digits)
                        result.append(item)
                return result
            except (ValueError, TypeError):
                return []
    if system == "Linux":
        output = _run(["lspci", "-mm"])
        result = []
        for line in output.splitlines():
            if "VGA compatible controller" not in line and "3D controller" not in line and "Display controller" not in line:
                continue
            fields = line.split('"')
            name = fields[3] if len(fields) > 3 else line
            result.append({"index": len(result), "name": name, "vendor": _vendor(name)})
        return result
    return []


def _vendor(name: str) -> str:
    value = name.lower()
    for needle, vendor in (("nvidia", "NVIDIA"), ("geforce", "NVIDIA"), ("amd", "AMD"),
                           ("radeon", "AMD"), ("intel", "Intel"), ("apple", "Apple")):
        if needle in value:
            return vendor
    return "Unknown"


@lru_cache(maxsize=1)
def nvidia_gpu_present() -> bool:
    """An NVIDIA driver is installed (nvidia-smi answers), whether or not PyTorch can use it."""
    return bool(_nvidia_smi())


def gpus() -> list[dict]:
    """Return detected display/inference GPUs; never import a framework just to enumerate devices."""
    torch = sys.modules.get("torch")
    smi = _nvidia_smi()
    driver_version = smi[0].get("driver_version") if smi else None
    if torch is not None and torch.cuda.is_available():
        result = []
        for index in range(torch.cuda.device_count()):
            free, total = torch.cuda.mem_get_info(index)
            item = {
                "index": index,
                "vendor": "NVIDIA",
                "name": torch.cuda.get_device_name(index),
                "vram_total_mb": total // (1 << 20),
                "vram_free_mb": free // (1 << 20),
            }
            if driver_version:
                item["driver_version"] = driver_version
            result.append(item)
        return result
    return smi or _other_gpus()


def cuda_usable() -> bool:
    """CUDA can actually run models (needs torch built with CUDA)."""
    if not torch_available():
        return False
    import torch  # pyright: ignore[reportMissingImports]

    return bool(torch.cuda.is_available())


def cuda_fallback_reason() -> str | None:
    """Detect if CPU fallback is active and explain why."""
    if cuda_usable():
        return None
    if not nvidia_gpu_present():
        return "No NVIDIA GPU hardware detected; operating in CPU mode."
    if not torch_available():
        return "PyTorch is not installed in the environment; operating in CPU mode."
    import torch  # pyright: ignore[reportMissingImports]

    if not torch.cuda.is_available():
        version = getattr(torch, "__version__", "unknown")
        return f"NVIDIA GPU detected, but current PyTorch build ({version}) does not include CUDA acceleration."
    return "CUDA initialization failed; operating in CPU fallback mode."


def _physical_cpu_count() -> int | None:
    system = platform.system()
    if system == "Darwin":
        value = _run(["sysctl", "-n", "hw.physicalcpu"])
        try:
            return max(1, int(value))
        except ValueError:
            return None
    if system == "Linux":
        try:
            cores = set()
            physical_id = "0"
            core_id = None
            for line in open("/proc/cpuinfo", encoding="utf-8", errors="replace"):
                if not line.strip():
                    if core_id is not None:
                        cores.add((physical_id, core_id))
                    physical_id, core_id = "0", None
                elif ":" in line:
                    key, value = (part.strip() for part in line.split(":", 1))
                    if key == "physical id":
                        physical_id = value
                    elif key == "core id":
                        core_id = value
            if core_id is not None:
                cores.add((physical_id, core_id))
            return len(cores) or None
        except OSError:
            return None
    return None


@lru_cache(maxsize=1)
def cpu_info() -> dict:
    return {
        "name": platform.processor() or platform.machine() or "Unknown",
        "architecture": platform.machine() or "Unknown",
        "logical_cores": os.cpu_count() or 1,
        "physical_cores": _physical_cpu_count(),
    }


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
            if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                return {"total": 0, "available": 0}
            return {"total": status.ullTotalPhys >> 20, "available": status.ullAvailPhys >> 20}
        page = os.sysconf("SC_PAGE_SIZE")
        total = os.sysconf("SC_PHYS_PAGES") * page
        available = os.sysconf("SC_AVPHYS_PAGES") * page if "SC_AVPHYS_PAGES" in os.sysconf_names else 0
        return {"total": total >> 20, "available": available >> 20}
    except (AttributeError, OSError, ValueError):
        return {"total": 0, "available": 0}


def runtime_info() -> dict:
    """Report installed inference runtimes without importing optional ML packages."""
    packages = {
        "pytorch": "torch",
        "onnx_runtime": "onnxruntime",
        "onnx_runtime_directml": "onnxruntime_directml",
        "tensorflow": "tensorflow",
        "coreml": "coremltools",
    }
    installed = {}
    for label, package in packages.items():
        try:
            installed[label] = importlib.util.find_spec(package) is not None
        except (ImportError, ValueError, ModuleNotFoundError):
            installed[label] = False
    providers = ["CPUExecutionProvider"] if installed["onnx_runtime"] else []
    if installed["onnx_runtime"]:
        providers += ["CUDAExecutionProvider"] if cuda_usable() else []
    if installed["onnx_runtime_directml"]:
        providers.append("DmlExecutionProvider")
    if installed["coreml"]:
        providers.append("CoreMLExecutionProvider")
    return {"installed": installed, "onnx_providers_detected": providers}


def recommended_preset(gpu_list: list[dict] | None = None, cuda: bool | None = None, ram: dict | None = None) -> str:
    """Recommend a conservative preset from available memory and known accelerator resources."""
    gpu_list = gpus() if gpu_list is None else gpu_list
    cuda = cuda_usable() if cuda is None else cuda
    ram = ram_mb() if ram is None else ram
    vram = max((g.get("vram_total_mb", 0) or 0 for g in gpu_list), default=0) if cuda else 0
    if (ram["total"] and ram["total"] < 8192) or (cuda and vram and vram < 4096):
        return "low_memory"
    return "balanced"


def summary() -> dict:
    gpu_list, cuda, ram = gpus(), cuda_usable(), ram_mb()
    torch_mod = sys.modules.get("torch")
    torch_ver = getattr(torch_mod, "__version__", None) if torch_mod else None
    cuda_ver = getattr(getattr(torch_mod, "version", None), "cuda", None) if torch_mod else None
    driver_ver = gpu_list[0].get("driver_version") if gpu_list else None
    return {
        "os": platform.system(),
        "platform": platform.platform(),
        "cpu": cpu_info(),
        "ram_mb": ram,
        "gpus": gpu_list,
        "cuda": cuda,
        "torch": torch_available(),
        "torch_version": torch_ver,
        "cuda_version": cuda_ver,
        "driver_version": driver_ver,
        "runtimes": runtime_info(),
        "fallback_reason": cuda_fallback_reason(),
        "recommended_preset": recommended_preset(gpu_list, cuda, ram),
    }


def available_devices() -> list[str]:
    devices = ["cpu"]
    if cuda_usable():
        import torch  # pyright: ignore[reportMissingImports]

        devices += [f"cuda:{i}" for i in range(torch.cuda.device_count())]
    return devices
