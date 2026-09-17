#!/bin/sh
set -eu
cd "$(dirname "$0")/../.."
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
PY=python3
[ ! -x .venv/bin/python ] || PY=.venv/bin/python
"$PY" -m proxy2vpn down
