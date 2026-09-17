"""LAN L2TP ingress with a strict source-IP allowlist and per-peer UDP mappings.

No host route, VPN adapter, or subscription access is required. Plain L2TP is for
the trusted home LAN only. The router must never forward this port from WAN.
"""
import asyncio
import ctypes
import logging
import socket
import sys
import time

def udp_socket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setblocking(False)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 * 1024 * 1024)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024 * 1024)
    # Windows translates an ICMP port-unreachable (e.g. a finished probe) into
    # WSAECONNRESET on UDP recv. Proactor transports can then stop receiving.
    # UDP has no connection to reset: retain the listener when a peer closes.
    if sys.platform == "win32":
        # CPython exposes only a subset of Winsock ioctls; invoke WSAIoctl
        # explicitly rather than silently skipping this protection.
        ws2 = ctypes.WinDLL("ws2_32", use_last_error=True)
        ioctl = ws2.WSAIoctl
        ioctl.argtypes = [ctypes.c_size_t, ctypes.c_uint32, ctypes.c_void_p,
                          ctypes.c_uint32, ctypes.c_void_p, ctypes.c_uint32,
                          ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
        ioctl.restype = ctypes.c_int
        enabled = ctypes.c_uint32(0)
        returned = ctypes.c_uint32(0)
        if ioctl(sock.fileno(), 0x9800000C, ctypes.byref(enabled), 4,
                 None, 0, ctypes.byref(returned), None, None) != 0:
            sock.close()
            raise OSError(ws2.WSAGetLastError(), "Could not disable UDP connection-reset behavior")
    return sock


class Backend(asyncio.DatagramProtocol):
    def __init__(self, owner, peer):
        self.owner, self.peer, self.last = owner, peer, time.monotonic()

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        self.last = time.monotonic()
        self.owner.transport.sendto(data, self.peer)

    def error_received(self, exc):
        logging.warning("Backend UDP error for %s: %s", self.peer, exc)


class Frontend(asyncio.DatagramProtocol):
    def __init__(self, allowed, backend=("127.0.0.1", 17010)):
        self.allowed, self.peers, self.pending = set(allowed), {}, set()
        self.backend = backend
        self.tasks = set()

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        if addr[0] not in self.allowed or len(data) < 6 or len(data) > 4096:
            return
        peer = self.peers.get(addr)
        if peer:
            peer.last = time.monotonic()
            peer.transport.sendto(data, self.backend)
        elif addr not in self.pending and len(self.peers) + len(self.pending) < 64:
            self.pending.add(addr)
            task = asyncio.create_task(self.add_peer(addr, data))
            self.tasks.add(task)
            task.add_done_callback(self.tasks.discard)

    async def add_peer(self, addr, data):
        try:
            sock = udp_socket()
            sock.connect(self.backend)
            _, peer = await asyncio.get_running_loop().create_datagram_endpoint(
                lambda: Backend(self, addr), sock=sock)
            self.peers[addr] = peer
            peer.transport.sendto(data, self.backend)
            logging.info("L2TP peer %s:%s", *addr)
        except Exception:
            logging.exception("Cannot create relay mapping")
        finally:
            self.pending.discard(addr)

    def error_received(self, exc):
        logging.warning("LAN UDP error: %s", exc)

    async def reap(self):
        while True:
            await asyncio.sleep(30)
            for addr, peer in list(self.peers.items()):
                if time.monotonic() - peer.last > 180:
                    peer.transport.close()
                    del self.peers[addr]


    async def close(self):
        for task in list(self.tasks):
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        for peer in self.peers.values():
            peer.transport.close()
        self.transport.close()


async def start(cfg):
    sock = udp_socket()
    sock.bind((cfg["listen_ip"], cfg["listen_port"]))
    _, protocol = await asyncio.get_running_loop().create_datagram_endpoint(
        lambda: Frontend([cfg["router_ip"], cfg["listen_ip"]], ("127.0.0.1", cfg["backend_port"])),
        sock=sock)
    logging.info("L2TP listening on %s:%s", cfg["listen_ip"], cfg["listen_port"])
    return protocol
