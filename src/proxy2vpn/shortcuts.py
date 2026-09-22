"""OS launchers that can start a stopped console without enabling login startup."""
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys


def create(home):
    home=Path(home).resolve()
    python=Path(sys.executable).resolve()
    # Keep the v0.2.0 desktop CMD entry working after an upgrade as well.
    (home/'open_console.py').write_text('from pathlib import Path\nfrom proxy2vpn.shortcuts import open_console\nopen_console(Path(__file__).parent)\n',encoding='utf-8')
    if sys.platform=='win32':
        if python.with_name('pythonw.exe').exists(): python=python.with_name('pythonw.exe')
        env=os.environ.copy()
        env.update(P2V_SHORTCUT_PYTHON=str(python), P2V_SHORTCUT_HOME=str(home),
                   P2V_SHORTCUT_ARGS=subprocess.list2cmdline(['-m','proxy2vpn.launcher','--home',str(home)]))
        # SpecialFolders honors redirected/OneDrive desktops; no personal paths
        # or credentials are interpolated into PowerShell source.
        script='''$ErrorActionPreference = 'Stop'
$shell = New-Object -ComObject WScript.Shell
$menu = Join-Path ($shell.SpecialFolders.Item('Programs')) 'Proxy2VPN'
New-Item -ItemType Directory -Force -Path $menu | Out-Null
$paths = @((Join-Path ($shell.SpecialFolders.Item('Desktop')) 'Proxy2VPN.lnk'), (Join-Path $menu 'Proxy2VPN.lnk'))
foreach ($path in $paths) {
    $link = $shell.CreateShortcut($path)
    $link.TargetPath = $env:P2V_SHORTCUT_PYTHON
    $link.Arguments = $env:P2V_SHORTCUT_ARGS
    $link.WorkingDirectory = $env:P2V_SHORTCUT_HOME
    $link.Description = 'Open Proxy2VPN local console'
    $link.Save()
}
'''
        subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',script],env=env,check=True,
                       creationflags=subprocess.CREATE_NO_WINDOW)
    elif sys.platform=='darwin':
        desktop=Path.home()/'Desktop'
        desktop.mkdir(exist_ok=True)
        path=desktop/'Proxy2VPN.command'
        command=shlex.join([str(python),'-m','proxy2vpn.launcher','--home',str(home)])
        path.write_text('#!/bin/bash\n'+command+'\nresult=$?\nif [ "$result" -ne 0 ]; then read -r -p "Could not open Proxy2VPN. Press Return to close."; fi\nexit "$result"\n',encoding='utf-8')
        path.chmod(0o700)


def open_console(home, browser=True):
    from .setup import main
    home=Path(home).resolve()
    install=json.loads((home/'installation.json').read_text())
    port=install.get('port',18990)
    if (home/'console.json').exists():
        port=json.loads((home/'console.json').read_text()).get('port',port)
    args=['--launch-only','--home',str(home),'--assets',install['assets'],
          '--qemu',install['qemu'],'--port',str(port)]
    if not browser: args.append('--no-browser')
    main(args)
