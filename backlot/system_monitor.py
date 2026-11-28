"""Local, dependency-free hardware readings for the Studio status strip.

Only built-in Windows APIs and an already installed NVIDIA CLI are queried.
Missing or ambiguous sensors are returned as None; no values are fabricated.
"""
from __future__ import annotations

import csv
import ctypes
import io
import os
import shutil
import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path

_cpu_lock = threading.Lock()
_last_cpu: tuple[int, int] | None = None


def _filetime_value(value: ctypes.Structure) -> int:
    return (int(value.dwHighDateTime) << 32) | int(value.dwLowDateTime)


def _cpu_usage_percent() -> float | None:
    """Return busy CPU time from GetSystemTimes; first sample is unavailable."""
    global _last_cpu
    if os.name != "nt":
        return _proc_cpu_usage_percent()
    class FILETIME(ctypes.Structure):
        _fields_ = [("dwLowDateTime", ctypes.c_uint32), ("dwHighDateTime", ctypes.c_uint32)]

    idle, kernel, user = FILETIME(), FILETIME(), FILETIME()
    try:
        get_times = ctypes.WinDLL("kernel32", use_last_error=True).GetSystemTimes
        get_times.argtypes = [ctypes.POINTER(FILETIME)] * 3
        get_times.restype = ctypes.c_int
        if not get_times(ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)):
            return None
        current = (_filetime_value(kernel) + _filetime_value(user), _filetime_value(idle))
    except (AttributeError, OSError):
        return None
    with _cpu_lock:
        previous, _last_cpu = _last_cpu, current
    if previous is None:
        return None
    total_delta = current[0] - previous[0]
    idle_delta = current[1] - previous[1]
    if total_delta <= 0 or idle_delta < 0:
        return None
    busy = max(0, total_delta - idle_delta)
    return round(min(100.0, 100.0 * busy / total_delta), 1)


def _proc_cpu_usage_percent() -> float | None:
    """Portable fallback for Linux test/development hosts."""
    try:
        values = Path("/proc/stat").read_text(encoding="ascii").splitlines()[0].split()[1:]
        numbers = [int(value) for value in values]
        idle = numbers[3] + (numbers[4] if len(numbers) > 4 else 0)
        total = sum(numbers)
        global _last_cpu
        with _cpu_lock:
            previous, _last_cpu = _last_cpu, (total, idle)
        if previous is None or total <= previous[0] or idle < previous[1]:
            return None
        return round(min(100.0, 100.0 * (total - previous[0] - idle + previous[1]) / (total - previous[0])), 1)
    except (OSError, IndexError, ValueError):
        return None


def _memory() -> dict[str, int | float | None]:
    if os.name == "nt":
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_uint32), ("dwMemoryLoad", ctypes.c_uint32),
                ("ullTotalPhys", ctypes.c_uint64), ("ullAvailPhys", ctypes.c_uint64),
                ("ullTotalPageFile", ctypes.c_uint64), ("ullAvailPageFile", ctypes.c_uint64),
                ("ullTotalVirtual", ctypes.c_uint64), ("ullAvailVirtual", ctypes.c_uint64),
                ("ullAvailExtendedVirtual", ctypes.c_uint64),
            ]
        status = MEMORYSTATUSEX()
        status.dwLength = ctypes.sizeof(status)
        try:
            fn = ctypes.WinDLL("kernel32", use_last_error=True).GlobalMemoryStatusEx
            fn.argtypes = [ctypes.POINTER(MEMORYSTATUSEX)]
            fn.restype = ctypes.c_int
            if not fn(ctypes.byref(status)) or not status.ullTotalPhys:
                return {"usage_percent": None, "used_bytes": None, "total_bytes": None}
            return {
                "usage_percent": int(status.dwMemoryLoad),
                "used_bytes": int(status.ullTotalPhys - status.ullAvailPhys),
                "total_bytes": int(status.ullTotalPhys),
            }
        except (AttributeError, OSError):
            return {"usage_percent": None, "used_bytes": None, "total_bytes": None}
    try:
        pages = os.sysconf("SC_PHYS_PAGES")
        available = os.sysconf("SC_AVPHYS_PAGES")
        page_size = os.sysconf("SC_PAGE_SIZE")
        total, free = pages * page_size, available * page_size
        return {"usage_percent": round((total-free) * 100 / total, 1), "used_bytes": total-free, "total_bytes": total}
    except (AttributeError, OSError, ValueError, ZeroDivisionError):
        return {"usage_percent": None, "used_bytes": None, "total_bytes": None}


def _fixed_disks() -> list[dict[str, int | float | str]]:
    roots: list[str] = []
    if os.name == "nt":
        try:
            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel.GetLogicalDrives.restype = ctypes.c_uint32
            kernel.GetDriveTypeW.argtypes = [ctypes.c_wchar_p]
            kernel.GetDriveTypeW.restype = ctypes.c_uint32
            mask = kernel.GetLogicalDrives()
            roots = [f"{chr(65+i)}:\\" for i in range(26) if mask & (1 << i) and kernel.GetDriveTypeW(f"{chr(65+i)}:\\") == 3]
        except (AttributeError, OSError):
            roots = []
    else:
        roots = ["/"]
    disks = []
    for root in roots:
        try:
            usage = shutil.disk_usage(root)
            if usage.total <= 0:
                continue
            disks.append({
                "name": root.rstrip("\\/") or root,
                "usage_percent": round(usage.used * 100 / usage.total, 1),
                "used_bytes": int(usage.used),
                "total_bytes": int(usage.total),
                "free_bytes": int(usage.free),
            })
        except OSError:
            continue
    return disks


def _gpu_devices() -> list[dict[str, int | float | str | None]]:
    """Read NVIDIA devices from nvidia-smi only when already installed."""
    executable = shutil.which("nvidia-smi")
    if not executable and os.name == "nt":
        candidate = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "nvidia-smi.exe"
        if candidate.is_file():
            executable = str(candidate)
    if not executable:
        return []
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        result = subprocess.run(
            [executable, "--query-gpu=name,utilization.gpu,temperature.gpu,memory.used,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1.5,
            check=False, creationflags=flags,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if result.returncode != 0:
        return []
    devices = []
    for row in csv.reader(io.StringIO(result.stdout)):
        if len(row) != 5:
            continue
        name, usage, temperature, used_memory, total_memory = (item.strip() for item in row)
        try:
            gpu_usage = float(usage)
            if not 0 <= gpu_usage <= 100:
                gpu_usage = None
        except ValueError:
            gpu_usage = None
        try:
            gpu_temperature = float(temperature)
            if not 0 <= gpu_temperature <= 150:
                gpu_temperature = None
        except ValueError:
            gpu_temperature = None
        try:
            used_mb, total_mb = int(used_memory), int(total_memory)
            if total_mb <= 0 or used_mb < 0 or used_mb > total_mb:
                used_mb = total_mb = None
        except ValueError:
            used_mb = total_mb = None
        devices.append({
            "name": name or "GPU NVIDIA",
            "usage_percent": round(gpu_usage, 1) if gpu_usage is not None else None,
            "temperature_c": round(gpu_temperature, 1) if gpu_temperature is not None else None,
            "memory_used_mb": used_mb,
            "memory_total_mb": total_mb,
        })
    return devices


def _cpu_temperature_c() -> float | None:
    """No generic ACPI thermal zone is treated as a CPU sensor."""
    # Windows' generic ACPI zone does not identify which component it measures.
    # A supported per-CPU sensor provider can be added without guessing here.
    return None


def snapshot() -> dict:
    """Return a local, best-effort sample; unavailable readings are null."""
    memory = _memory()
    return {
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "source": "local operating-system APIs and installed NVIDIA driver CLI",
        "cpu": {"usage_percent": _cpu_usage_percent(), "temperature_c": _cpu_temperature_c()},
        "gpus": _gpu_devices(),
        "memory": memory,
        "disks": _fixed_disks(),
    }
