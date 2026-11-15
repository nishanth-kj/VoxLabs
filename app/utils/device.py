"""Cross-platform hardware inspection. Runtime policy remains in ModelService."""

import importlib.metadata
import importlib.util
import json
import re
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
            "Get-CimInstance Win32_VideoController | Select-Object Name,AdapterRAM,DriverVersion | ConvertTo-Json -Compress",
        ])
        try:
            rows = json.loads(output) if output else []
            rows = rows if isinstance(rows, list) else [rows]
        except ValueError:
            return []
        result = []
        for index, row in enumerate(rows):
            name = row.get("Name")
            if not name:
                continue
            item = {"index": index, "name": name, "vendor": _vendor(name)}
            try:
                # Win32_VideoController.AdapterRAM is a 32-bit field; max/overflow values are not trustworthy.
                memory = int(row.get("AdapterRAM") or 0)
                if 0 < memory < 0xFFFFFFFF:
                    item["vram_total_mb"] = memory // (1 << 20)
            except (TypeError, ValueError):
                pass
            if row.get("DriverVersion"):
                item["driver_version"] = row["DriverVersion"]
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
                            item["vram_total_mb"] = _parse_vram_mb(str(vram))
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
            vendor = fields[3] if len(fields) > 3 else "Unknown"
            model = fields[5] if len(fields) > 5 else ""
            name = f"{vendor} {model}".strip()
            result.append({"index": len(result), "name": name, "vendor": _vendor(vendor)})
        return result
    return []


def _parse_vram_mb(value: str) -> int | None:
    match = re.search(r"(\d+(?:\.\d+)?)\s*(TB|GB|MB)", value, re.IGNORECASE)
    if not match:
        return None
    amount, unit = float(match.group(1)), match.group(2).upper()
    multiplier = {"TB": 1024 * 1024, "GB": 1024, "MB": 1}[unit]
    return int(amount * multiplier)


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
    detected = smi or _other_gpus()
    # Keep a stable GPU schema for UI consumers when a device does not expose VRAM telemetry.
    for gpu in detected:
        gpu.setdefault("vram_total_mb", None)
        gpu.setdefault("vram_free_mb", None)
    return detected


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
        other_gpus = _other_gpus()
        if other_gpus:
            return "No NVIDIA CUDA-capable GPU detected; non-CUDA graphics hardware is present."
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
    if system == "Windows":
        value = _run([
            "powershell", "-NoProfile", "-NonInteractive", "-Command",
            "(Get-CimInstance Win32_Processor | Measure-Object -Property NumberOfCores -Sum).Sum",
        ])
        try:
            return max(1, int(value))
        except ValueError:
            return None
    if system == "Linux":
        try:
            cores = set()
            physical_id = "0"
            core_id = None
            with open("/proc/cpuinfo", encoding="utf-8", errors="replace") as cpuinfo:
                for line in cpuinfo:
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


def _cpu_model() -> str:
    system = platform.system()
    if system == "Windows":
        value = _run([
            "powershell", "-NoProfile", "-NonInteractive", "-Command",
            "(Get-CimInstance Win32_Processor | Select-Object -First 1 -ExpandProperty Name)",
        ])
        if value:
            return value
    elif system == "Darwin":
        value = _run(["sysctl", "-n", "machdep.cpu.brand_string"])
        if value:
            return value
    elif system == "Linux":
        try:
            with open("/proc/cpuinfo", encoding="utf-8", errors="replace") as cpuinfo:
                for line in cpuinfo:
                    if line.startswith(("model name", "Hardware", "Processor")) and ":" in line:
                        value = line.split(":", 1)[1].strip()
                        if value:
                            return value
        except OSError:
            pass
    return platform.processor() or platform.machine() or "Unknown"


@lru_cache(maxsize=1)
def cpu_info() -> dict:
    return {
        "name": _cpu_model(),
        "architecture": platform.machine() or "Unknown",
        "cores": os.cpu_count() or 1,  # Backward-compatible key used by ModelsPage.
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
    try:
        importlib.metadata.distribution("onnxruntime-directml")
        installed["onnx_runtime_directml"] = True
    except importlib.metadata.PackageNotFoundError:
        pass
    onnxruntime = sys.modules.get("onnxruntime")
    providers = onnxruntime.get_available_providers() if onnxruntime is not None else []
    return {"installed": installed, "onnx_providers_detected": providers}


def recommended_preset(gpu_list: list[dict] | None = None, cuda: bool | None = None, ram: dict | None = None) -> str:
    """Return the selectable performance profile recommended for the detected hardware."""
    return recommended_profile(gpu_list, ram, cpu_info())


def recommended_profile(gpu_list: list[dict] | None = None, ram: dict | None = None,
                        cpu: dict | None = None) -> str:
    """Recommend a conservative resource tier; unknown telemetry never counts as a capability."""
    gpu_list = gpus() if gpu_list is None else gpu_list
    ram = ram_mb() if ram is None else ram
    cpu = cpu_info() if cpu is None else cpu
    total_ram, available_ram = ram.get("total", 0), ram.get("available", 0)
    known_vram = [gpu for gpu in gpu_list if gpu.get("vram_total_mb") is not None]
    if (total_ram and total_ram < 4096) or (available_ram and available_ram < 1024):
        return "ultra_low"
    if (total_ram and total_ram < 8192) or (available_ram and available_ram < 2048):
        return "low"
    if known_vram and max(gpu["vram_total_mb"] for gpu in known_vram) < 4096:
        return "low"
    known_free_vram = [gpu["vram_free_mb"] for gpu in known_vram if gpu.get("vram_free_mb") is not None]
    if known_free_vram and max(known_free_vram) < 1024:
        return "low"
    if (total_ram >= 16384 and available_ram >= 8192 and cpu.get("logical_cores", 0) >= 8
            and known_vram and max(gpu["vram_total_mb"] for gpu in known_vram) >= 8192
            and (not known_free_vram or max(known_free_vram) >= 4096)):
        return "performance"
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
        "recommended_profile": recommended_profile(gpu_list, ram, cpu_info()),
    }


def available_devices() -> list[str]:
    devices = ["cpu"]
    if cuda_usable():
        import torch  # pyright: ignore[reportMissingImports]

        devices += [f"cuda:{i}" for i in range(torch.cuda.device_count())]
    return devices
