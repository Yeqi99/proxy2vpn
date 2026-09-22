#!/bin/bash
set -euo pipefail
if [ "$(uname -s)" != Darwin ]; then
  printf 'This installer is for macOS. Use install.ps1 on Windows.\n' >&2
  exit 1
fi
case "$(uname -m)" in
  arm64) platform=macos-arm64 ;;
  x86_64) platform=macos-intel ;;
  *) printf 'Unsupported CPU architecture.\n' >&2; exit 1 ;;
esac
version=0.2.2
base="https://github.com/Yeqi99/proxy2vpn/releases/download/v$version"
name="proxy2vpn-$version-$platform.zip"
stage="$(mktemp -d "${TMPDIR:-/tmp}/proxy2vpn.XXXXXXXX")"
printf 'Downloading Proxy2VPN %s for %s...\n' "$version" "$platform"
curl --fail --location --retry 3 "$base/$name" -o "$stage/$name"
curl --fail --silent --show-error --location --retry 3 "$base/SHA256SUMS" -o "$stage/SHA256SUMS"
expected="$(awk -v file="$name" '$2 == file {print $1}' "$stage/SHA256SUMS")"
actual="$(shasum -a 256 "$stage/$name" | awk '{print $1}')"
if [[ ! "$expected" =~ ^[a-fA-F0-9]{64}$ ]] || [ "$actual" != "$expected" ]; then
  printf 'Checksum verification failed. Installation has not started.\n' >&2
  exit 1
fi
ditto -x -k "$stage/$name" "$stage"
/bin/bash "$stage/Proxy2VPN/Install-Mac.command"
printf 'Done. The local console and desktop launcher are ready.\n'
