"""JSON persistence for assistant question and answer history."""

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MEMORY_DIR = Path(__file__).resolve().parent


def save_exchange(
    *,
    question: str,
    answer: str | None,
    asked_at: str,
    model: str,
    voice: str = "en-US-ChristopherNeural",
    duration_seconds: float,
    speech_status: str,
    status: str,
    error: str | None = None,
) -> Path:
    """Save one complete exchange as its own readable JSON record."""
    record: dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "asked_at": asked_at,
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "question": question,
        "answer": answer,
        "provider": "ollama",
        "model": model,
        "duration_seconds": duration_seconds,
        "speech": {"voice": voice, "status": speech_status},
        "status": status,
    }
    if error:
        record["error"] = error

    timestamp = re.sub(r"[^0-9TZ]", "-", asked_at)
    destination = MEMORY_DIR / f"{timestamp}_{record['id']}.json"
    destination.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return destination
