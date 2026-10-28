"""Non-blocking startup checks for internet and computer health."""

import platform
from pathlib import Path
import subprocess
import urllib.error
import urllib.request


def check_internet(timeout: float = 3.0) -> dict:
    """Check internet reachability; this result never gates startup."""
    request = urllib.request.Request(
        "https://www.microsoft.com/", method="HEAD", headers={"User-Agent": "Jarvis health check"}
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return {"available": response.status < 500, "detail": f"HTTP {response.status}"}
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {"available": False, "detail": str(exc)}


def _temperature() -> dict:
    """Read a thermal-zone temperature when the machine exposes one."""
    try:
        import psutil

        sensors = psutil.sensors_temperatures()
        readings = [
            (sensor.label or name, item.current)
            for name, entries in sensors.items()
            for item in entries
            if item.current is not None
        ]
        if readings:
            return {"available": True, "readings": readings}
    except Exception:
        pass

    if platform.system() == "Windows":
        script = (
            "$ErrorActionPreference='Stop'; "
            "Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature "
            "| Select-Object -ExpandProperty CurrentTemperature"
        )
        try:
            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
                capture_output=True,
                text=True,
                timeout=4,
                check=False,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            values = [float(line.strip()) for line in result.stdout.splitlines() if line.strip().isdigit()]
            celsius = [round(value / 10 - 273.15, 1) for value in values]
            if result.returncode == 0 and celsius:
                return {"available": True, "readings": [("ACPI thermal zone", value) for value in celsius]}
        except (OSError, subprocess.TimeoutExpired, ValueError):
            pass
    return {"available": False, "readings": []}


def check_device() -> dict:
    """Collect CPU, memory, disk, and temperature metrics where available."""
    try:
        import psutil
    except ImportError:
        return {"available": False, "detail": "Install psutil to read device metrics."}

    memory = psutil.virtual_memory()
    disk_path = Path.home().anchor or "/"
    disk = psutil.disk_usage(disk_path)
    return {
        "available": True,
        "cpu_percent": psutil.cpu_percent(interval=0.5),
        "cpu_count": psutil.cpu_count(logical=True),
        "ram_percent": memory.percent,
        "ram_used_gb": round(memory.used / (1024 ** 3), 2),
        "ram_total_gb": round(memory.total / (1024 ** 3), 2),
        "disk_percent": disk.percent,
        "temperature": _temperature(),
    }


def run_startup_checks() -> dict:
    """Run and print diagnostics; never prevent the assistant from starting."""
    from offline import OLLAMA_MODEL, check_ollama
    from speechdrive import check_edge_voice, speech_capabilities

    print("Startup checks (informational):")
    try:
        internet = check_internet()
    except Exception as exc:
        internet = {"available": False, "detail": str(exc)}
    print(f"  Internet: {'available' if internet['available'] else 'unavailable'} ({internet['detail']})")

    try:
        ollama = check_ollama()
    except Exception as exc:
        ollama = {"available": False, "detail": str(exc), "models": []}
    if not ollama["available"]:
        print("  Ollama: not found on Windows or WSL; questions will fail until it is available.")
    else:
        location = ollama["location"]
        print(f"  Ollama: found in {location} at {ollama['url']}")
        if ollama["model_available"]:
            print(f"  Model: {OLLAMA_MODEL} is available")
        else:
            installed = ", ".join(ollama["models"]) or "none"
            print(f"  Model: {OLLAMA_MODEL} is missing; installed models: {installed}")

    try:
        device = check_device()
    except Exception as exc:
        device = {"available": False, "detail": str(exc)}
    if not device["available"]:
        print(f"  Device metrics: unavailable ({device['detail']})")
    else:
        print(
            f"  CPU: {device['cpu_percent']}% across {device['cpu_count']} logical cores | "
            f"RAM: {device['ram_percent']}% ({device['ram_used_gb']}/{device['ram_total_gb']} GB) | "
            f"Disk: {device['disk_percent']}% used"
        )
        temperature = device["temperature"]
        if temperature["available"]:
            values = ", ".join(f"{name}: {value} C" for name, value in temperature["readings"])
            print(f"  Temperature: {values}")
        else:
            print("  Temperature: unavailable (this device does not expose a readable sensor)")

    try:
        memory_dir = Path(__file__).resolve().parent / "memory"
        memory_dir.mkdir(parents=True, exist_ok=True)
        probe = memory_dir / ".startup-check"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        memory_ready = True
    except Exception:
        memory_ready = False
    print(f"  JSON memory: {'ready' if memory_ready else 'unavailable; exchanges will continue without saving'}")

    try:
        speech = speech_capabilities()
        edge_voice = check_edge_voice()
        modules = speech["modules"]
        commands = speech["commands"]
        playback = [
            modules["pygame"],
            modules["playsound"],
            platform.system() == "Windows",
            commands["ffplay"],
            platform.system() == "Windows" and commands["ffmpeg"],
        ]
        ready_count = sum(bool(item) for item in playback)
        edge_status = (
            "Edge Christopher online"
            if edge_voice["available"]
            else f"Edge Christopher unavailable ({edge_voice.get('detail', 'service check failed')}); Windows SAPI will be used"
        )
        print(f"  Speech: {edge_status}; {ready_count}/5 playback methods available")
    except Exception:
        print("  Speech: capability check unavailable; text answers will still work")
    print()
    return {
        "internet": internet,
        "ollama": ollama,
        "device": device,
        "memory_ready": memory_ready,
        "edge_voice": edge_voice if "edge_voice" in locals() else {"available": False},
    }
