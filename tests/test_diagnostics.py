import subprocess
import unittest
from unittest.mock import patch
from proxy2vpn import doctor
from proxy2vpn.config import new_config


class DiagnosticTests(unittest.TestCase):
    def setUp(self):
        self.cfg=new_config('192.168.50.10','192.168.50.1','192.168.50.10',7890)

    @patch('proxy2vpn.doctor.shutil.which',return_value='curl')
    def test_windows_test_does_not_open_console(self,_):
        with patch.object(doctor.sys,'platform','win32'), patch.object(subprocess,'CREATE_NO_WINDOW',0x08000000,create=True), patch.object(subprocess,'run',return_value=subprocess.CompletedProcess([],0,'204','')) as run:
            doctor.https(self.cfg)
            self.assertEqual(run.call_args.kwargs['creationflags'],0x08000000)
            self.assertTrue(run.call_args.kwargs['capture_output'])

    @patch('proxy2vpn.doctor.shutil.which',return_value='curl')
    def test_connection_failure_has_stable_localizable_code(self,_):
        with patch.object(subprocess,'run',return_value=subprocess.CompletedProcess([],7,'000','')):
            with self.assertRaises(doctor.DiagnosticError) as error:doctor.https(self.cfg)
            self.assertEqual(error.exception.code,'test_connect')

    @patch('proxy2vpn.doctor.shutil.which',return_value='curl')
    def test_timeout_has_stable_localizable_code(self,_):
        with patch.object(subprocess,'run',side_effect=subprocess.TimeoutExpired('curl',20)):
            with self.assertRaises(doctor.DiagnosticError) as error:doctor.https(self.cfg)
            self.assertEqual(error.exception.code,'test_timeout')
