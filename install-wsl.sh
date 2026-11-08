#!/usr/bin/env bash
set -Eeuo pipefail

repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
venv="$repo/.venv"
bin="$HOME/.local/bin"
log="${TMPDIR:-/tmp}/jarvis-setup-${UID}.log"
total_steps=9

progress() {
  printf 'Progress %s/%s: %s\n' "$1" "$total_steps" "$2"
}

fail() {
  trap - ERR INT TERM
  printf 'Setup could not finish: %s\n' "$1" >&2
  if [[ -f "$log" ]]; then
    printf 'Setup notes were saved to: %s\n' "$log" >&2
  fi
  exit 1
}

unexpected_failure() {
  fail 'An unexpected setup step failed. Review the setup notes and run setup again.'
}
trap unexpected_failure ERR
trap 'fail "Setup was interrupted before it finished."' INT TERM

run_logged() {
  : >"$log"
  "$@" >"$log" 2>&1
}

run_sudo_logged() {
  if [[ $EUID -eq 0 ]]; then
    run_logged "$@"
  else
    run_logged sudo "$@"
  fi
}

progress 1 'Checking prerequisites'
if ! command -v apt-get >/dev/null 2>&1; then
  fail 'This installer needs an Ubuntu or Debian based WSL distribution with apt-get.'
fi
if ! command -v curl >/dev/null 2>&1; then
  # curl is installed with the other system prerequisites below.
  :
fi

progress 2 'Installing system packages'
if ! run_sudo_logged apt-get update -qq; then
  fail 'System package lists could not be refreshed. Check your network and package manager access.'
fi
if ! run_sudo_logged env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
  ca-certificates curl ffmpeg gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
  python3 python3-dev python3-pip python3-venv build-essential pkg-config; then
  fail 'Required system packages could not be installed. Check administrator access and review the setup notes.'
fi

if ! command -v python3 >/dev/null 2>&1 || ! python3 -c 'import sys; raise SystemExit(sys.version_info < (3, 10))' >/dev/null 2>&1; then
  fail 'Python 3.10 or newer is required. Install a supported Python version and run setup again.'
fi

progress 3 'Checking Ollama runtime'
if command -v ollama >/dev/null 2>&1; then
  progress 4 'Using installed Ollama'
else
  progress 4 'Installing Ollama runtime'
  ollama_installer="${TMPDIR:-/tmp}/jarvis-ollama-install-${UID}.sh"
  if ! run_logged curl -fsSL https://ollama.com/install.sh -o "$ollama_installer"; then
    fail 'Ollama could not be downloaded. Check your network or install it from ollama.com/download.'
  fi
  if ! run_sudo_logged sh "$ollama_installer"; then
    rm -f -- "$ollama_installer"
    fail 'Ollama installation could not finish. Review the setup notes or install it from ollama.com/download.'
  fi
  rm -f -- "$ollama_installer"
  if ! command -v ollama >/dev/null 2>&1; then
    fail 'Ollama was installed but its command is not available. Open a new shell and run setup again.'
  fi
fi

progress 5 'Preparing Python environment'
if [[ -L "$venv" ]]; then
  fail 'The private Python environment path is a symbolic link. Remove or rename it before setup.'
fi
if [[ -e "$venv" ]]; then
  resolved_venv="$(realpath -m -- "$venv")"
  if [[ "$(dirname -- "$resolved_venv")" != "$repo" || "$(basename -- "$resolved_venv")" != '.venv' ]]; then
    fail 'The existing private environment path is unexpected. Move it aside before setup.'
  fi
  if [[ ! -x "$venv/bin/python" ]] || ! "$venv/bin/python" -c 'import sys; raise SystemExit(sys.version_info < (3, 10))' >/dev/null 2>&1; then
    rm -rf -- "$venv"
  fi
fi
if ! run_logged python3 -m venv --upgrade "$venv"; then
  fail 'The private Python environment could not be prepared. Review the setup notes and check available disk space.'
fi
if [[ ! -x "$venv/bin/python" ]] || ! "$venv/bin/python" -c 'import sys; raise SystemExit(sys.version_info < (3, 10))' >/dev/null 2>&1; then
  fail 'The private environment does not contain a supported Python version.'
fi

progress 6 'Updating package tools'
if ! run_logged "$venv/bin/python" -m ensurepip --upgrade; then
  fail 'Python package support could not be prepared. Review the setup notes.'
fi
if ! run_logged "$venv/bin/python" -m pip install --upgrade --disable-pip-version-check pip setuptools wheel; then
  fail 'Python package tools could not be updated. Check your network and review the setup notes.'
fi

progress 7 'Installing Python libraries'
if ! run_logged "$venv/bin/python" -m pip install --upgrade --disable-pip-version-check -r "$repo/requirements.txt"; then
  fail 'Jarvis libraries could not be installed. Check your network and review the setup notes.'
fi
if ! run_logged "$venv/bin/python" -m pip check; then
  fail 'Some Python libraries have incompatible requirements. Review the setup notes and run setup again.'
fi
progress 8 'Updating Jarvis command'
mkdir -p -- "$bin"
cat >"$bin/jarvis" <<EOF
#!/usr/bin/env bash
exec "$venv/bin/python" "$repo/main.py" "\$@"
EOF
chmod 755 "$bin/jarvis"

for profile in "$HOME/.profile" "$HOME/.bashrc"; do
  touch "$profile"
  temporary="$(mktemp "${TMPDIR:-/tmp}/jarvis-profile.XXXXXX")"
  awk '
    /^# Jarvis CLI PATH BEGIN$/ { skip=1; next }
    /^# Jarvis CLI PATH END$/ { skip=0; next }
    /^# Jarvis CLI PATH$/ { getline; if ($0 ~ /export PATH=.*\.local\/bin/) next; print; next }
    !skip { print }
  ' "$profile" >"$temporary"
  {
    printf '\n# Jarvis CLI PATH BEGIN\n'
    printf 'export PATH="$HOME/.local/bin:$PATH"\n'
    printf '# Jarvis CLI PATH END\n'
  } >>"$temporary"
  cat "$temporary" >"$profile"
  rm -f -- "$temporary"
done
export PATH="$bin:$PATH"

progress 9 'Finishing installation'
rm -f -- "$log"
printf 'Jarvis is installed or updated. Open a new shell and type: jarvis\n'
printf 'Setup note: Install a model with: ollama pull llama3.2\n'
