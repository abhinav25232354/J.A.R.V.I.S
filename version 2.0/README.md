# Jarvis

This project asks a locally running [Ollama](https://ollama.com/) model for answers, speaks them with the configured [ElevenLabs Text to Speech API](https://elevenlabs.io/docs/api-reference/text-to-speech/convert), and saves each exchange as a separate JSON file in `memory/`. At startup it checks internet reachability, Ollama, ElevenLabs speech, memory storage and playback options, and reports CPU, RAM, disk, and available temperature sensor readings. These checks are informational and do not prevent startup.

## Setup

1. Install Ollama in Windows or WSL and download a model, for example `ollama pull llama3.2`.
2. Copy `.env.example` to `.env` and set `ELEVENLABS_API_KEY` to your API key. Keep `.env` private. Jarvis uses the George voice (`JBFqnCBsd6RMkjVDRZzb`) by default; change the voice ID with `/settings`. Set `ELEVENLABS_MODEL_ID` to change the model (default: `eleven_multilingual_v2`).
3. Install the terminal command:
   - Windows PowerShell: `powershell -ExecutionPolicy Bypass -File .\install-windows.ps1`, then open a new terminal.
   - WSL: `bash install-wsl.sh`, then open a new shell (or run `source ~/.profile`).

The Windows installer registers a PowerShell `jarvis` function and a Command Prompt
launcher. The WSL installer adds `~/.local/bin` to login and interactive shell paths.
The installers use Python 3.10 or newer, install Python if it is missing, create a
private environment for Jarvis, and install its libraries quietly. The command runs
inside the terminal where you type `jarvis`. Jarvis asks for your name once and
keeps it in `memory/profile.json`. Type `/settings` to change the Ollama model, ElevenLabs voice ID,
or speech speed. The uninstall menu removes the command, private environment, and
preferences after confirmation; project files and conversation history remain.

Jarvis prints Ollama output as it
arrives and begins speaking after the first seven words. Speech synthesis prepares
upcoming phrases while a separate playback worker speaks them in order, so audio
does not pause the text stream and the text stream does not interrupt audio.

Ollama discovery checks the configured server. Use `/settings` → `Ollama server` to choose automatic detection, WSL, Windows/local, or a custom URL; model selection remains available in `/settings`. `OLLAMA_TARGET` and `OLLAMA_URL` can override those preferences. Windows SAPI with the default installed voice is the secondary synthesis path when ElevenLabs is unavailable. Audio playback tries pygame, playsound, Windows MCI, ffplay, then ffmpeg WAV conversion with winsound. The text assistant continues if speech or memory storage is unavailable.

Type `exit`, `quit`, or `q` to close the assistant. Successful answers and failed attempts are recorded with timestamps, model, duration, and speech status.
