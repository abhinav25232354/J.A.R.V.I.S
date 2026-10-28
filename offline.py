"""Discover and query an Ollama server on Windows or inside WSL."""

import json
import os
import subprocess
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from user_settings import get_settings


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
_active_url: str | None = None


def _get(url: str, path: str, timeout: float = 2.0) -> dict:
    request = Request(f"{url.rstrip('/')}{path}", headers={"Accept": "application/json"})
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _wsl_urls() -> list[str]:
    """Get WSL virtual addresses, if WSL is installed and running."""
    command = "wsl.exe"
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        result = subprocess.run(
            [command, "--", "hostname", "-I"],
            capture_output=True,
            text=True,
            timeout=4,
            check=False,
            creationflags=creationflags,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if result.returncode != 0:
        return []
    urls = []
    for address in result.stdout.split():
        # WSL commonly returns one or more IPv4 addresses; bracket IPv6 literals.
        host = f"[{address}]" if ":" in address else address
        urls.append(f"http://{host}:11434")
    return urls


def _model_names(payload: dict) -> set[str]:
    return {
        str(item.get("name", ""))
        for item in payload.get("models", [])
        if isinstance(item, dict)
    }


def configured_model() -> str:
    """Resolve the persisted model, while allowing an environment override."""
    return os.getenv("OLLAMA_MODEL", get_settings()["model"])


def check_ollama() -> dict:
    """Find a reachable Ollama server, preferring Windows before WSL."""
    global _active_url
    candidates = [OLLAMA_URL]
    candidates.extend(url for url in _wsl_urls() if url.rstrip("/") != OLLAMA_URL.rstrip("/"))
    tried: list[str] = []
    for url in candidates:
        tried.append(url)
        try:
            tags = _get(url, "/api/tags")
        except (HTTPError, URLError, TimeoutError, OSError, ValueError):
            continue
        _active_url = url
        names = _model_names(tags)
        model = configured_model()
        available = any(name == model or name.split(":", 1)[0] == model for name in names)
        return {
            "available": True,
            "url": url,
            "model_available": available,
            "models": sorted(names),
            "location": "WSL" if url not in (OLLAMA_URL, "http://localhost:11434") else "Windows/local endpoint",
        }
    _active_url = None
    return {
        "available": False,
        "url": None,
        "model_available": False,
        "models": [],
        "tried": tried,
    }


def answer_question(question: str, on_chunk=None) -> str:
    """Return an answer, optionally delivering Ollama's text chunks as they arrive."""
    global _active_url
    question = question.strip()
    if not question:
        raise ValueError("Question cannot be empty.")

    url = _active_url
    if not url:
        result = check_ollama()
        if not result["available"]:
            raise RuntimeError(
                "Ollama was not found on Windows or WSL. Start Ollama and expose "
                "its service on port 11434 (WSL localhost forwarding or WSL networking)."
            )
        url = result["url"]

    payload = json.dumps({
        "model": configured_model(),
        "messages": [{"role": "user", "content": question}],
        "stream": on_chunk is not None,
    }).encode("utf-8")
    request = Request(
        f"{url.rstrip('/')}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=180) as response:
            if on_chunk is None:
                result = json.loads(response.read().decode("utf-8"))
                answer = result.get("message", {}).get("content", "").strip()
            else:
                parts = []
                for line in response:
                    if not line.strip():
                        continue
                    event = json.loads(line.decode("utf-8"))
                    piece = event.get("message", {}).get("content", "")
                    if piece:
                        parts.append(piece)
                        on_chunk(piece)
                    if event.get("error"):
                        raise RuntimeError(f"Ollama stream error: {event['error']}")
                answer = "".join(parts).strip()
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Ollama returned HTTP {exc.code}: {detail}") from exc
    except (URLError, TimeoutError) as exc:
        _active_url = None
        raise RuntimeError(f"Could not reach Ollama at {url}: {exc}") from exc

    if not answer:
        raise RuntimeError("Ollama returned an empty answer.")
    return answer
