#!/usr/bin/env bash
set -euo pipefail

repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
bin="$HOME/.local/bin"
mkdir -p "$bin"
cat > "$bin/jarvis" <<EOF
#!/usr/bin/env bash
exec python3 "$repo/main.py" "\$@"
EOF
chmod +x "$bin/jarvis"

case ":$PATH:" in
  *":$bin:"*) ;;
  *)
    profile="$HOME/.profile"
    touch "$profile"
    if ! grep -Fq 'export PATH="$HOME/.local/bin:$PATH"' "$profile"; then
      printf '\nexport PATH="$HOME/.local/bin:$PATH"\n' >> "$profile"
    fi
    export PATH="$bin:$PATH"
    ;;
esac
printf "Installed 'jarvis' for this WSL user. Open a new shell or run: source ~/.profile\n"
