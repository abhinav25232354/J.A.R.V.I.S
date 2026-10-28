"""Fault-tolerant speech output with five audio playback backends."""

import asyncio
import importlib.util
import os
import queue
import shutil
import subprocess
import tempfile
from threading import Thread
import time
import uuid
from pathlib import Path
from user_settings import get_settings

VOICE = "en-US-ChristopherNeural"
_EDGE_AVAILABLE: bool | None = None
_EDGE_CHECKED_AT = 0.0
_EDGE_RECHECK_SECONDS = 300


def speech_capabilities() -> dict:
    """Report installed speech and playback options without importing pygame."""
    modules = {
        name: importlib.util.find_spec(name) is not None
        for name in ("edge_tts", "pygame", "playsound", "pyttsx3")
    }
    commands = {name: shutil.which(name) is not None for name in ("ffplay", "ffmpeg")}
    return {"modules": modules, "commands": commands}


async def _generate_edge_audio(text: str, path: str) -> None:
    import edge_tts

    proxy = os.getenv("EDGE_TTS_PROXY") or None
    settings = get_settings()
    voice = settings["voice"]
    speed = round((settings["speech_speed"] - 1.0) * 100)
    rate = f"{speed:+d}%"
    last_error = None
    for attempt in range(2):
        try:
            communicate = edge_tts.Communicate(
                text,
                voice,
                rate=rate,
                proxy=proxy,
                connect_timeout=12,
                receive_timeout=45,
            )
            await asyncio.wait_for(communicate.save(path), timeout=60)
            if not Path(path).is_file() or Path(path).stat().st_size < 128:
                raise RuntimeError("Edge TTS returned an empty or invalid audio file")
            return
        except Exception as exc:
            last_error = exc
            if attempt == 0:
                await asyncio.sleep(0.4)
    raise RuntimeError(f"Edge TTS synthesis failed: {last_error}") from last_error


def check_edge_voice(timeout: float = 10.0) -> dict:
    """Verify Christopher can actually synthesize audio, not merely import."""
    global _EDGE_AVAILABLE, _EDGE_CHECKED_AT
    if not importlib.util.find_spec("edge_tts"):
        _EDGE_AVAILABLE = False
        _EDGE_CHECKED_AT = time.monotonic()
        return {"available": False, "detail": "edge-tts package is not installed"}
    audio_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as audio_file:
            audio_path = audio_file.name
        asyncio.run(asyncio.wait_for(
            _generate_edge_audio("Jarvis voice check.", audio_path), timeout=timeout
        ))
        _EDGE_AVAILABLE = True
        _EDGE_CHECKED_AT = time.monotonic()
        return {"available": True, "voice": get_settings()["voice"]}
    except Exception as exc:
        _EDGE_AVAILABLE = False
        _EDGE_CHECKED_AT = time.monotonic()
        return {"available": False, "detail": f"{type(exc).__name__}: {exc}"}
    finally:
        if audio_path:
            try:
                os.remove(audio_path)
            except OSError:
                pass


def _play_pygame(path: str) -> None:
    os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
    import pygame

    pygame.mixer.init()
    try:
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        pygame.mixer.music.unload()
    finally:
        pygame.mixer.quit()


def _play_playsound(path: str) -> None:
    from playsound import playsound

    try:
        playsound(path, block=True)
    except TypeError:
        playsound(path)


def _play_mci(path: str) -> None:
    """Play MP3 through Windows Media Control Interface."""
    if os.name != "nt":
        raise OSError("Windows MCI is unavailable")
    import ctypes

    alias = f"jarvis_{uuid.uuid4().hex}"
    escaped = os.path.abspath(path).replace('"', '""')
    command = ctypes.windll.winmm.mciSendStringW
    buffer = ctypes.create_unicode_buffer(512)
    open_result = command(f'open "{escaped}" type mpegvideo alias {alias}', buffer, 512, None)
    if open_result:
        raise OSError(f"MCI open failed ({open_result})")
    try:
        result = command(f"play {alias} wait", buffer, 512, None)
        if result:
            raise OSError(f"MCI playback failed ({result})")
    finally:
        command(f"close {alias}", buffer, 512, None)


def _play_ffplay(path: str) -> None:
    executable = shutil.which("ffplay")
    if not executable:
        raise FileNotFoundError("ffplay not installed")
    subprocess.run(
        [executable, "-nodisp", "-autoexit", "-loglevel", "quiet", path],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=300,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def _play_wav(path: str) -> None:
    """Last playback option: convert to WAV with ffmpeg and use Windows winsound."""
    if os.name != "nt":
        raise OSError("winsound playback is available only on Windows")
    executable = shutil.which("ffmpeg")
    if not executable:
        raise FileNotFoundError("ffmpeg not installed for WAV conversion")
    import winsound

    wav_path = f"{path}.wav"
    subprocess.run(
        [executable, "-y", "-loglevel", "quiet", "-i", path, "-ac", "1", "-ar", "22050", wav_path],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=120,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    winsound.PlaySound(wav_path, winsound.SND_FILENAME)


def _play_with_fallbacks(path: str) -> str | None:
    """Try five independent playback methods; return the successful method."""
    backends = (
        ("pygame", _play_pygame),
        ("playsound", _play_playsound),
        ("Windows MCI", _play_mci),
        ("ffplay", _play_ffplay),
        ("WAV/winsound", _play_wav),
    )
    for name, playback in backends:
        try:
            # Do not redirect sys.stdout/stderr here: they are process-wide, so a
            # playback thread would swallow the independent Ollama text stream.
            playback(path)
            return name
        except Exception:
            continue
    return None


def _speak_local_windows(text: str) -> bool:
    """Last resort speech synthesis via built-in Windows SAPI."""
    if os.name != "nt":
        return False
    try:
        import base64

        settings = get_settings()
        voice_name = settings["voice"].split("-")[-1].replace("Multilingual", "").replace("Neural", "")
        encoded = base64.b64encode(text.encode("utf-16le")).decode("ascii")
        encoded_voice = base64.b64encode(voice_name.encode("utf-16le")).decode("ascii")
        script = (
            "$text=[Text.Encoding]::Unicode.GetString([Convert]::FromBase64String('"
            + encoded
            + "')); $voiceName=[Text.Encoding]::Unicode.GetString([Convert]::FromBase64String('"
            + encoded_voice
            + "')); Add-Type -AssemblyName System.Speech; "
            "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            "$v=$s.GetInstalledVoices() | Where-Object { $_.VoiceInfo.Name -match [regex]::Escape($voiceName) } | Select-Object -First 1; "
            "if ($v) { $s.SelectVoice($v.VoiceInfo.Name) }; $s.Speak($text)"
        )
        subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=300,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return True
    except Exception:
        return False


def speak(text: str) -> str:
    """Speak with the configured Edge voice, never raising to the caller."""
    global _EDGE_AVAILABLE, _EDGE_CHECKED_AT
    if not isinstance(text, str) or not text.strip():
        return "skipped"
    audio_path = None
    should_try_edge = (
        _EDGE_AVAILABLE is not False
        or time.monotonic() - _EDGE_CHECKED_AT >= _EDGE_RECHECK_SECONDS
    )
    if should_try_edge:
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as audio_file:
                audio_path = audio_file.name
            asyncio.run(_generate_edge_audio(text, audio_path))
            _EDGE_AVAILABLE = True
            _EDGE_CHECKED_AT = time.monotonic()
            backend = _play_with_fallbacks(audio_path)
            if backend:
                return f"spoken with {get_settings()['voice']} via {backend}"
        except Exception:
            _EDGE_AVAILABLE = False
            _EDGE_CHECKED_AT = time.monotonic()
        finally:
            if audio_path:
                try:
                    os.remove(audio_path)
                except OSError:
                    pass
                try:
                    os.remove(f"{audio_path}.wav")
                except OSError:
                    pass

    if _speak_local_windows(text):
        return "spoken with Windows SAPI secondary voice"
    return "unavailable; text answer retained"


class SpeechStreamer:
    """Synthesize upcoming phrases while a playback worker speaks earlier ones."""

    def __init__(self) -> None:
        self._text_queue: queue.Queue = queue.Queue()
        self._audio_queue: queue.Queue = queue.Queue()
        self._statuses: list[str] = []
        self._synthesizer = None
        self._player = None
        self._closed = False

    def _start(self) -> None:
        if self._synthesizer is not None:
            return
        self._synthesizer = Thread(target=self._synthesize, daemon=True)
        self._player = Thread(target=self._play, daemon=True)
        self._synthesizer.start()
        self._player.start()

    def submit(self, text: str) -> None:
        if text and text.strip() and not self._closed:
            self._start()
            self._text_queue.put(text.strip())

    def _synthesize(self) -> None:
        global _EDGE_AVAILABLE, _EDGE_CHECKED_AT
        while True:
            text = self._text_queue.get()
            try:
                if text is None:
                    break
                path = None
                try:
                    should_try_edge = (
                        _EDGE_AVAILABLE is not False
                        or time.monotonic() - _EDGE_CHECKED_AT >= _EDGE_RECHECK_SECONDS
                    )
                    if not should_try_edge:
                        self._audio_queue.put((None, text, False))
                        continue
                    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as audio_file:
                        path = audio_file.name
                    asyncio.run(_generate_edge_audio(text, path))
                    _EDGE_AVAILABLE = True
                    _EDGE_CHECKED_AT = time.monotonic()
                    self._audio_queue.put((path, text, True))
                    path = None
                except Exception:
                    _EDGE_AVAILABLE = False
                    _EDGE_CHECKED_AT = time.monotonic()
                    self._audio_queue.put((None, text, False))
                finally:
                    if path:
                        try:
                            os.remove(path)
                        except OSError:
                            pass
            finally:
                self._text_queue.task_done()
        self._audio_queue.put(None)

    def _play(self) -> None:
        while True:
            item = self._audio_queue.get()
            try:
                if item is None:
                    return
                path, text, synthesized = item
                try:
                    if synthesized and path:
                        backend = _play_with_fallbacks(path)
                        if backend:
                            self._statuses.append(f"spoken with {get_settings()['voice']} via {backend}")
                        elif _speak_local_windows(text):
                            self._statuses.append("spoken with Windows SAPI secondary voice")
                        else:
                            self._statuses.append("unavailable; text answer retained")
                    elif _speak_local_windows(text):
                        self._statuses.append("spoken with Windows SAPI secondary voice")
                    else:
                        self._statuses.append("unavailable; text answer retained")
                finally:
                    if path:
                        for target in (path, f"{path}.wav"):
                            try:
                                os.remove(target)
                            except OSError:
                                pass
            finally:
                self._audio_queue.task_done()

    def close(self) -> str:
        if self._closed:
            return "; ".join(dict.fromkeys(self._statuses)) or "skipped"
        self._closed = True
        if self._synthesizer is None:
            return "skipped"
        self._text_queue.put(None)
        self._text_queue.join()
        self._synthesizer.join()
        self._audio_queue.join()
        self._player.join()
        return "; ".join(dict.fromkeys(self._statuses)) or "unavailable; text answer retained"
