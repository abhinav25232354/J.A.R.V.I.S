"""Discover and query an Ollama server on Windows or inside WSL."""

import json
import getpass
import os
import platform
from pathlib import Path
import shutil
import subprocess
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from user_settings import get_settings


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
_active_url: str | None = None
_active_model: str | None = None
_ollama_process = None


def locate_ollama_models_folder() -> str | None:
    """Locate Ollama's model store on Windows, WSL, or a custom install path."""
    candidates: list[Path] = []
    configured = os.getenv("OLLAMA_MODELS")
    if configured:
        candidates.append(Path(os.path.expandvars(configured)).expanduser())

    if platform.system() == "Windows":
        profiles = [os.getenv("USERPROFILE"), str(Path.home())]
        candidates.extend(Path(profile) / ".ollama" / "models" for profile in dict.fromkeys(p for p in profiles if p))
    else:
        candidates.append(Path.home() / ".ollama" / "models")
        # WSL can share the Windows Ollama model store. Check likely usernames
        # first, then mounted user profiles so a different Linux username works.
        if "microsoft" in platform.release().lower() or os.getenv("WSL_DISTRO_NAME"):
            users_root = Path("/mnt/c/Users")
            usernames = [os.getenv("LOGNAME"), getpass.getuser()]
            for username in dict.fromkeys(name for name in usernames if name):
                candidates.append(users_root / username / ".ollama" / "models")
            try:
                candidates.extend(path / ".ollama" / "models" for path in users_root.iterdir() if path.is_dir())
            except OSError:
                pass

    checked: set[str] = set()
    existing: list[Path] = []
    for candidate in candidates:
        key = str(candidate).casefold()
        if key in checked:
            continue
        checked.add(key)
        try:
            if candidate.is_dir():
                existing.append(candidate)
                if any(candidate.iterdir()):
                    return str(candidate)
        except OSError:
            continue
    return str(existing[0]) if existing else None


def _ollama_executable() -> str | None:
    """Find Ollama on PATH or in its common per-user/system install folders."""
    found = shutil.which("ollama") or shutil.which("ollama.exe")
    if found:
        return found
    if os.name == "nt":
        roots = [Path(os.environ.get("LOCALAPPDATA", "")), Path(os.environ.get("ProgramFiles", r"C:\Program Files"))]
        candidates = [root / "Programs" / "Ollama" / "ollama.exe" for root in roots]
        candidates.extend(root / "Ollama" / "ollama.exe" for root in roots)
        # The installer records custom install locations in the Windows registry.
        try:
            import winreg
            keys = (
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\App Paths\ollama.exe"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\App Paths\ollama.exe"),
            )
            for hive, key_name in keys:
                try:
                    with winreg.OpenKey(hive, key_name) as key:
                        registered, _ = winreg.QueryValueEx(key, None)
                    candidates.insert(0, Path(os.path.expandvars(registered.strip('"'))))
                except OSError:
                    continue
        except ImportError:
            pass
        for candidate in candidates:
            if candidate.is_file():
                return str(candidate)
    return None


def _start_ollama() -> None:
    """Start the local Ollama service when installed but not already listening."""
    global _ollama_process
    executable = _ollama_executable()
    if not executable:
        return
    try:
        _ollama_process = subprocess.Popen(
            [executable, "serve"], stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except OSError:
        return
    import time
    for _ in range(12):
        try:
            _get(OLLAMA_URL, "/api/tags", timeout=1.0)
            return
        except (HTTPError, URLError, TimeoutError, OSError, ValueError):
            time.sleep(0.5)


def _get(url: str, path: str, timeout: float = 2.0) -> dict:
    request = Request(f"{url.rstrip('/')}{path}", headers={"Accept": "application/json"})
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _wsl_urls() -> list[str]:
    """Get addresses for each running WSL distribution."""
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    urls = []
    try:
        listing = subprocess.run(["wsl.exe", "--list", "--quiet"], capture_output=True, timeout=5, check=False, creationflags=creationflags)
    except (OSError, subprocess.TimeoutExpired):
        return []
    if listing.returncode != 0:
        return []
    raw = listing.stdout
    # wsl.exe may emit UTF-16 even when Python requested no text decoding.
    output = raw.decode("utf-16-le", errors="ignore") if b"\x00" in raw else raw.decode(errors="replace")
    distros = [line.strip().strip("\x00").strip() for line in output.splitlines() if line.strip().strip("\x00").strip()]
    for distro in distros:
        try:
            result = subprocess.run(
                ["wsl.exe", "-d", distro, "--", "hostname", "-I"],
                capture_output=True, text=True, timeout=4, check=False,
                creationflags=creationflags,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        if result.returncode != 0:
            continue
        for address in result.stdout.split():
            host = f"[{address}]" if ":" in address else address
            url = f"http://{host}:11434"
            if url not in urls:
                urls.append(url)
    return urls


def _wsl_distros() -> list[str]:
    """Return installed WSL distro names, including distros that are stopped."""
    try:
        result = subprocess.run(
            ["wsl.exe", "--list", "--quiet"], capture_output=True, timeout=5,
            check=False, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if result.returncode != 0:
        return []
    raw = result.stdout
    output = raw.decode("utf-16-le", errors="ignore") if b"\x00" in raw else raw.decode(errors="replace")
    return [line.strip().strip("\x00").strip() for line in output.splitlines() if line.strip().strip("\x00").strip()]


def _start_wsl_ollama() -> None:
    """Start Ollama inside any WSL distro where its Linux command is installed."""
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    for distro in _wsl_distros():
        try:
            installed = subprocess.run(
                ["wsl.exe", "-d", distro, "--", "sh", "-lc", "command -v ollama"],
                capture_output=True, text=True, timeout=5, check=False,
                creationflags=creationflags,
            )
            if installed.returncode != 0 or not installed.stdout.strip():
                continue
            subprocess.Popen(
                ["wsl.exe", "-d", distro, "--", "sh", "-lc", "OLLAMA_HOST=0.0.0.0:11434 ollama serve"],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, creationflags=creationflags,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue


def _model_names(payload: dict) -> set[str]:
    return {
        str(item.get("name", ""))
        for item in payload.get("models", [])
        if isinstance(item, dict)
    }


def list_ollama_models() -> dict:
    """Discover Ollama and return its installed models and server location."""
    return check_ollama()


def _resolve_discovered_model(names: set[str]) -> str:
    settings = get_settings()
    model = os.getenv("OLLAMA_MODEL") or settings["model"]
    # Automatic mode can recover from a stale saved model. Manual mode keeps
    # the user's choice so a missing model is reported instead of silently
    # switching to another one.
    if (
        names
        and settings.get("model_selection", "auto") == "auto"
        and not os.getenv("OLLAMA_MODEL")
        and not any(name == model or name.split(":", 1)[0] == model for name in names)
    ):
        model = sorted(names)[0]
    return model


def configured_model() -> str:
    """Resolve the persisted model, while allowing an environment override."""
    if os.getenv("OLLAMA_MODEL"):
        return os.environ["OLLAMA_MODEL"]
    settings = get_settings()
    if settings.get("model_selection", "auto") == "manual":
        return settings["model"]
    return _active_model or settings["model"]


def check_ollama() -> dict:
    """Find a reachable Ollama server, preferring Windows before WSL."""
    global _active_url, _active_model
    models_dir = locate_ollama_models_folder()
    candidates = [OLLAMA_URL]
    candidates.extend(url for url in _wsl_urls() if url.rstrip("/") != OLLAMA_URL.rstrip("/"))
    tried: list[str] = []
    for url in candidates:
        tried.append(url)
        try:
            tags = _get(url, "/api/tags")
        except (HTTPError, URLError, TimeoutError, OSError, ValueError):
            continue
        names = _model_names(tags)
        model = _resolve_discovered_model(names)
        _active_model = model
        _active_url = url
        available = any(name == model or name.split(":", 1)[0] == model for name in names)
        return {
            "available": True,
            "url": url,
            "model_available": available,
            "models": sorted(names),
            "location": "WSL" if url not in (OLLAMA_URL, "http://localhost:11434") else "Windows/local endpoint",
            "models_dir": models_dir,
        }
    if OLLAMA_URL.rstrip("/") == "http://localhost:11434":
        _start_ollama()
        try:
            tags = _get(OLLAMA_URL, "/api/tags")
            names = _model_names(tags)
            if names:
                model = _resolve_discovered_model(names)
                _active_url, _active_model = OLLAMA_URL, model
                return {"available": True, "url": OLLAMA_URL, "model_available": any(name == model or name.split(":", 1)[0] == model for name in names), "models": sorted(names), "location": "Windows/local endpoint", "models_dir": models_dir}
        except (HTTPError, URLError, TimeoutError, OSError, ValueError):
            pass
    # Windows may have Ollama installed but stopped inside a WSL distro. Start
    # it there, then retry localhost forwarding and each distro's network IP.
    _start_wsl_ollama()
    wsl_candidates = ["http://localhost:11434", *_wsl_urls()]
    for url in dict.fromkeys(wsl_candidates):
        if url in tried and url != "http://localhost:11434":
            continue
        tried.append(url)
        try:
            tags = _get(url, "/api/tags", timeout=3.0)
        except (HTTPError, URLError, TimeoutError, OSError, ValueError):
            continue
        names = _model_names(tags)
        model = _resolve_discovered_model(names)
        _active_url, _active_model = url, model
        return {
            "available": True,
            "url": url,
            "model_available": any(name == model or name.split(":", 1)[0] == model for name in names),
            "models": sorted(names),
            "location": "WSL",
            "models_dir": models_dir,
        }
    _active_url = None
    _active_model = None
    return {
        "available": False,
        "url": None,
        "model_available": False,
        "models": [],
        "tried": tried,
        "models_dir": models_dir,
    }


def answer_question(question: str, on_chunk=None) -> str:
    """Return an answer, optionally delivering Ollama's text chunks as they arrive."""
    global _active_url
    question = question.strip()
    if not question:
        raise ValueError("Question cannot be empty.")

    payload = json.dumps({
        "model": configured_model(),
        "messages": [{"role": "user", "content": question}],
        "stream": on_chunk is not None,
    }).encode("utf-8")
    delivered_chunks = False
    last_error = None
    for attempt in range(2):
        url = _active_url
        if not url:
            result = check_ollama()
            if not result["available"]:
                raise RuntimeError(
                    "Ollama was not found on Windows or WSL. Start Ollama and expose "
                    "its service on port 11434 (WSL localhost forwarding or WSL networking)."
                )
            url = result["url"]

        request = Request(
            f"{url.rstrip('/')}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        parts = []
        try:
            with urlopen(request, timeout=180) as response:
                if on_chunk is None:
                    result = json.loads(response.read().decode("utf-8"))
                    answer = result.get("message", {}).get("content", "").strip()
                else:
                    for line in response:
                        if not line.strip():
                            continue
                        event = json.loads(line.decode("utf-8"))
                        piece = event.get("message", {}).get("content", "")
                        if piece:
                            parts.append(piece)
                            delivered_chunks = True
                            on_chunk(piece)
                        if event.get("error"):
                            raise RuntimeError(f"Ollama stream error: {event['error']}")
                    answer = "".join(parts).strip()
            if not answer:
                raise RuntimeError("Ollama returned an empty answer.")
            return answer
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Ollama returned HTTP {exc.code}: {detail}") from exc
        except (URLError, TimeoutError, ConnectionError) as exc:
            _active_url = None
            last_error = exc
            # Rediscover/restart Ollama once when a connection drops before any
            # streamed text reaches the user. Never replay a partial response.
            if attempt == 0 and not delivered_chunks:
                continue
            raise RuntimeError(f"Could not reach Ollama at {url}: {exc}") from exc

    raise RuntimeError(f"Could not reconnect to Ollama: {last_error}")
