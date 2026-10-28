"""Interactive terminal entry point for the local Jarvis assistant."""

from datetime import datetime, timezone
import re
from time import perf_counter

from diagnostics import run_startup_checks
from offline import OLLAMA_MODEL, answer_question
from speechdrive import SpeechStreamer
from memory import save_exchange


def _save_safely(**record) -> None:
    try:
        save_exchange(**record)
    except Exception:
        # Keeping the interactive assistant alive takes priority over persistence.
        pass


def main() -> None:
    try:
        run_startup_checks()
    except Exception:
        pass
    print("Jarvis is ready. Ask a question, or type 'exit' to quit.")
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
                model=OLLAMA_MODEL,
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
                model=OLLAMA_MODEL,
                duration_seconds=elapsed,
                speech_status="not attempted",
                status="error",
                error=type(exc).__name__,
            )


if __name__ == "__main__":
    main()
