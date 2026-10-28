# Jarvis

This root project asks a locally running [Ollama](https://ollama.com/) model for answers, speaks them with the selected Edge TTS voice, and saves each exchange as a separate JSON file in `memory/`. At startup it checks internet reachability, looks for Ollama on Windows and then WSL, checks memory storage and speech playback options, and reports CPU, RAM, disk, and available temperature sensor readings. These checks are informational and do not prevent startup.

## Setup

1. Install Ollama in Windows or WSL and download a model, for example `ollama pull llama3.2`.
2. Install the terminal command:
   - Windows PowerShell: `powershell -ExecutionPolicy Bypass -File .\install-windows.ps1`, then open a new terminal.
   - WSL: `bash install-wsl.sh`, then open a new shell (or run `source ~/.profile`).

The Windows installer registers a PowerShell `jarvis` function and a Command Prompt
launcher. The WSL installer adds `~/.local/bin` to login and interactive shell paths.
The installers use Python 3.10 or newer, install Python if it is missing, create a
private environment for Jarvis, and install its libraries quietly. The command runs
inside the terminal where you type `jarvis`. Jarvis asks for your name once and
keeps it in `memory/profile.json`. Type `/settings` to change the Ollama model, voice,
or speech speed. The uninstall menu removes the command, private environment, and
preferences after confirmation; project files and conversation history remain.

Jarvis prints Ollama output as it
arrives and begins speaking after the first seven words. Speech synthesis prepares
upcoming phrases while a separate playback worker speaks them in order, so audio
does not pause the text stream and the text stream does not interrupt audio.

Ollama discovery checks the configured `OLLAMA_URL` (default `http://localhost:11434`) and then the WSL VM's IP address on port 11434. You can select a different installed model with `/settings` or override it with `OLLAMA_MODEL`; change the preferred server URL with `OLLAMA_URL`. If Ollama is bound only to WSL's loopback and Windows localhost forwarding is unavailable, configure Ollama to listen on the WSL network interface. Windows SAPI is the secondary voice path and uses a matching installed voice when available, otherwise the Windows default voice. Audio playback tries pygame, playsound, Windows MCI, ffplay, then ffmpeg WAV conversion with winsound. The text assistant continues if speech or memory storage is unavailable.

Type `exit`, `quit`, or `q` to close the assistant. Successful answers and failed attempts are recorded with timestamps, model, duration, and speech status.
