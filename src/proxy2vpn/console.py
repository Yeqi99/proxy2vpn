"""Authenticated loopback-only web console and persistent gateway manager."""
import copy
import json
import logging
from logging.handlers import RotatingFileHandler
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import threading
import time
import webbrowser
import signal
from urllib.parse import urlsplit
import psutil
from . import autostart, config, doctor, runtime, vm
from .protocols import ensure_keys, client_config


def lan_addresses():
    return sorted({a.address for entries in psutil.net_if_addrs().values() for a in entries
                   if a.family == socket.AF_INET and not a.address.startswith(('127.', '169.254.'))})


def suggested_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(('192.0.2.1', 9))
            return s.getsockname()[0]
    except OSError:
        return next(iter(lan_addresses()), '192.168.50.10')


class Manager:
    def __init__(self, home, assets, port):
        self.home, self.assets, self.port = config.private_dir(home), Path(assets).resolve(), port
        self.mutex = threading.RLock()
        self.error = ''
        self.alive = True
        self.child = None
        token_file = self.home / 'console.token'
        if not token_file.exists():
            token_file.write_text(secrets.token_urlsafe(32))
            if sys.platform != 'win32': token_file.chmod(0o600)
        self.token = token_file.read_text().strip()
        settings = self.home / 'console.json'
        self.desired = json.loads(settings.read_text()).get('desired', False) if settings.exists() else False

    def set_desired(self, desired):
        self.desired = desired
        runtime.atomic_json(self.home / 'console.json', {'desired': desired, 'port': self.port})

    def stop_gateway(self):
        if runtime.running(self.home):
            (self.home / 'stop').touch()
            for _ in range(100):
                if not runtime.running(self.home): return
                time.sleep(.1)
            raise RuntimeError('停止超时；原配置已保留，请检查状态后重试。')

    def loop(self):
        while self.alive:
            try:
                with self.mutex:
                    if self.desired and not runtime.running(self.home) and (not self.child or self.child.poll() is not None):
                        cfg = config.load(self.home)
                        vm.binary(cfg); vm.verify_assets(self.assets)
                        with (self.home / 'launcher.log').open('ab') as log:
                            self.child = vm.popen([sys.executable, '-m', 'proxy2vpn', '--home', str(self.home), 'run', '--assets', str(self.assets)],
                                stdin=subprocess.DEVNULL, stdout=log, stderr=log)
                        self.error = ''
                    if self.child and self.child.poll() not in (None, 0):
                        self.error = '转发进程退出，请检查端口占用、代理设置和本地 launcher.log。'
            except Exception as exc:
                self.error = str(exc)
                logging.exception('Gateway management failed')
            time.sleep(3)

    def state(self):
        exists = (self.home / 'config.json').exists()
        cfg = config.load(self.home) if exists else config.new_config(suggested_ip(), suggested_ip().rsplit('.', 1)[0]+'.1', suggested_ip(), 7890)
        config.validate(cfg)
        public = copy.deepcopy(cfg)
        public['password'] = ''
        public['proxy']['password'] = ''
        public.pop('wireguard', None)
        public.pop('qemu', None)
        status = {}
        try: status = json.loads((self.home / 'status.json').read_text())
        except (OSError, ValueError): pass
        status['process_alive'] = runtime.running(self.home)
        if not status['process_alive']: status.update(running=False, l2tp_ready=False)
        return dict(configured=exists, config=public, status=status, desired=self.desired,
                    error=self.error, addresses=lan_addresses(), autostart=autostart.enabled(),
                    assets_ready=(self.assets / 'manifest.json').exists())

    def apply(self, values):
        old = config.load(self.home) if (self.home / 'config.json').exists() else config.new_config(suggested_ip(), suggested_ip().rsplit('.', 1)[0]+'.1', suggested_ip(), 7890)
        cfg = copy.deepcopy(old)
        for field in ('listen_ip','router_ip','listen_port','protocols','wireguard_port','http_port','socks_port'):
            if field in values: cfg[field] = values[field]
        p = values.get('proxy', {})
        if not isinstance(p,dict): raise ValueError('proxy 必须是对象。')
        for field in ('type','host','port','udp','username'):
            if field in p: cfg['proxy'][field] = p[field]
        if p.get('password'): cfg['proxy']['password'] = p['password']
        if values.get('clear_proxy_password'): cfg['proxy']['password'] = ''
        config.validate(cfg); ensure_keys(cfg)
        # Discover a locally provisioned binary without exposing executable paths as a web setting.
        install = self.home / 'installation.json'
        if install.exists(): cfg['qemu'] = json.loads(install.read_text())['qemu']
        vm.binary(cfg)
        vm.verify_assets(self.assets)
        with self.mutex:
            self.stop_gateway()
            # Coexist with other gateways: private QEMU forwarding ports need not
            # be fixed. LAN ports stay explicit because clients depend on them.
            for field in ('backend_port','wireguard_backend_port'):
                for port in range(cfg[field], min(cfg[field]+100,65536)):
                    try:
                        with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock: sock.bind(('127.0.0.1',port))
                    except OSError: continue
                    if port not in [cfg[k] for k in ('listen_port','wireguard_port','http_port','socks_port')]:
                        cfg[field]=port;break
                else: raise ValueError('无法分配内部 UDP 端口。')
            for name,field,kind in [('l2tp','listen_port',socket.SOCK_DGRAM),('wireguard','wireguard_port',socket.SOCK_DGRAM),('http','http_port',socket.SOCK_STREAM),('socks5','socks_port',socket.SOCK_STREAM)]:
                if name not in cfg['protocols']: continue
                try:
                    with socket.socket(socket.AF_INET,kind) as sock: sock.bind((cfg['listen_ip'],cfg[field]))
                except OSError as exc: raise ValueError(f'{name} 监听地址或端口不可用，请检查本机 IP 和端口占用。') from exc
            config.replace(self.home, cfg)
            self.set_desired(True)
            self.error = ''
        return {'ok': True, 'message': '已保存，正在启动转发。'}


class Handler(BaseHTTPRequestHandler):
    server_version = 'Proxy2VPN'
    def log_message(self, *args): pass  # never log bootstrap tokens or credentials
    @property
    def manager(self): return self.server.manager

    def reply(self, status, data, content_type='application/json; charset=utf-8', filename=None):
        body = json.dumps(data, ensure_ascii=False).encode() if not isinstance(data, bytes) else data
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'none'; connect-src 'self'")
        if filename: self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
        self.end_headers(); self.wfile.write(body)

    def permitted(self, api=True):
        expected = f'127.0.0.1:{self.server.server_port}'
        if self.headers.get('Host') != expected: return False
        origin = self.headers.get('Origin')
        if origin and origin != 'http://' + expected: return False
        return not api or secrets.compare_digest(self.headers.get('X-P2V-Token',''), self.manager.token)

    def do_GET(self):
        path = urlsplit(self.path).path
        if not self.permitted(path.startswith('/api/')):
            return self.reply(403, {'error':'请从安装器打开控制台，或输入本机控制台访问密钥。'})
        try:
            if path == '/api/state': return self.reply(200, self.manager.state())
            if path == '/api/credentials':
                cfg = config.load(self.manager.home)
                return self.reply(200, {'username':cfg['username'], 'password':cfg['password'], 'server':cfg['listen_ip']})
            if path == '/api/wireguard':
                cfg = config.load(self.manager.home)
                if 'wireguard' not in cfg['protocols']: raise ValueError('请先启用并保存 WireGuard')
                return self.reply(200, client_config(cfg).encode(), 'text/plain; charset=utf-8', 'proxy2vpn.conf')
            allowed = {'/':'index.html','/app.js':'app.js','/style.css':'style.css','/i18n.js':'i18n.js'}
            if path not in allowed: return self.reply(404, {'error':'Not found'})
            mime = {'/':'text/html; charset=utf-8','/app.js':'text/javascript; charset=utf-8','/style.css':'text/css; charset=utf-8','/i18n.js':'text/javascript; charset=utf-8'}[path]
            self.reply(200, (Path(__file__).parent / 'static' / allowed[path]).read_bytes(), mime)
        except (OSError, ValueError, KeyError) as exc: self.reply(400, {'error':str(exc)})

    def do_POST(self):
        if not self.permitted(): return self.reply(403, {'error':'禁止跨站请求或访问密钥无效。'})
        try:
            length = int(self.headers.get('Content-Length','0'))
            if not 0 < length <= 16384 or self.headers.get('Content-Type','').split(';')[0] != 'application/json':
                return self.reply(400, {'error':'需要有效的 JSON 请求。'})
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict): raise ValueError('Invalid request')
            path = urlsplit(self.path).path
            if path == '/api/config': return self.reply(200, self.manager.apply(body))
            if path == '/api/control':
                if body.get('action') not in ('start','stop'): raise ValueError('Unknown action')
                with self.manager.mutex:
                    if body['action'] == 'start': config.load(self.manager.home)
                    self.manager.set_desired(body['action'] == 'start')
                    if body['action'] == 'stop': self.manager.stop_gateway()
                return self.reply(200, {'ok':True})
            if path == '/api/autostart':
                if type(body.get('enabled')) is not bool: raise ValueError('Invalid enabled value')
                autostart.configure(body['enabled'], self.manager.home, self.manager.assets, self.manager.port)
                return self.reply(200, {'ok':True})
            if path == '/api/test':
                cfg = config.load(self.manager.home) if (self.manager.home/'config.json').exists() else config.new_config(suggested_ip(), suggested_ip().rsplit('.',1)[0]+'.1', suggested_ip(),7890)
                if 'proxy' in body:
                    if not isinstance(body['proxy'],dict): raise ValueError('Invalid proxy')
                    for key in ('type','host','port','username','password','udp'):
                        if key in body['proxy']:
                            if key == 'password' and not body['proxy'][key]: continue
                            cfg['proxy'][key]=body['proxy'][key]
                    if body.get('clear_proxy_password'): cfg['proxy']['password']=''
                    config.validate(cfg)
                result = doctor.https(cfg)
                return self.reply(200, {'ok':True, 'code':'test_ok', 'message':result})
            self.reply(404, {'error':'Not found'})
        except doctor.DiagnosticError as exc:
            self.reply(400, {'error':str(exc), 'code':exc.code})
        except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.SubprocessError) as exc:
            self.reply(400, {'error':str(exc)})


def serve(home, assets, port=18990, open_browser=False):
    manager = Manager(home, assets, port)
    handler = RotatingFileHandler(manager.home / 'console.log', maxBytes=2_000_000, backupCount=2)
    logging.basicConfig(handlers=[handler], level=logging.INFO)
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    server.daemon_threads = True
    server.manager = manager
    proc=psutil.Process()
    runtime.atomic_json(manager.home/'console-owner.json',{'pid':proc.pid,'created':proc.create_time()})
    worker = threading.Thread(target=manager.loop, daemon=True)
    worker.start()
    if open_browser: webbrowser.open(f'http://127.0.0.1:{port}/#{manager.token}')
    def shutdown(signum, frame): raise SystemExit(0)
    if threading.current_thread() is threading.main_thread(): signal.signal(signal.SIGTERM, shutdown)
    try: server.serve_forever(poll_interval=.5)
    finally:
        manager.alive = False
        with manager.mutex: manager.stop_gateway()
        server.server_close()
        (manager.home/'console-owner.json').unlink(missing_ok=True)
