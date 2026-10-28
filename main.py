"""Interactive terminal entry point for the local Jarvis assistant."""

from datetime import datetime, timezone
import re
from time import perf_counter

from diagnostics import run_startup_checks
from offline import answer_question, configured_model
from speechdrive import SpeechStreamer
from memory import save_exchange
from settings_menu import settings_menu
from user_settings import get_name, get_settings, set_name


def _save_safely(**record) -> None:
    try:
        save_exchange(**record)
    except Exception:
        # Keeping the interactive assistant alive takes priority over persistence.
        pass


def main() -> None:
    name = get_name()
    while not name:
        try:
            name = input("Hi, I'm Jarvis. What should I call you? ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            return
        if not name:
            print("Please enter a name so I can save your profile.")
            continue
        try:
            set_name(name)
        except OSError:
            print("I couldn't save your name. Check that the memory folder is writable.")
            name = ""

    try:
        run_startup_checks()
    except Exception:
        pass
    print(f"Jarvis is ready, {name}. Ask a question, type '/settings' to configure, or 'exit' to quit.")
    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break
        except Exception:
            continue
        if question.lower() in {"exit", "quit", "q"}:
            print("Goodbye.")
            break
        if not question:
            continue
        if question.lower() == "/settings":
            try:
                if settings_menu():
                    print("Goodbye.")
                    break
            except (EOFError, KeyboardInterrupt):
                print("\nSettings closed.")
            continue

        started = perf_counter()
        asked_at = datetime.now(timezone.utc).isoformat()
        speech = SpeechStreamer()
        spoken_buffer = ""
        first_segment = True

        def queue_speech(segment: str) -> None:
            speech.submit(segment)

        def receive_chunk(chunk: str) -> None:
            nonlocal spoken_buffer, first_segment
            print(chunk, end="", flush=True)
            spoken_buffer += chunk
            words = spoken_buffer.split()
            minimum_words, maximum_words = (7, 20) if first_segment else (12, 20)
            # Keep whole sentences when possible; split long sentences into full phrases.
            boundary = max(spoken_buffer.rfind(mark) for mark in (". ", "! ", "? ", ", "))
            boundary_ready = boundary >= 0 and len(spoken_buffer[:boundary + 1].split()) >= minimum_words
            if boundary_ready or len(words) >= maximum_words:
                if boundary_ready:
                    cut = boundary + 1
                else:
                    word_spans = list(re.finditer(r"\S+", spoken_buffer))
                    cut = word_spans[maximum_words - 1].end()
                segment, spoken_buffer = spoken_buffer[:cut].strip(), spoken_buffer[cut:].strip()
                if segment:
                    queue_speech(segment)
                    first_segment = False

        try:
            print("Jarvis: ", end="", flush=True)
            answer = answer_question(question, on_chunk=receive_chunk)
            if spoken_buffer.strip():
                queue_speech(spoken_buffer.strip())
            speech_status = speech.close()
            elapsed = round(perf_counter() - started, 3)
            print()
            _save_safely(
                question=question,
                answer=answer,
                asked_at=asked_at,
                model=configured_model(),
                voice=get_settings()["voice"],
                duration_seconds=elapsed,
                speech_status=speech_status,
                status="success",
            )
        except Exception as exc:
            speech.close()
            elapsed = round(perf_counter() - started, 3)
            print("Jarvis: I can't answer that right now. Please try again.")
            _save_safely(
                question=question,
                answer=None,
                asked_at=asked_at,
                model=configured_model(),
                duration_seconds=elapsed,
                speech_status="not attempted",
                status="error",
                error=type(exc).__name__,
            )


if __name__ == "__main__":
    main()
