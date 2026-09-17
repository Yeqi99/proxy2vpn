"""Bounded, unauthenticated L2TP control-plane health check; no user payload."""
import secrets
import socket
import struct


def avp(kind, payload):
    return struct.pack("!HHH", 0x8000 | (len(payload) + 6), 0, kind) + payload


def packet(tunnel, sequence, received, attributes):
    body = b"".join(attributes)
    return struct.pack("!6H", 0xC802, len(body) + 12, tunnel, 0, sequence, received) + body


def probe(address, port=1701, timeout=3):
    tid = secrets.randbelow(65534) + 1
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((address, 0))
        sock.settimeout(timeout)
        target = (address, port)
        sock.sendto(packet(0, 0, 0, [avp(0, b"\x00\x01"), avp(2, b"\x01\x00"),
            avp(3, b"\x00\x00\x00\x03"), avp(7, b"Proxy2VPNProbe"),
            avp(9, struct.pack("!H", tid)), avp(10, b"\x00\x04")]), target)
        response, peer = sock.recvfrom(4096)
        if peer != target or len(response) < 12:
            raise ValueError("Invalid L2TP response source/header")
        flags, length, returned_tid, session, ns, nr = struct.unpack("!6H", response[:12])
        if flags != 0xC802 or session != 0 or returned_tid != tid or nr != 1 or length != len(response):
            raise ValueError("Invalid SCCRP header")
        attrs, offset = {}, 12
        while offset < len(response):
            if offset + 6 > len(response):
                raise ValueError("Truncated SCCRP AVP")
            size, vendor, kind = struct.unpack("!3H", response[offset:offset+6])
            size &= 1023
            if size < 6 or offset + size > len(response):
                raise ValueError("Invalid SCCRP AVP")
            if vendor == 0:
                attrs[kind] = response[offset+6:offset+size]
            offset += size
        if attrs.get(0) != b"\x00\x02":
            raise ValueError("Expected SCCRP")
        if len(attrs.get(9, b"")) != 2:
            raise ValueError("Missing tunnel ID")
        server_tid = struct.unpack("!H", attrs[9])[0]
        sock.sendto(packet(server_tid, 1, ns+1, [avp(0, b"\x00\x03")]), target)
        sock.sendto(packet(server_tid, 2, ns+1, [avp(0, b"\x00\x04"),
            avp(9, struct.pack("!H", tid)), avp(1, b"\x00\x01")]), target)
        return True
