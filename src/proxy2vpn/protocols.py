"""Backward-compatible ingress settings and locally generated WireGuard keys."""
import base64
import ipaddress
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, PublicFormat, NoEncryption


def keypair():
    key = X25519PrivateKey.generate()
    return (base64.b64encode(key.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())).decode(),
            base64.b64encode(key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)).decode())


def defaults(cfg):
    cfg.setdefault("protocols", ["l2tp"])
    cfg.setdefault("wireguard_port", 51820)
    cfg.setdefault("wireguard_backend_port", 51821)
    cfg.setdefault("http_port", 18080)
    cfg.setdefault("socks_port", 11080)
    return cfg


def ensure_keys(cfg):
    if "wireguard" in cfg["protocols"] and not cfg.get("wireguard"):
        private, public = keypair()
        client_private, client_public = keypair()
        cfg["wireguard"] = dict(private=private, public=public, client_private=client_private, client_public=client_public)


def client_config(cfg):
    keys = cfg["wireguard"]
    subnet = ipaddress.ip_network(cfg["subnet"])
    return f'''[Interface]
PrivateKey = {keys['client_private']}
Address = {subnet[20]}/32
DNS = {subnet[1]}
MTU = {cfg['mtu']}

[Peer]
PublicKey = {keys['public']}
AllowedIPs = 0.0.0.0/0
Endpoint = {cfg['listen_ip']}:{cfg['wireguard_port']}
PersistentKeepalive = 25
'''
