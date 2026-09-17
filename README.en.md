# Proxy2VPN

[中文说明](README.md)

Share an existing HTTP CONNECT or SOCKS5 proxy on a Windows or macOS computer
through a router-compatible **plain L2TP** gateway. No router flashing, host
network bridging, or additional Ethernet cable is required.

```
Headset / TV / console -> Wi-Fi router -> Proxy2VPN -> your existing proxy
```

The router must support an L2TP client without mandatory IPsec. Device-based
routing is recommended: exclude the computer that runs the upstream proxy.
SOCKS5 can carry TCP and UDP when the upstream supports UDP ASSOCIATE. Ordinary
HTTP CONNECT carries TCP only; gateway DNS is forwarded using TCP.

## Early release

Windows x64 has passed end-to-end L2TP/PPP, HTTPS, DNS and UDP tests. The ARM64
guest has passed the same tests under QEMU emulation. Native macOS/HVF and real
device experience are **not yet verified**. See [validation](docs/validation.md).

Plain L2TP is not encrypted. Use only inside a trusted home LAN and never expose
its port to the Internet. This tool is not an Internet VPN provider or kill switch.

## Quick start

Install Python 3.11+ and [QEMU](https://www.qemu.org/download/). Docker Desktop is
needed only to build the clean guest, not to run the gateway.

```sh
python -m venv .venv
# Activate .venv using the command for your shell.
python -m pip install -e .
python scripts/build_guest.py --arch x86_64
# On Apple Silicon, use --arch aarch64 and artifacts/aarch64 below.
proxy2vpn init --listen-ip 192.168.50.10 --router-ip 192.168.50.1 --proxy-host 192.168.50.10 --proxy-port 7890
proxy2vpn up --assets artifacts/x86_64
proxy2vpn status
proxy2vpn doctor --assets artifacts/x86_64 --network
proxy2vpn router
```

Replace the example addresses. The last command displays locally generated
router credentials; configure them in your router's L2TP client. Use
`--proxy-type http` for HTTP CONNECT or `--proxy-auth` to privately prompt for
proxy credentials. Configuration is stored in `~/.proxy2vpn/config.json`.

For SOCKS5 UDP, prefer your computer's LAN address over loopback: some proxy
applications advertise a loopback UDP relay address that is inaccessible to the
Linux guest. Configure the existing application to accept the required local
connections. Proxy2VPN does not read subscriptions or modify the proxy app.

Stop with `proxy2vpn down`. Keep the computer awake and the upstream proxy running.
If needed, permit UDP 1701 only from your router through the host firewall.

## Development and licensing

```sh
python -m unittest discover -s tests -v
```

The host controller and original project code are MIT licensed. QEMU, Linux,
Mihomo and other third-party components retain their own licenses. This release
distributes source only; build guest assets locally. See
[third-party notices](THIRD_PARTY_NOTICES.md), [architecture](docs/architecture.md),
[security](SECURITY.md) and [contributing](CONTRIBUTING.md).
