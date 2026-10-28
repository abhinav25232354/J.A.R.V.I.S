"""Persistent Jarvis profile and preferences stored alongside conversation memory."""

import json
import os
from pathlib import Path

MEMORY_DIR = Path(__file__).resolve().parent / "memory"
PROFILE_PATH = MEMORY_DIR / "profile.json"
SETTINGS_PATH = MEMORY_DIR / "settings.json"
DEFAULT_SETTINGS = {
    "model": "llama3.2:1b",
    "voice": "en-US-ChristopherNeural",
    "speech_speed": 1.0,
}


def _read(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def _write(path: Path, value: dict) -> None:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def get_name() -> str | None:
    name = _read(PROFILE_PATH).get("name")
    return name.strip() if isinstance(name, str) and name.strip() else None


def set_name(name: str) -> None:
    _write(PROFILE_PATH, {"name": name.strip()})


def get_settings() -> dict:
    settings = {**DEFAULT_SETTINGS, **_read(SETTINGS_PATH)}
    try:
        settings["speech_speed"] = min(2.0, max(0.5, float(settings["speech_speed"])))
    except (TypeError, ValueError):
        settings["speech_speed"] = 1.0
    for key in ("model", "voice"):
        if not isinstance(settings.get(key), str) or not settings[key].strip():
            settings[key] = DEFAULT_SETTINGS[key]
    return settings


def save_settings(settings: dict) -> None:
    current = get_settings()
    current.update(settings)
    _write(SETTINGS_PATH, current)
