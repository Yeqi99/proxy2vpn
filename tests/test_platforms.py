from pathlib import Path
import unittest
from unittest.mock import patch
from proxy2vpn import vm
from proxy2vpn.config import new_config


class PlatformTests(unittest.TestCase):
    def setUp(self): self.cfg = new_config("192.168.50.10", "192.168.50.1", "192.168.50.10", 7890)

    @patch("proxy2vpn.vm.platform.machine", return_value="arm64")
    @patch("proxy2vpn.vm.sys.platform", "darwin")
    def test_apple_silicon_uses_arm_hvf(self, _):
        self.assertEqual(vm.architecture(self.cfg), "aarch64")
        self.assertEqual(vm.accelerators(self.cfg)[0], "hvf")
        with patch("proxy2vpn.vm.binary", return_value="qemu-system-aarch64"):
            cmd = vm.command(self.cfg, Path("home"), Path("assets"), "hvf")
        self.assertIn("virt", cmd); self.assertIn("host", cmd)
        self.assertIn("rdinit=/init console=ttyAMA0 panic=5", cmd)

    @patch("proxy2vpn.vm.platform.machine", return_value="AMD64")
    @patch("proxy2vpn.vm.sys.platform", "win32")
    def test_windows_acceleration_fallback(self, _):
        self.assertEqual(vm.accelerators(self.cfg), ["whpx,kernel-irqchip=off", "tcg,thread=multi"])

    @patch("proxy2vpn.vm.platform.machine", return_value="arm64")
    @patch("proxy2vpn.vm.sys.platform", "darwin")
    def test_cross_arch_forces_emulation(self, _):
        self.cfg["architecture"] = "x86_64"
        self.assertEqual(vm.accelerators(self.cfg), ["tcg,thread=multi"])
