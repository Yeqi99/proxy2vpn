# Security

Proxy2VPN is a trusted-LAN compatibility bridge, not a public VPN service.

The v0.2 console binds to 127.0.0.1, authenticates API calls with a local random
token, rejects mismatched Host/Origin, and accepts bounded JSON mutation requests.
Status/config reads redact passwords and WireGuard keys. Explicit credential
display and client export require authentication. Do not expose this console
through a reverse proxy. Local processes running as the same user remain trusted.

WireGuard provides encrypted VPN ingress. HTTP/SOCKS ingress requires the generated
username/password but does not encrypt the LAN authentication exchange; use only
a trusted LAN. The SOCKS ingress currently supports TCP only. WireGuard exports
one client key: do not reuse that file on simultaneously active routers.

- Plain L2TP does not encrypt packets. CHAP authenticates a PPP session but does
  not encrypt it. Use only a trusted LAN. Never forward its UDP port from WAN.
- The UDP listener permits the configured router and local diagnostic address.
  IP allowlists do not prevent spoofing by another LAN participant.
- The guest has no SSH server, web administration port, or writable persistent
  disk. Credentials are generated locally and injected into a private initramfs.
- Host-private configuration contains proxy and VPN passwords. Do not attach
  `.proxy2vpn`, logs, dumps, generated initramfs files or router screenshots to
  public issues. Diagnostic commands must not print subscriptions or passwords.
- Guest DNS goes through the configured proxy. IPv6 is not routed by this tool;
  the router/device might use another path. This is not a kill switch.
- VM forwarding defaults to DROP. There is no direct Internet fallback for PPP
  traffic if the proxy fails; router failover outside the VM is router-dependent.
- The software does not change host firewall policy. Permit only the router's
  source IP to the configured L2TP UDP port when a firewall rule is necessary.
- Build only from trusted source. Local asset checksums detect corruption, not
  a malicious replacement of both an image and its manifest.

Do not put exploit details containing private credentials in public issues. For
a repository with GitHub private vulnerability reporting enabled, use that
mechanism; otherwise contact its maintainer before sharing sensitive details.
