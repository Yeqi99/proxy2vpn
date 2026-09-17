#!/bin/sh
set -eu
cd "$(dirname "$0")/../.."
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
PY=python3
[ ! -x .venv/bin/python ] || PY=.venv/bin/python
[ -f "$HOME/.proxy2vpn/config.json" ] || "$PY" -m proxy2vpn init
ARCH=x86_64
[ "$(uname -m)" != arm64 ] || ARCH=aarch64
"$PY" -m proxy2vpn up --assets "artifacts/$ARCH"
