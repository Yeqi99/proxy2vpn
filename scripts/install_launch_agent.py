"""Create, but do not load, a macOS per-user LaunchAgent."""
import argparse
from pathlib import Path
import plistlib
import sys

p = argparse.ArgumentParser()
p.add_argument("--assets", type=Path, required=True)
p.add_argument("--home", type=Path, default=Path.home() / ".proxy2vpn")
args = p.parse_args()
if sys.platform != "darwin":
    p.error("This installer is for macOS only")
destination = Path.home() / "Library/LaunchAgents/local.proxy2vpn.plist"
if destination.exists():
    p.error("LaunchAgent already exists; inspect it before replacing")
destination.parent.mkdir(parents=True, exist_ok=True)
home = args.home.resolve()
if not (home / "config.json").exists():
    p.error("Run proxy2vpn init first")
with destination.open("xb") as file:
    plistlib.dump({"Label": "local.proxy2vpn",
        "ProgramArguments": [sys.executable, "-m", "proxy2vpn", "--home", str(home), "run", "--assets", str(args.assets.resolve())],
        "RunAtLoad": True, "KeepAlive": True, "ThrottleInterval": 30,
        "EnvironmentVariables": {"PATH": "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"},
        "StandardOutPath": str(home / "launchd.log"), "StandardErrorPath": str(home / "launchd-error.log")}, file)
print(f'Created {destination}')
print('Load after stopping any manually launched instance:')
print(f'launchctl bootstrap gui/$(id -u) "{destination}"')
