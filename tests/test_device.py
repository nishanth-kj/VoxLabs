"""Hardware detection must degrade gracefully across machines and optional runtimes."""

import sys

from app.utils import device


def test_cpu_info_reports_architecture_and_core_counts(monkeypatch):
    device.cpu_info.cache_clear()
    monkeypatch.setattr(device.platform, "processor", lambda: "Test CPU")
    monkeypatch.setattr(device.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(device.os, "cpu_count", lambda: 8)
    monkeypatch.setattr(device, "_physical_cpu_count", lambda: 4)

    result = device.cpu_info()

    assert result == {
        "name": "Test CPU",
        "architecture": "x86_64",
        "logical_cores": 8,
        "physical_cores": 4,
    }
    device.cpu_info.cache_clear()


def test_gpu_inventory_falls_back_when_nvidia_gpu_is_missing(monkeypatch):
    monkeypatch.setattr(device, "_nvidia_smi", lambda: [])
    monkeypatch.setattr(device, "_other_gpus", lambda: [])

    assert device.gpus() == []


def test_gpu_inventory_supports_non_nvidia_devices_without_vram(monkeypatch):
    gpu = {"index": 0, "vendor": "Apple", "name": "Apple M-series GPU"}
    monkeypatch.setattr(device, "_nvidia_smi", lambda: [])
    monkeypatch.setattr(device, "_other_gpus", lambda: [gpu])

    assert device.gpus() == [gpu]
    assert device.recommended_preset([gpu], False, {"total": 16384, "available": 8000}) == "balanced"


def test_recommendation_uses_low_memory_when_system_ram_is_limited():
    assert device.recommended_preset([], False, {"total": 4096, "available": 900}) == "low_memory"


def test_recommendation_uses_low_memory_for_known_small_cuda_memory():
    gpu = [{"index": 0, "name": "GPU", "vram_total_mb": 2048, "vram_free_mb": 1800}]
    assert device.recommended_preset(gpu, True, {"total": 16384, "available": 8000}) == "low_memory"


def test_runtime_detection_does_not_import_optional_frameworks(monkeypatch):
    imported = []

    def find_spec(name):
        imported.append(name)
        return None

    monkeypatch.setattr(device.importlib.util, "find_spec", find_spec)
    torch_was_loaded = "torch" in sys.modules
    result = device.runtime_info()

    assert all(value is False for value in result["installed"].values())
    assert result["onnx_providers_detected"] == []
    assert ("torch" in sys.modules) == torch_was_loaded
    assert imported == ["torch", "onnxruntime", "onnxruntime_directml", "tensorflow", "coremltools"]



def test_profile_is_ultra_low_when_available_ram_is_critically_low():
    assert device.recommended_profile(
        [], {"total": 16384, "available": 700}, {"logical_cores": 8}
    ) == "ultra_low"


def test_profile_is_low_when_gpu_vram_is_limited():
    gpu = [{"index": 0, "name": "GPU", "vram_total_mb": 2048, "vram_free_mb": 1800}]
    assert device.recommended_profile(
        gpu, {"total": 16384, "available": 8000}, {"logical_cores": 8}
    ) == "low"


def test_profile_does_not_assume_unknown_vram_is_large():
    gpu = [{"index": 0, "name": "Integrated GPU"}]
    assert device.recommended_profile(
        gpu, {"total": 16384, "available": 8000}, {"logical_cores": 8}
    ) == "balanced"


def test_profile_recommends_performance_only_with_headroom():
    gpu = [{"index": 0, "name": "GPU", "vram_total_mb": 12288, "vram_free_mb": 8192}]
    assert device.recommended_profile(
        gpu, {"total": 32768, "available": 20000}, {"logical_cores": 16}
    ) == "performance"



def test_vram_parser_converts_units_without_treating_gigabytes_as_megabytes():
    assert device._parse_vram_mb("8 GB") == 8192
    assert device._parse_vram_mb("1536 MB") == 1536
    assert device._parse_vram_mb("unknown") is None



def test_windows_physical_core_detection_uses_system_metadata(monkeypatch):
    monkeypatch.setattr(device.platform, "system", lambda: "Windows")
    monkeypatch.setattr(device, "_run", lambda command, timeout=5: "6")

    assert device._physical_cpu_count() == 6
