import argparse
import asyncio
import getpass
import json
from pathlib import Path
import subprocess
import sys
import time
from .config import load, new_config, save
from . import doctor, runtime, vm


def parser():
    p = argparse.ArgumentParser(description="LAN proxy to router-compatible L2TP gateway")
    p.add_argument("--home", type=Path, default=Path.home() / ".proxy2vpn", help="Private state directory")
    commands = p.add_subparsers(dest="command", required=True)
    console = commands.add_parser('console', help='Local web console and gateway manager')
    console.add_argument('--assets', type=Path, required=True)
    console.add_argument('--port', type=int, default=18990)
    console.add_argument('--open', action='store_true')
    init = commands.add_parser("init", help="Create a configuration; never overwrite existing credentials")
    init.add_argument("--listen-ip")
    init.add_argument("--router-ip")
    init.add_argument("--proxy-host")
    init.add_argument("--proxy-port", type=int, default=7890)
    init.add_argument("--proxy-type", choices=["socks5", "http"], default="socks5")
    init.add_argument("--proxy-auth", action="store_true", help="Prompt privately for upstream credentials")
    init.add_argument("--qemu", default="")
    for name in ("up", "run", "doctor"):
        command = commands.add_parser(name)
        command.add_argument("--assets", type=Path, required=True, help="Directory with vmlinuz, initramfs.gz, manifest.json")
        if name == "doctor":
            command.add_argument("--network", action="store_true", help="Contact gstatic through the configured proxy")
    commands.add_parser("down")
    commands.add_parser("status")
    commands.add_parser("router", help="Show router settings and password locally")
    return p


def execute(args):
    home = args.home.expanduser().resolve()
    if args.command == 'console':
        from .console import serve
        serve(home, args.assets, args.port, args.open)
        return 0
    if args.command == "init":
        listen = args.listen_ip or input("Computer LAN IPv4 address: ").strip()
        router = args.router_ip or input("Router LAN IPv4 address: ").strip()
        host = args.proxy_host or input(f"Proxy IPv4 address [{listen}]: ").strip() or listen
        cfg = new_config(listen, router, host, args.proxy_port, args.proxy_type)
        cfg["qemu"] = args.qemu
        if args.proxy_auth:
            cfg["proxy"]["username"] = input("Proxy username: ")
            cfg["proxy"]["password"] = getpass.getpass("Proxy password: ")
        save(home, cfg)
        print(f"Created {home / 'config.json'}. Run 'proxy2vpn router' to see router settings.")
        return 0
    if args.command == "status":
        state = json.loads((home / "status.json").read_text()) if (home / "status.json").exists() else {}
        state["process_alive"] = runtime.running(home)
        if not state["process_alive"]:
            state.update(running=False, l2tp_ready=False)
        print(json.dumps(state, indent=2))
        return 0 if state["process_alive"] and state.get("l2tp_ready") else 1
    if args.command == "down":
        if not runtime.running(home):
            print("Not running."); return 0
        (home / "stop").touch()
        for _ in range(20):
            if not runtime.running(home):
                print("Stopped."); return 0
            time.sleep(1)
        print("Stop requested; process has not exited yet."); return 1
    cfg = load(home)
    if args.command == "router":
        print(f"Protocol: L2TP (without IPsec)\nServer: {cfg['listen_ip']}\nPort: {cfg['listen_port']}"
              f"\nUsername: {cfg['username']}\nPassword: {cfg['password']}"
              "\nEnable device-based routing only for intended clients; keep this computer's proxy traffic outside the VPN.")
        return 0
    if args.command == "doctor":
        report = doctor.inspect(cfg, args.assets.resolve(), args.network)
        print(json.dumps(report, indent=2))
        return 0 if all(v.get("ok", True) for v in report.values()) else 1
    if args.command == "run":
        asyncio.run(runtime.serve(home, args.assets))
        return 0
    if runtime.running(home):
        print("Already running."); return 0
    vm.binary(cfg)
    vm.verify_assets(args.assets)
    executable = sys.executable
    if sys.platform == "win32" and Path(executable).with_name("pythonw.exe").exists():
        executable = str(Path(executable).with_name("pythonw.exe"))
    with (home / "launcher.log").open("ab") as log:
        child = vm.popen([executable, "-m", "proxy2vpn", "--home", str(home), "run",
            "--assets", str(args.assets.resolve())], stdin=subprocess.DEVNULL, stdout=log, stderr=log,
            start_new_session=sys.platform != "win32")
    # Wait for ownership, not full boot; status/doctor distinguish those states.
    for _ in range(20):
        if child.poll() is not None:
            raise RuntimeError(f"Gateway did not start. Inspect {home / 'launcher.log'}")
        if runtime.running(home):
            print("Started in background. Guest boot takes time; use status or doctor to check readiness.")
            return 0
        time.sleep(0.25)
    raise RuntimeError("Startup timed out; inspect launcher.log")


def main():
    args = parser().parse_args()
    try:
        code = execute(args)
    except KeyboardInterrupt:
        code = 130
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"Error: {error}", file=sys.stderr)
        code = 1
    raise SystemExit(code)
