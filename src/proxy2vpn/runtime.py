"""Owned foreground supervisor; status never substitutes for device acceptance."""
import asyncio
from contextlib import contextmanager
import ctypes
import datetime
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import subprocess
import signal
import sys
import time
import psutil
from . import relay, vm
from .config import load, private_dir
from .probe import probe
from .render import write_initramfs


def atomic_json(path, value):
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(value, indent=2), encoding="utf-8")
    temp.replace(path)


def running(home):
    try:
        record = json.loads((home / "owner.json").read_text())
        proc = psutil.Process(record["pid"])
        if abs(proc.create_time() - record["created"]) > 0.1:
            return False
        return proc.is_running() and "proxy2vpn" in " ".join(proc.cmdline())
    except (OSError, ValueError, KeyError, psutil.Error):
        return False


@contextmanager
def lock(home):
    handle = (home / "instance.lock").open("a+b")
    try:
        if sys.platform == "win32":
            import msvcrt
            handle.seek(0); handle.write(b"0"); handle.flush(); handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        handle.close()


async def serve(home, assets):
    home, assets = Path(home).resolve(), Path(assets).resolve()
    cfg = load(home)
    manifest = vm.verify_assets(assets)
    if manifest["architecture"] != vm.architecture(cfg):
        raise ValueError("Guest asset architecture does not match configured QEMU architecture")
    private_dir(home)
    handler = RotatingFileHandler(home / "service.log", maxBytes=2_000_000, backupCount=2)
    logging.basicConfig(handlers=[handler], level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    with lock(home):
        stop = home / "stop"
        stop.unlink(missing_ok=True)
        me = psutil.Process()
        write_initramfs(assets / "initramfs.gz", home / "session-initramfs.gz", cfg)
        gateway = None
        child = None
        reap = None
        awake = None
        loop = asyncio.get_running_loop()
        if sys.platform != "win32":
            # launchd sends SIGTERM on bootout. Request a graceful stop so the
            # owned QEMU child does not survive and retain the backend UDP port.
            loop.add_signal_handler(signal.SIGTERM, stop.touch)
        try:
            # Bind first: fail without starting a VM if another gateway owns this LAN port.
            gateway = await relay.start(cfg)
            atomic_json(home / "owner.json", {"pid": me.pid, "created": me.create_time()})
            reap = asyncio.create_task(gateway.reap())
            if sys.platform == "win32":
                ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)
            elif sys.platform == "darwin":
                awake = vm.popen(["/usr/bin/caffeinate", "-i", "-w", str(me.pid)])
            choices = vm.accelerators(cfg)
            index = 0
            last_health = 0
            while not stop.exists():
                if child is None or child.poll() is not None:
                    if child is not None:
                        logging.warning("Guest exited with %s", child.returncode)
                        index = min(index + 1, len(choices) - 1)
                        await asyncio.sleep(3)
                    accel = choices[index]
                    with (home / "guest.log").open("ab") as log:
                        child = vm.popen(vm.command(cfg, home, assets, accel), stdin=subprocess.DEVNULL,
                                         stdout=log, stderr=log)
                    logging.info("Guest started, accelerator %s", accel)
                if time.monotonic() - last_health > 15:
                    healthy = False
                    try:
                        healthy = await asyncio.to_thread(probe, cfg["listen_ip"], cfg["listen_port"], 2)
                    except (OSError, ValueError):
                        pass
                    atomic_json(home / "status.json", {"running": True,
                        "l2tp_ready": healthy, "guest_running": child.poll() is None,
                        "updated_at": datetime.datetime.now().astimezone().isoformat(),
                        "note": "Control handshake only; upstream and device usability are separate checks."})
                    last_health = time.monotonic()
                await asyncio.sleep(1)
        finally:
            if sys.platform != "win32":
                loop.remove_signal_handler(signal.SIGTERM)
            if reap:
                reap.cancel()
                await asyncio.gather(reap, return_exceptions=True)
            if gateway:
                await gateway.close()
            for proc in (child, awake):
                if proc and proc.poll() is None:
                    proc.terminate()
                    try:
                        proc.wait(timeout=8)
                    except subprocess.TimeoutExpired:
                        proc.kill(); proc.wait()
            if sys.platform == "win32":
                ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
            atomic_json(home / "status.json", {"running": False, "l2tp_ready": False})
            (home / "owner.json").unlink(missing_ok=True)
            (home / "session-initramfs.gz").unlink(missing_ok=True)
