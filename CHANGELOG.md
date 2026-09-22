# Changelog

## 0.2.0 — 2026-09-22

- Windows installer and macOS Intel/Apple Silicon installer packages.
- Authenticated loopback WebUI, configuration, start/stop, login startup, tests and tutorials.
- WireGuard VPN, authenticated HTTP and SOCKS5 TCP ingress alongside L2TP.
- Persistent gateway manager, private settings and background process restart.
- Prebuilt guests with exact Alpine recipes and corresponding source companion.
- Native macOS installation/HVF and whole-machine reboot remain unverified.

## 0.1.0 — 2026-09-17

- Initial source release: configurable plain-L2TP-to-SOCKS5/HTTP gateway.
- Stateless Linux guest builds for x86_64 and ARM64; fixed Mihomo release hashes.
- Windows WHPX / macOS HVF selection with TCG fallback.
- Source-restricted UDP listener, Windows UDP reset handling, generated PPP credentials.
- Background start/stop/status, upstream diagnostics and real QEMU PPP integration client.
- Windows and macOS launchers, MIT source license and third-party notices.
- macOS hardware, sleep/reboot recovery and end-device experience remain unverified.
