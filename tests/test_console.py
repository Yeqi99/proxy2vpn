import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from unittest.mock import patch
from proxy2vpn.console import Handler, Manager
from proxy2vpn.config import new_config, save, validate
from proxy2vpn.protocols import ensure_keys, client_config
from proxy2vpn.render import guest_files


class ConsoleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.home=Path(cls.temp.name)
        cls.cfg=new_config('192.168.50.10','192.168.50.1','192.168.50.10',7890)
        cls.cfg.update(protocols=['l2tp','wireguard','http','socks5'])
        ensure_keys(cls.cfg);save(cls.home,cls.cfg)
        cls.manager=Manager(cls.home,cls.home/'assets',0)
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        cls.server.manager=cls.manager
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join();cls.temp.cleanup()

    def request(self,path,token=True,origin=None,body=None,host=None):
        client=http.client.HTTPConnection('127.0.0.1',self.server.server_port)
        headers={}
        if token:headers['X-P2V-Token']=self.manager.token
        if origin:headers['Origin']=origin
        if host:headers['Host']=host
        if body is not None:headers['Content-Type']='application/json'
        client.request('POST' if body is not None else 'GET',path,json.dumps(body) if body is not None else None,headers)
        response=client.getresponse();data=response.read();client.close()
        return response.status,data

    def test_state_requires_token(self):self.assertEqual(self.request('/api/state',token=False)[0],403)
    def test_cross_origin_rejected(self):self.assertEqual(self.request('/api/state',origin='https://example.com')[0],403)
    def test_dns_rebinding_host_rejected(self):self.assertEqual(self.request('/api/state',host='attacker.example')[0],403)
    def test_public_page_has_no_credentials(self):
        code,body=self.request('/',token=False)
        self.assertEqual(code,200);self.assertNotIn(self.cfg['password'].encode(),body)
    def test_state_redacts_all_secrets(self):
        code,body=self.request('/api/state');self.assertEqual(code,200)
        for secret in (self.cfg['password'],self.cfg['wireguard']['private'],self.cfg['wireguard']['client_private'],self.manager.token):self.assertNotIn(secret.encode(),body)
    def test_wireguard_export_authentication(self):
        self.assertEqual(self.request('/api/wireguard',token=False)[0],403)
        code,body=self.request('/api/wireguard');self.assertEqual(code,200)
        self.assertIn(self.cfg['wireguard']['client_private'].encode(),body)
        self.assertNotIn(self.cfg['wireguard']['private'].encode(),body)
    def test_invalid_protocol_cannot_stop_running_gateway(self):
        with patch.object(self.manager,'stop_gateway') as stop:
            code,_=self.request('/api/config',body={'protocols':['not-a-protocol']})
            self.assertEqual(code,400);stop.assert_not_called()
    def test_invalid_json_object_rejected(self):self.assertEqual(self.request('/api/control',body=[])[0],400)
    def test_unknown_control_rejected(self):self.assertEqual(self.request('/api/control',body={'action':'execute'})[0],400)
    def test_rendered_proxy_auth_is_required(self):
        cfg=json.loads(guest_files(self.cfg)['etc/mihomo/config.yaml'])
        self.assertEqual(cfg['port'],8080);self.assertEqual(cfg['socks-port'],1080)
        self.assertTrue(cfg['authentication'])
    def test_wireguard_client_excludes_server_private_key(self):
        export=client_config(self.cfg)
        self.assertNotIn(self.cfg['wireguard']['private'],export)
        self.assertIn('AllowedIPs = 0.0.0.0/0',export)
