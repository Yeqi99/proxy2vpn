# Architecture

```
Router L2TP client
    | UDP (LAN address, router-only allowlist)
Python UDP relay on Windows/macOS
    | one localhost UDP mapping per router peer
QEMU user networking / SLIRP
    | UDP 1701 inside the guest
xl2tpd -> pppd -> PPP IPv4 packets
    | source-policy routing table 177
Mihomo TUN (gVisor) -> SOCKS5 / HTTP CONNECT -> existing proxy application
```

## Why a small VM

L2TP carries PPP/IP traffic, whereas HTTP and SOCKS are application proxy
protocols. A byte-forwarding TCP server cannot translate between them. The guest
uses established implementations: xl2tpd/pppd for VPN termination and Mihomo for
IP-to-proxy translation. QEMU gives both Windows and macOS a Linux kernel with
PPP/TUN support, independent of Docker Desktop's kernel and networking limits.

Docker is used only as a clean guest builder. The runtime boots a Linux kernel
and compressed initramfs directly. No disk installation, shared home directory,
SSH password or administrator-level host interface is needed. Generated config
is a second newc archive appended to the clean initramfs and stays host-private.

## Routing

Only packets from the configured VPN subnet use the TUN routing table. A
higher-priority destination rule retains access to PPP peers, including DNS
replies. The guest's own proxy connections keep its QEMU default route, avoiding
a recursive proxy route. Guest FORWARD is DROP except PPP↔TUN traffic. HTTP mode
explicitly rejects general forwarded UDP. Gateway DNS uses TCP upstream through
the proxy; DNS requests to other servers require SOCKS5 UDP support.

The host default route, DNS settings and adapters are not changed. The router
must exclude the computer running the upstream proxy from its VPN policy.

## Lifecycle and diagnostics

The host supervisor owns only the QEMU process it starts; shutdown never kills
other QEMU instances. A per-home OS file lock prevents duplicate supervisors.
Process ownership includes creation time to avoid stale PID reuse. There are no
fixed machine/user paths in source.

L2TP health probes establish and tear down a control tunnel without PPP
credentials. This confirms the listener and LNS, not Internet access. A separate
disposable QEMU integration client authenticates PPP and sends HTTPS, DNS and
UDP packets through the whole chain. Neither substitutes for actual headset or
game testing.

On Windows the UDP socket disables `SIO_UDP_CONNRESET` through Winsock WSAIoctl.
A closed diagnostic client otherwise can cause an ICMP port-unreachable to stop
the Proactor receive loop. Peer mappings are capped and expire after inactivity.

## References

- [QEMU direct Linux boot](https://www.qemu.org/docs/master/system/linuxboot.html)
- [Linux initramfs buffer format](https://www.kernel.org/doc/Documentation/early-userspace/buffer-format.txt)
- [Mihomo SOCKS5](https://wiki.metacubex.one/en/config/proxies/socks/)
- [Mihomo HTTP](https://wiki.metacubex.one/en/config/proxies/http/)
- [Winsock IOCTLs](https://learn.microsoft.com/en-us/windows/win32/winsock/winsock-ioctls)
