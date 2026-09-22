#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
if ! command -v brew >/dev/null; then
  printf 'Installing Homebrew. macOS may request administrator permission or Command Line Tools.\n'
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi
if [ -x /opt/homebrew/bin/brew ]; then eval "$(/opt/homebrew/bin/brew shellenv)"; fi
if [ -x /usr/local/bin/brew ]; then eval "$(/usr/local/bin/brew shellenv)"; fi
brew install python@3.13 qemu
ROOT="$HOME/Library/Application Support/Proxy2VPN"
mkdir -p "$ROOT/assets"
"$(brew --prefix python@3.13)/bin/python3.13" -m venv "$ROOT/python"
"$ROOT/python/bin/python" -m pip install --upgrade --force-reinstall app/*.whl
cp assets/* "$ROOT/assets/"
ARCH=x86_64
[ "$(uname -m)" != arm64 ] || ARCH=aarch64
"$ROOT/python/bin/python" -m proxy2vpn.setup --restart --home "$HOME/.proxy2vpn" --assets "$ROOT/assets" --qemu "$(command -v qemu-system-$ARCH)"
printf '\nReady: http://127.0.0.1:18990/\n'
