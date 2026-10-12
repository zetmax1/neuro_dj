"""
benchmarks/environment.py — what the timings depend on besides the code (D63).

A time in milliseconds means nothing without the machine it was measured on,
so the record carries the Postgres build and its two settings that change
write cost the most (``shared_buffers``, ``fsync``), the CPU and how much of
it was busy, the memory, the frequency governor — a laptop on
``powersave`` produces numbers that cannot be compared with anything — and
the five processes using the most CPU while the run started, which is how a
reader can tell whether something else was competing for the machine.

Everything here is read-only and fails soft: a missing sysfs file leaves a
``None`` in the record rather than ending a two-hour run.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
from pathlib import Path


def postgres(using: str) -> dict:
    """The server's version and the settings that matter for write cost."""
    from django.db import connections

    out: dict = {"vendor": connections[using].vendor}
    try:
        with connections[using].cursor() as cursor:
            for name, key in (
                ("server_version", "version"),
                ("shared_buffers", "shared_buffers"),
                ("fsync", "fsync"),
                ("synchronous_commit", "synchronous_commit"),
                ("max_connections", "max_connections"),
            ):
                cursor.execute(f"SHOW {name}")
                out[key] = cursor.fetchone()[0]
            cursor.execute("SELECT current_database()")
            out["database"] = cursor.fetchone()[0]
    except Exception as error:  # noqa: BLE001 - an unreachable server is reported, not raised
        out["error"] = f"{type(error).__name__}: {error}"
    return out


def _read(path: str) -> str | None:
    try:
        return Path(path).read_text(encoding="utf-8").strip()
    except OSError:
        return None


def cpu() -> dict:
    """Model, cores and the frequency governors in use."""
    model = None
    cores = 0
    info = _read("/proc/cpuinfo") or ""
    for line in info.splitlines():
        if line.startswith("model name") and model is None:
            model = line.split(":", 1)[1].strip()
        if line.startswith("processor"):
            cores += 1
    governors = sorted({
        value for value in (
            _read(str(path))
            for path in Path("/sys/devices/system/cpu").glob("cpu*/cpufreq/scaling_governor")
        ) if value
    })
    return {
        "model": model,
        "logical_cores": cores or os.cpu_count(),
        "governors": governors or None,
        "platform": platform.platform(),
    }


def memory() -> dict:
    out: dict = {}
    info = _read("/proc/meminfo") or ""
    for line in info.splitlines():
        for key, name in (("MemTotal:", "total_kb"), ("MemAvailable:", "available_kb")):
            if line.startswith(key):
                out[name] = int(line.split()[1])
    return out


def load() -> dict:
    values = (_read("/proc/loadavg") or "").split()
    if len(values) < 3:
        return {}
    return {"load_1m": float(values[0]), "load_5m": float(values[1]), "load_15m": float(values[2])}


def busiest(count: int = 5) -> list[dict]:
    """The processes using the most CPU right now — "was the machine quiet?"."""
    if not shutil.which("ps"):
        return []
    try:
        output = subprocess.run(
            ["ps", "-eo", "pcpu,comm", "--sort=-pcpu"],
            capture_output=True, text=True, timeout=10, check=True,
        ).stdout
    except (subprocess.SubprocessError, OSError):
        return []
    out: list[dict] = []
    for line in output.splitlines()[1:count + 1]:
        parts = line.split(None, 1)
        if len(parts) == 2:
            out.append({"cpu_percent": float(parts[0]), "command": parts[1].strip()})
    return out


def capture(using: str) -> dict:
    """Everything above, for the start of a run."""
    return {
        "postgres": postgres(using),
        "cpu": cpu(),
        "memory": memory(),
        "load": load(),
        "busiest_processes": busiest(),
        "note": (
            "vaqt o‘lchovlari mashinaga bog‘liq; nisbat (ρ) va uning oralig‘i "
            "mashinadan kam bog‘liq, shuning uchun da’vo ular ustiga qurilgan"
        ),
    }


def at_end() -> dict:
    """The facts that can change during a run."""
    return {"memory": memory(), "load": load(), "busiest_processes": busiest()}


__all__ = ["capture", "at_end", "postgres", "cpu", "memory", "load", "busiest"]
