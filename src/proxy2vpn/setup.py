"""Finalize a packaged install, register login startup and open the local console."""
import argparse
import json
from pathlib import Path
import socket
import subprocess
import sys
import time
import webbrowser
import psutil
from . import autostart, config, runtime, vm, shortcuts


def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument('--home',type=Path,default=Path.home()/'.proxy2vpn')
    p.add_argument('--assets',type=Path,required=True)
    p.add_argument('--qemu',required=True)
    p.add_argument('--port',type=int,default=18990)
    p.add_argument('--no-autostart',action='store_true')
    p.add_argument('--no-browser',action='store_true')
    p.add_argument('--restart',action='store_true')
    p.add_argument('--launch-only',action='store_true',help='Open/start the console without changing startup preferences')
    a=p.parse_args(argv); home=config.private_dir(a.home); assets=a.assets.resolve()
    installed=(home/'installation.json').exists()
    start_on_login=False if a.no_autostart else autostart.preference(home,installed)
    manifest=vm.verify_assets(assets)
    if not Path(a.qemu).is_file(): raise FileNotFoundError('QEMU missing')
    runtime.atomic_json(home/'installation.json',{'qemu':str(Path(a.qemu).resolve()),'assets':str(assets),'architecture':manifest['architecture'],'port':a.port})
    # Existing users keep all credentials and proxy settings.
    if (home/'config.json').exists():
        cfg=config.load(home);cfg['qemu']=str(Path(a.qemu).resolve());config.replace(home,cfg)
    python=Path(sys.executable).resolve()
    if sys.platform=='win32' and python.with_name('pythonw.exe').exists():python=python.with_name('pythonw.exe')
    args=[str(python),'-m','proxy2vpn','--home',str(home),'console','--assets',str(assets),'--port',str(a.port)]
    if a.restart and (home/'console-owner.json').exists():
        owner=json.loads((home/'console-owner.json').read_text())
        try:
            proc=psutil.Process(owner['pid'])
            cmd=proc.cmdline()
            if abs(proc.create_time()-owner['created'])<.1 and 'proxy2vpn' in cmd and 'console' in cmd and str(home) in cmd:
                if runtime.running(home):
                    (home/'stop').touch()
                    for _ in range(60):
                        if not runtime.running(home):break
                        time.sleep(.25)
                    else:raise RuntimeError('Gateway did not stop for upgrade')
                proc.terminate();proc.wait(10)
        except psutil.NoSuchProcess:pass
    try:
        with socket.create_connection(('127.0.0.1',a.port),timeout=1): listening=True
    except OSError: listening=False
    if listening:
        # Fail closed on an unrelated service at the console port.
        from urllib.request import Request,urlopen
        token=(home/'console.token').read_text().strip()
        with urlopen(Request(f'http://127.0.0.1:{a.port}/api/state',headers={'X-P2V-Token':token}),timeout=3) as r:
            if r.status!=200:raise RuntimeError('Console port occupied')
    elif sys.platform=='darwin' and start_on_login and not a.launch_only:
        autostart.configure(True,home,assets,a.port)
    else:
        with (home/'console-launch.log').open('ab') as log:
            vm.popen(args,stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=sys.platform!='win32')
    for _ in range(40):
        try:
            with socket.create_connection(('127.0.0.1',a.port),timeout=.5): break
        except OSError: time.sleep(.25)
    else: raise RuntimeError('Console did not start; inspect console-launch.log')
    if not a.launch_only:
        autostart.configure(start_on_login,home,assets,a.port)
        shortcuts.create(home)
    if not a.no_browser:webbrowser.open(f'http://127.0.0.1:{a.port}/#'+(home/'console.token').read_text().strip())
    print('Console ready. Enter the upstream proxy in the web page; save to start forwarding.')


if __name__=='__main__':main()
