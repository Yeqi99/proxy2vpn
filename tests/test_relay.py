import asyncio
import unittest
from proxy2vpn.relay import Frontend, udp_socket


class Echo(asyncio.DatagramProtocol):
    def connection_made(self, transport): self.transport = transport
    def datagram_received(self, data, addr): self.transport.sendto(data, addr)


class RelayTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        loop = asyncio.get_running_loop()
        self.back, _ = await loop.create_datagram_endpoint(Echo, local_addr=("127.0.0.1", 0))
        self.backend = self.back.get_extra_info("sockname")
        sock = udp_socket(); sock.bind(("127.0.0.1", 0))
        self.address = sock.getsockname()
        _, self.relay = await loop.create_datagram_endpoint(lambda: Frontend(["127.0.0.1"], self.backend), sock=sock)

    async def asyncTearDown(self):
        await self.relay.close(); self.back.close()
        await asyncio.sleep(0)

    async def exchange(self, payload):
        loop = asyncio.get_running_loop()
        sock = udp_socket(); sock.bind(("127.0.0.1", 0))
        try:
            await loop.sock_sendto(sock, payload, self.address)
            return await asyncio.wait_for(loop.sock_recvfrom(sock, 4096), 1)
        finally:
            sock.close()

    async def test_multiple_closed_udp_peers(self):
        for n in range(8):
            data = f"packet-{n}".encode()
            actual, _ = await self.exchange(data)
            self.assertEqual(actual, data)

    async def test_source_allowlist(self):
        self.relay.allowed = {"192.168.50.1"}
        with self.assertRaises(asyncio.TimeoutError): await self.exchange(b"blocked-packet")
        self.assertEqual(len(self.relay.peers), 0)

    async def test_packet_limit(self):
        with self.assertRaises(asyncio.TimeoutError): await self.exchange(b"x" * 4097)
        self.assertEqual(len(self.relay.peers), 0)
