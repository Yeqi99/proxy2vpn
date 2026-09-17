"""Validated local configuration. Never reads a proxy subscription or profile."""
import ipaddress
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys


def private_dir(path):
    path = Path(path).resolve()
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if sys.platform == "win32":
        # Resolve the current SID, avoiding localized account names and ACLs.
        sid = subprocess.check_output(["whoami", "/user", "/fo", "csv", "/nh"], text=True)
        sid = re.search(r"S-1-5-[0-9-]+", sid).group()
        subprocess.run(["icacls", str(path), "/inheritance:r", "/grant:r", f"*{sid}:(OI)(CI)F"],
                       check=True, stdout=subprocess.DEVNULL)
    else:
        path.chmod(0o700)
    return path


def new_config(listen, router, proxy_host, proxy_port, kind="socks5"):
    return {"listen_ip": listen, "router_ip": router, "listen_port": 1701,
            "backend_port": 17010, "subnet": "10.77.0.0/24", "mtu": 1360,
            "username": "proxy2vpn", "password": secrets.token_urlsafe(24),
            "proxy": {"type": kind, "host": proxy_host, "port": proxy_port,
                      "udp": kind == "socks5", "username": "", "password": ""},
            "architecture": "auto", "qemu": "", "memory_mb": 768}


def validate(cfg):
    for key in ("listen_ip", "router_ip"):
        addr = ipaddress.IPv4Address(cfg[key])
        if not addr.is_private or addr.is_unspecified or addr.is_multicast:
            raise ValueError(f"{key} must be a private unicast IPv4 address")
    for key in ("listen_port", "backend_port"):
        if type(cfg[key]) is not int or not 1024 <= cfg[key] <= 65535:
            raise ValueError(f"{key} must be a port between 1024 and 65535")
    if cfg["listen_port"] == cfg["backend_port"]:
        raise ValueError("LAN and internal UDP ports must differ")
    subnet = ipaddress.IPv4Network(cfg["subnet"])
    if subnet.prefixlen != 24 or not subnet.is_private:
        raise ValueError("subnet must be a private /24")
    for address in (cfg["listen_ip"], cfg["router_ip"], "10.0.2.2"):
        if ipaddress.IPv4Address(address) in subnet:
            raise ValueError("VPN subnet overlaps host/router/QEMU network")
    for key in ("username", "password"):
        if not isinstance(cfg[key], str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", cfg[key]):
            raise ValueError(f"{key} must contain only letters, digits, underscore or hyphen")
    if len(cfg["password"]) < 16:
        raise ValueError("VPN password must have at least 16 characters")
    proxy = cfg["proxy"]
    if proxy["type"] not in ("http", "socks5"):
        raise ValueError("proxy.type must be http or socks5")
    # An IP avoids proxy bootstrap DNS ambiguity; loopback means the host alias.
    proxy_addr = ipaddress.IPv4Address(proxy["host"])
    if proxy_addr.is_unspecified or proxy_addr.is_multicast or proxy_addr in subnet:
        raise ValueError("Proxy address must be unicast and outside the VPN subnet")
    if type(proxy["port"]) is not int or not 1 <= proxy["port"] <= 65535:
        raise ValueError("Invalid proxy port")
    if type(proxy["udp"]) is not bool:
        raise ValueError("proxy.udp must be a boolean")
    if proxy["type"] == "http" and proxy["udp"]:
        raise ValueError("HTTP CONNECT cannot carry general UDP; set proxy.udp=false")
    for key in ("username", "password"):
        if not isinstance(proxy.get(key, ""), str):
            raise ValueError(f"proxy.{key} must be text")
    if not 1200 <= cfg["mtu"] <= 1460:
        raise ValueError("mtu must be 1200..1460")
    if cfg["architecture"] not in ("auto", "x86_64", "aarch64"):
        raise ValueError("Unsupported guest architecture")
    if not 512 <= cfg["memory_mb"] <= 4096:
        raise ValueError("memory_mb must be 512..4096")
    return cfg


def load(home):
    return validate(json.loads((Path(home) / "config.json").read_text(encoding="utf-8")))


def save(home, cfg):
    validate(cfg)
    home = private_dir(home)
    path = home / "config.json"
    if path.exists():
        raise FileExistsError("Configuration already exists; edit it instead of replacing credentials")
    with path.open("x", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")
    if os.name != "nt":
        path.chmod(0o600)
