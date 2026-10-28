"""Interactive terminal entry point for the local Jarvis assistant."""

from datetime import datetime, timezone
from time import perf_counter

from diagnostics import run_startup_checks
from offline import OLLAMA_MODEL, answer_question
from speechdrive import speak
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
        try:
            answer = answer_question(question)
            elapsed = round(perf_counter() - started, 3)
            print(f"Jarvis: {answer}")
            speech_status = speak(answer)
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
