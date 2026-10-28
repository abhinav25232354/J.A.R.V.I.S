"""Interactive preferences and confirmed CLI removal."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from user_settings import get_settings, save_settings, PROFILE_PATH, SETTINGS_PATH

VOICES = (
    ("Christopher (US)", "en-US-ChristopherNeural"),
    ("Andrew (US)", "en-US-AndrewMultilingualNeural"),
    ("Aria (US)", "en-US-AriaNeural"),
    ("Ava (US)", "en-US-AvaMultilingualNeural"),
    ("Emma (US)", "en-US-EmmaMultilingualNeural"),
    ("Jenny (US)", "en-US-JennyNeural"),
    ("Guy (US)", "en-US-GuyNeural"),
    ("Neerja (India)", "en-IN-NeerjaNeural"),
    ("Prabhat (India)", "en-IN-PrabhatNeural"),
)


def _remove_preferences() -> None:
    for path in (PROFILE_PATH, SETTINGS_PATH):
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass


def _uninstall() -> bool:
    root = Path(__file__).resolve().parent
    environment = (root / ".venv").resolve()
    if environment.parent != root or environment.name != ".venv":
        raise RuntimeError("Refusing to remove an unexpected environment path.")

    if os.name == "nt":
        bin_dir = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Jarvis" / "bin"
        launcher = bin_dir / "jarvis.cmd"
        try:
            launcher.unlink(missing_ok=True)
        except OSError:
            pass
        try:
            import winreg

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE) as key:
                try:
                    user_path, value_type = winreg.QueryValueEx(key, "Path")
                except FileNotFoundError:
                    user_path, value_type = "", winreg.REG_EXPAND_SZ
                match = str(bin_dir).casefold()
                path_entries = [entry for entry in user_path.split(";") if entry and entry.casefold() != match]
                winreg.SetValueEx(key, "Path", 0, value_type, ";".join(path_entries))
        except OSError:
            pass

        documents = Path.home() / "Documents"
        for profile_path in (
            documents / "WindowsPowerShell" / "Microsoft.PowerShell_profile.ps1",
            documents / "PowerShell" / "Microsoft.PowerShell_profile.ps1",
        ):
            try:
                lines = profile_path.read_text(encoding="utf-8-sig").splitlines()
                filtered = []
                skip_function = False
                for line in lines:
                    if line.strip() == "# Jarvis CLI function":
                        skip_function = True
                        continue
                    if skip_function:
                        skip_function = False
                        continue
                    filtered.append(line)
                if len(filtered) != len(lines):
                    profile_path.write_text("\n".join(filtered) + "\n", encoding="utf-8")
            except OSError:
                pass

        quoted_root = str(environment).replace("'", "''")
        script = (
            f"Wait-Process -Id {os.getpid()}; "
            f"if (Test-Path -LiteralPath '{quoted_root}') {{ Remove-Item -LiteralPath '{quoted_root}' -Recurse -Force }}; "
            "Remove-Item -LiteralPath $MyInvocation.MyCommand.Path -Force"
        )
        with tempfile.NamedTemporaryFile("w", suffix=".ps1", delete=False, encoding="utf-8") as file:
            file.write(script)
            cleanup_script = file.name
        subprocess.Popen(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden", "-File", cleanup_script],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        try:
            bin_dir.rmdir()
            bin_dir.parent.rmdir()
        except OSError:
            pass
    else:
        launcher = Path.home() / ".local" / "bin" / "jarvis"
        try:
            launcher.unlink(missing_ok=True)
        except OSError:
            pass
        if environment.exists():
            shutil.rmtree(environment, ignore_errors=True)
        profile = Path.home() / ".profile"
        for shell_file in (profile, Path.home() / ".bashrc"):
            try:
                lines = shell_file.read_text(encoding="utf-8").splitlines()
                filtered = []
                skip_path = False
                for line in lines:
                    if line.strip() == "# Jarvis CLI PATH":
                        skip_path = True
                        continue
                    if skip_path:
                        skip_path = False
                        continue
                    filtered.append(line)
                shell_file.write_text("\n".join(filtered) + "\n", encoding="utf-8")
            except OSError:
                pass
    _remove_preferences()
    return True


def settings_menu() -> bool:
    """Show the terminal settings menu. Return True after confirmed removal."""
    while True:
        settings = get_settings()
        print("\nJarvis settings")
        print(f"  1. Ollama model   {settings['model']}")
        print(f"  2. Speech speed   {settings['speech_speed']:.1f}x")
        current_voice = next((label for label, value in VOICES if value == settings['voice']), settings['voice'])
        print(f"  3. Voice          {current_voice}")
        print("  4. Uninstall Jarvis")
        print("  0. Back")
        choice = input("Select an option: ").strip()
        if choice == "0":
            return False
        if choice == "1":
            value = input("Ollama model name: ").strip()
            if value:
                save_settings({"model": value})
                print(f"Model set to {value}.")
        elif choice == "2":
            value = input("Speech speed (0.5 to 2.0, where 1.0 is normal): ").strip()
            try:
                speed = float(value)
                if not 0.5 <= speed <= 2.0:
                    raise ValueError
            except ValueError:
                print("Enter a number from 0.5 to 2.0.")
            else:
                save_settings({"speech_speed": speed})
                print(f"Speech speed set to {speed:.1f}x.")
        elif choice == "3":
            print("Available voices:")
            for index, (label, _) in enumerate(VOICES, start=1):
                print(f"  {index}. {label}")
            selected = input("Voice number: ").strip()
            try:
                voice = VOICES[int(selected) - 1][1]
            except (ValueError, IndexError):
                print("Choose one of the listed numbers.")
            else:
                save_settings({"voice": voice})
                print(f"Voice set to {voice}.")
        elif choice == "4":
            print("This removes the jarvis command, its private Python environment, and saved preferences.")
            print("Your project files and conversation history will remain.")
            if input("Type DELETE to confirm: ").strip() == "DELETE":
                _uninstall()
                print("Jarvis command removed.")
                return True
            print("Uninstall cancelled.")
        else:
            print("Choose 0, 1, 2, 3, or 4.")
