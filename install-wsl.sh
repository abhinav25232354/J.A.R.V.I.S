#!/usr/bin/env bash
set -euo pipefail

repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
bin="$HOME/.local/bin"
python=""

echo 'Jarvis setup: checking Python...'
if command -v python3 >/dev/null 2>&1 && python3 -c 'import sys; raise SystemExit(sys.version_info < (3, 10))' 2>/dev/null; then
  python=python3
else
  echo 'Installing Python and virtual environment support...'
  if ! command -v apt-get >/dev/null 2>&1; then
    echo 'Python 3.10+ is required; install it with your Linux package manager and rerun.' >&2
    exit 1
  fi
  sudo apt-get update -qq >/dev/null
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3 python3-venv python3-pip >/dev/null
  python=python3
  if ! "$python" -c 'import sys; raise SystemExit(sys.version_info < (3, 10))'; then
    echo 'The system package manager did not provide Python 3.10+. Install that version and rerun.' >&2
    exit 1
  fi
fi

echo 'Preparing private environment...'
venv="$repo/.venv"
log="${TMPDIR:-/tmp}/jarvis-setup.log"
if [[ ! -x "$venv/bin/python" ]]; then
  if ! "$python" -m venv "$venv" >"$log" 2>&1; then
    echo 'Installing Python virtual environment support...'
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3-venv >/dev/null
    if ! "$python" -m venv "$venv" >"$log" 2>&1; then
      echo "Python environment setup failed. Details: $log" >&2
      exit 1
    fi
  fi
fi
echo 'Installing required libraries...'
if ! "$venv/bin/python" -m pip install --disable-pip-version-check --quiet -r "$repo/requirements.txt" >"$log" 2>&1; then
  echo "Library installation failed. Details: $log" >&2
  exit 1
fi

mkdir -p "$bin"
cat > "$bin/jarvis" <<EOF
#!/usr/bin/env bash
exec "$venv/bin/python" "$repo/main.py" "\$@"
EOF
chmod +x "$bin/jarvis"

case ":$PATH:" in
  *":$bin:"*) ;;
  *)
    profile="$HOME/.profile"
    touch "$profile"
    if ! grep -Fq '# Jarvis CLI PATH' "$profile"; then
      printf '\n# Jarvis CLI PATH\nexport PATH="$HOME/.local/bin:$PATH"\n' >> "$profile"
    fi
    export PATH="$bin:$PATH"
    ;;
esac

bashrc="$HOME/.bashrc"
touch "$bashrc"
if ! grep -Fq '# Jarvis CLI PATH' "$bashrc"; then
  printf '\n# Jarvis CLI PATH\nexport PATH="$HOME/.local/bin:$PATH"\n' >> "$bashrc"
fi
echo 'Jarvis is installed. Open a shell and type: jarvis'
