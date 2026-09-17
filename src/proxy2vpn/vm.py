"""QEMU direct Linux boot: no host routing changes or privileged containers."""
import hashlib
import json
import platform
from pathlib import Path
import shutil
import subprocess
import sys


def architecture(cfg):
    if cfg["architecture"] != "auto":
        return cfg["architecture"]
    return "aarch64" if platform.machine().lower() in ("arm64", "aarch64") else "x86_64"


def binary(cfg):
    if cfg["qemu"]:
        path = Path(cfg["qemu"])
        if not path.is_file():
            raise FileNotFoundError("Configured QEMU executable not found")
        return str(path.resolve())
    name = "qemu-system-" + architecture(cfg)
    found = shutil.which(name)
    if not found:
        raise FileNotFoundError(f"{name} not found. Install QEMU and add it to PATH or set config.qemu")
    return found


def verify_assets(directory):
    directory = Path(directory)
    manifest = json.loads((directory / "manifest.json").read_text())
    for name in ("vmlinuz", "initramfs.gz"):
        digest = hashlib.sha256((directory / name).read_bytes()).hexdigest()
        if digest != manifest["sha256"][name]:
            raise ValueError(f"Guest asset checksum mismatch: {name}")
    return manifest


def accelerators(cfg):
    arch = architecture(cfg)
    native = (platform.machine().lower() in ("arm64", "aarch64")) == (arch == "aarch64")
    if sys.platform == "win32" and arch == "x86_64" and native:
        return ["whpx,kernel-irqchip=off", "tcg,thread=multi"]
    if sys.platform == "darwin" and native:
        return ["hvf", "tcg,thread=multi"]
    return ["tcg,thread=multi"]


def command(cfg, home, assets, accel):
    arch = architecture(cfg)
    arm = arch == "aarch64"
    cpu = "host" if accel == "hvf" else "max"
    args = [binary(cfg), "-name", "Proxy2VPN", "-machine", "virt" if arm else "q35",
            "-accel", accel, "-smp", "2", "-m", str(cfg["memory_mb"]),
            "-display", "none", "-monitor", "none", "-serial", "stdio", "-no-reboot",
            "-kernel", str(assets / "vmlinuz"), "-initrd", str(home / "session-initramfs.gz"),
            "-append", "rdinit=/init console=" + ("ttyAMA0" if arm else "ttyS0") + " panic=5",
            "-netdev", f'user,id=wan,hostfwd=udp:127.0.0.1:{cfg["backend_port"]}-:1701',
            "-device", "virtio-net-pci,netdev=wan"]
    if arm:
        args.extend(["-cpu", cpu])
    return args


def popen(args, **kwargs):
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    return subprocess.Popen(args, **kwargs)
