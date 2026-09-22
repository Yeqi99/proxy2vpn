"""Render guest files as JSON (also valid YAML) and a Linux newc archive."""
import gzip
import ipaddress
import json
import stat
from .config import validate


def guest_files(cfg):
    validate(cfg)
    net = ipaddress.IPv4Network(cfg["subnet"])
    gateway, first, last = map(str, (net[1], net[2], net[10]))
    proxy = cfg["proxy"]
    host = "10.0.2.2" if ipaddress.ip_address(proxy["host"]).is_loopback else proxy["host"]
    upstream = {"name": "upstream", "type": proxy["type"], "server": host, "port": proxy["port"]}
    if proxy["type"] == "socks5":
        upstream["udp"] = proxy["udp"]
    if proxy.get("username"):
        upstream.update(username=proxy["username"], password=proxy.get("password", ""))
    mihomo = {"log-level": "warning", "ipv6": False, "allow-lan": False,
        "tun": {"enable": True, "device": "p2v", "stack": "gvisor", "mtu": 1500,
                "auto-route": False, "auto-detect-interface": False},
        "dns": {"enable": True, "listen": f"{gateway}:53", "ipv6": False,
                "enhanced-mode": "redir-host", "respect-rules": True,
                "nameserver": ["tcp://1.1.1.1:53", "tcp://8.8.8.8:53"],
                "proxy-server-nameserver": ["1.1.1.1"]},
        "proxies": [upstream], "rules": ["MATCH,upstream"]}
    if 'http' in cfg['protocols'] or 'socks5' in cfg['protocols']:
        mihomo.update({'allow-lan': True, 'bind-address': '*', 'authentication': [cfg['username']+':'+cfg['password']]})
        if 'http' in cfg['protocols']: mihomo['port'] = 8080
        if 'socks5' in cfg['protocols']: mihomo['socks-port'] = 1080
    files = {
        "etc/mihomo/config.yaml": json.dumps(mihomo, indent=2) + "\n",
        "etc/xl2tpd/xl2tpd.conf": f"""[global]
port = 1701
access control = no
[lns default]
ip range = {first}-{last}
local ip = {gateway}
require authentication = yes
refuse pap = yes
require chap = yes
name = proxy2vpn
pppoptfile = /etc/ppp/options.proxy2vpn
length bit = yes
""",
        "etc/ppp/options.proxy2vpn": f"""auth
name proxy2vpn
mtu {cfg['mtu']}
mru {cfg['mtu']}
ms-dns {gateway}
asyncmap 0
hide-password
lcp-echo-interval 20
lcp-echo-failure 3
noccp
noipv6
nodefaultroute
noipdefault
""",
        "etc/ppp/chap-secrets": f'{cfg["username"]} proxy2vpn "{cfg["password"]}" *\n',
        "etc/proxy2vpn.env": f"GATEWAY={gateway}\nSUBNET={net}\nUDP_ENABLED={int(proxy['udp'])}\nL2TP_ENABLED={int('l2tp' in cfg['protocols'])}\nWG_ENABLED={int('wireguard' in cfg['protocols'])}\nWG_CLIENT={net[20]}\n",
    }
    if 'wireguard' in cfg['protocols']:
        keys = cfg['wireguard']
        import base64
        for key in keys.values():
            if len(base64.b64decode(key, validate=True)) != 32: raise ValueError('Invalid WireGuard key')
        files['etc/wireguard/wg0.conf'] = f"[Interface]\nPrivateKey = {keys['private']}\nListenPort = 51820\n\n[Peer]\nPublicKey = {keys['client_public']}\nAllowedIPs = {net[20]}/32\n"
    return files


def cpio(files, executable=()):
    """Only relative regular files; reject traversal before creating initramfs."""
    result = bytearray()
    directories = set()
    for name in files:
        if name.startswith("/") or ".." in name.split("/") or "\\" in name or "\0" in name:
            raise ValueError("Unsafe archive path")
        parts = name.split("/")
        directories.update("/".join(parts[:i]) for i in range(1, len(parts)))
    entries = [(d, b"", stat.S_IFDIR | 0o700) for d in sorted(directories, key=lambda n: (n.count('/'), n))]
    entries += [(name, content.encode() if isinstance(content, str) else content,
                 stat.S_IFREG | (0o700 if name in executable else 0o600))
                for name, content in sorted(files.items())]
    entries.append(("TRAILER!!!", b"", 0))
    for ino, (name, data, mode) in enumerate(entries, 1):
        encoded = name.encode() + b"\0"
        fields = [ino, mode, 0, 0, 1, 0, len(data), 0, 0, 0, 0, len(encoded), 0]
        result.extend(b"070701" + ''.join(f"{n:08x}" for n in fields).encode() + encoded)
        result.extend(b"\0" * (-len(result) % 4))
        result.extend(data)
        result.extend(b"\0" * (-len(result) % 4))
    return bytes(result)


def write_initramfs(base, output, cfg):
    # Linux supports concatenated compressed newc archives. No writable guest disk.
    with output.open("wb") as target:
        target.write(base.read_bytes())
        target.write(gzip.compress(cpio(guest_files(cfg)), mtime=0))
