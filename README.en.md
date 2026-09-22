# Proxy2VPN

[中文](README.md) · [Download installers](https://github.com/Yeqi99/proxy2vpn/releases/tag/v0.2.1)

Share an existing HTTP CONNECT or SOCKS5 proxy through a router VPN or an authenticated application proxy. Your computer and upstream proxy must stay running.

## Quick start

1. Extract the Windows x64, Apple Silicon macOS, or Intel macOS ZIP. Open `Install-Windows.cmd` or `Install-Mac.command`.
2. The installer prepares Python/QEMU, opens `http://127.0.0.1:18990/`, and enables current-user login startup. No Docker or manual guest build is needed. Installation requires internet access.
3. Enter the computer LAN IP, router IP and existing proxy address. Select protocols, save and start. Follow the built-in router/browser guide.

Closing the browser does not stop forwarding. The console supervises the gateway and retries failed processes. Stop is remembered across logins. First installation defaults login startup on; the console toggle saves immediately, and upgrades preserve your choice to disable it. Login startup is not a pre-login system service.

## Protocols

| Inbound | Default port | Client |
| --- | --- | --- |
| Plain L2TP (no IPsec) | UDP 1701 | Compatible stock router firmware, trusted LAN only |
| WireGuard | UDP 51820 | Compatible router; download its client configuration |
| HTTP / CONNECT | TCP 18080 | Browser/system proxy, generated credentials required |
| SOCKS5 | TCP 11080 | Apps supporting username/password authentication; TCP only |

Multiple inbounds may run together. VPN UDP requires upstream SOCKS5 UDP ASSOCIATE. HTTP upstreams carry TCP only; gateway DNS uses a TCP upstream. IPv6 and a kill switch are not provided. Do not expose ports to the internet. VPN listeners allow the configured router and local diagnostic address; HTTP/SOCKS listeners require authentication.

For browsers, choose HTTP: Chrome/Edge use system proxy settings; Firefox supports manual HTTP proxy settings for HTTP and HTTPS. Browser SOCKS authentication support is limited. Exclude the proxy host from router VPN device routing to avoid loops.

## Platform status

- Windows x64: clean installation, console, authenticated HTTP/SOCKS, real L2TP/PPP and WireGuard clients tested. Login registration/removal and QEMU crash recovery tested; a full reboot is not yet tested.
- Apple Silicon / Intel Mac: installers use Homebrew Python/QEMU and a user LaunchAgent. Homebrew/Command Line Tools may require a password or OS confirmation. Real Mac installation, HVF, reboot and sleep recovery remain unverified. ARM64 emulation is not Mac validation.

Private state lives under `~/.proxy2vpn`. The console binds loopback only and requires a local token with Host/Origin validation. The installer opens an authenticated URL; Windows gets desktop and Start menu shortcuts; Mac gets a desktop Proxy2VPN.command launcher. Shortcuts start the console if necessary without changing login-startup preferences. Direct visits require the token in `console.token`.

To retire an installation, stop forwarding and disable login startup, disconnect the router VPN, then close the console process and remove the application directory. Keep the private state directory if you need its credentials. Disabling Mac startup takes effect at the next login and keeps the current session running. Shared Homebrew dependencies are not automatically removed.

## Development and licenses

Use Python 3.11+, `python -m pip install -e .` and `python -m unittest discover -s tests -v`. Guest builds require Docker. See [contributing](CONTRIBUTING.md), [architecture](docs/architecture.md), [validation](docs/validation.md), and [security](SECURITY.md).

Original code is MIT licensed. Third-party components retain their licenses. Binary releases include a corresponding-source archive; see [notices](THIRD_PARTY_NOTICES.md).
