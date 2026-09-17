import json
import unittest
from proxy2vpn.config import new_config, validate
from proxy2vpn.render import guest_files, cpio


class ConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.cfg = new_config("192.168.50.10", "192.168.50.1", "192.168.50.10", 7890)

    def test_password_randomized(self):
        other = new_config("192.168.50.10", "192.168.50.1", "192.168.50.10", 7890)
        self.assertNotEqual(self.cfg["password"], other["password"])

    def test_public_listener_rejected(self):
        self.cfg["listen_ip"] = "8.8.8.8"
        with self.assertRaises(ValueError): validate(self.cfg)

    def test_subnet_collision_rejected(self):
        self.cfg["subnet"] = "192.168.50.0/24"
        with self.assertRaises(ValueError): validate(self.cfg)

    def test_qemu_network_collision_rejected(self):
        self.cfg["subnet"] = "10.0.2.0/24"
        with self.assertRaises(ValueError): validate(self.cfg)

    def test_ppp_injection_rejected(self):
        self.cfg["username"] = 'user\nnoauth'
        with self.assertRaises(ValueError): guest_files(self.cfg)

    def test_http_udp_rejected(self):
        self.cfg["proxy"]["type"] = "http"
        with self.assertRaises(ValueError): validate(self.cfg)

    def test_http_dns_over_tcp(self):
        self.cfg["proxy"].update(type="http", udp=False)
        rendered = json.loads(guest_files(self.cfg)["etc/mihomo/config.yaml"])
        self.assertTrue(all(n.startswith("tcp://") for n in rendered["dns"]["nameserver"]))
        self.assertNotIn("udp", rendered["proxies"][0])

    def test_proxy_credentials_cannot_inject_yaml(self):
        self.cfg["proxy"].update(username='x\nallow-lan: true', password='"\\')
        rendered = json.loads(guest_files(self.cfg)["etc/mihomo/config.yaml"])
        self.assertFalse(rendered["allow-lan"])
        self.assertEqual(rendered["proxies"][0]["username"], self.cfg["proxy"]["username"])

    def test_loopback_maps_to_host_alias(self):
        self.cfg["proxy"]["host"] = "127.0.0.1"
        rendered = json.loads(guest_files(self.cfg)["etc/mihomo/config.yaml"])
        self.assertEqual(rendered["proxies"][0]["server"], "10.0.2.2")

    def test_archive_traversal_rejected(self):
        for path in ("../secret", "/etc/passwd", "etc/../../secret", "etc\\secret"):
            with self.assertRaises(ValueError): cpio({path: "x"})

    def test_cpio_format_and_credentials(self):
        files = guest_files(self.cfg)
        data = cpio(files)
        decoded = {}
        offset = 0
        while data[offset:offset+6] == b"070701":
            header = data[offset:offset+110]
            values = [int(header[6+i*8:14+i*8], 16) for i in range(13)]
            name = data[offset+110:offset+110+values[11]-1].decode()
            offset = (offset+110+values[11]+3) & ~3
            decoded[name] = data[offset:offset+values[6]]
            offset = (offset+values[6]+3) & ~3
        self.assertEqual(decoded["etc/ppp/chap-secrets"].decode(), files["etc/ppp/chap-secrets"])
        self.assertIn("TRAILER!!!", decoded)


if __name__ == "__main__": unittest.main()
