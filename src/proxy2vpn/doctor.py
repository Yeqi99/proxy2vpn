"""Diagnostics return separate local-port, HTTPS and L2TP evidence."""
import json
import shutil
import socket
import subprocess
from . import vm
from .probe import probe


def inspect(cfg, assets, network=False):
    results = {}
    for name, action in {
        "qemu": lambda: vm.binary(cfg),
        "guest_assets": lambda: vm.verify_assets(assets)["architecture"],
        "proxy_tcp": lambda: tcp(cfg["proxy"]["host"], cfg["proxy"]["port"]),
        "l2tp": lambda: probe(cfg["listen_ip"], cfg["listen_port"]),
    }.items():
        try:
            results[name] = {"ok": True, "detail": action()}
        except (OSError, ValueError, KeyError) as error:
            results[name] = {"ok": False, "detail": str(error)}
    if network:
        try:
            results["proxy_https"] = {"ok": True, "detail": https(cfg)}
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            results["proxy_https"] = {"ok": False, "detail": str(error)}
    results["udp"] = {"enabled": cfg["proxy"]["udp"],
                      "note": "Requires SOCKS5 UDP ASSOCIATE and a relay address reachable from the guest. Not tested by TCP checks."}
    return results


def tcp(host, port):
    with socket.create_connection((host, port), timeout=3):
        return "TCP connection accepted (not an Internet test)"


def https(cfg):
    curl = shutil.which("curl")
    if not curl:
        raise OSError("curl is required for --network HTTPS diagnostics")
    p = cfg["proxy"]
    scheme = "socks5h" if p["type"] == "socks5" else "http"
    settings = [f'proxy = "{scheme}://{p["host"]}:{p["port"]}"', 'noproxy = ""']
    if p.get("username"):
        credential = p["username"] + ":" + p.get("password", "")
        if any(c in credential for c in "\r\n\0"):
            raise ValueError("Proxy credentials contain unsupported control characters")
        settings.append("proxy-user = " + json.dumps(credential))
    # Credentials travel through stdin, never argv or the report.
    response = subprocess.run([curl, "--config", "-", "--silent", "--show-error",
        "--max-time", "15", "--output", "NUL" if __import__('os').name == 'nt' else "/dev/null",
        "--write-out", "%{http_code}", "https://www.gstatic.com/generate_204"],
        input="\n".join(settings), text=True, capture_output=True, timeout=20)
    if response.returncode or response.stdout != "204":
        raise ValueError(f"HTTPS test failed (curl={response.returncode}, HTTP={response.stdout[:3]})")
    return "HTTPS 204 via configured upstream (not through L2TP)"
