import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from proxy2vpn import autostart, shortcuts


class StartupTests(unittest.TestCase):
    def test_first_install_defaults_on(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertTrue(autostart.preference(Path(tmp)))

    def test_upgrade_preserves_saved_off(self):
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp)
            (home/'startup.json').write_text('{"enabled":false}')
            with patch.object(autostart,'enabled',return_value=True):
                self.assertFalse(autostart.preference(home,installed=True))

    def test_old_install_preserves_actual_disabled(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(autostart,'enabled',return_value=False):
            self.assertFalse(autostart.preference(Path(tmp),installed=True))

    def test_shortcut_never_reenables_startup(self):
        with tempfile.TemporaryDirectory() as tmp, patch('proxy2vpn.setup.main') as setup:
            home=Path(tmp)
            (home/'installation.json').write_text(json.dumps({'assets':'assets','qemu':'qemu','port':19091}))
            shortcuts.open_console(home,browser=False)
            args=setup.call_args.args[0]
            self.assertIn('--launch-only',args)
            self.assertEqual(args[args.index('--port')+1],'19091')

    def test_mac_shortcut_quotes_paths_and_is_executable(self):
        with tempfile.TemporaryDirectory(prefix='proxy folder ') as tmp:
            home=Path(tmp)
            (home/'private settings').mkdir()
            with patch.object(shortcuts.sys,'platform','darwin'), patch.object(Path,'home',return_value=home):
                shortcuts.create(home/'private settings')
            shortcut=home/'Desktop/Proxy2VPN.command'
            self.assertTrue(shortcut.exists())
            self.assertIn('proxy2vpn.launcher',shortcut.read_text())
            self.assertIn("'",shortcut.read_text())


if __name__=='__main__': unittest.main()
