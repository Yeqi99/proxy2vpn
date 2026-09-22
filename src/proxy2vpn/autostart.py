"""Current-user login startup; never modifies other applications' entries."""
import os
from pathlib import Path
import plistlib
import subprocess
import sys
import socket


def arguments(home, assets, port):
    python = Path(sys.executable)
    if sys.platform == 'win32' and python.with_name('pythonw.exe').exists(): python = python.with_name('pythonw.exe')
    return [str(python), '-m', 'proxy2vpn', '--home', str(home), 'console', '--assets', str(assets), '--port', str(port)]


def enabled():
    if sys.platform == 'win32':
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run') as key:
                winreg.QueryValueEx(key, 'Proxy2VPN')
            return True
        except OSError: return False
    if sys.platform == 'darwin':
        return (Path.home() / 'Library/LaunchAgents/local.proxy2vpn.console.plist').exists()
    return False


def configure(enable, home, assets, port):
    args = arguments(home, assets, port)
    if sys.platform == 'win32':
        import winreg
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run') as key:
            if enable: winreg.SetValueEx(key, 'Proxy2VPN', 0, winreg.REG_SZ, subprocess.list2cmdline(args))
            else:
                try: winreg.DeleteValue(key, 'Proxy2VPN')
                except FileNotFoundError: pass
    elif sys.platform == 'darwin':
        path = Path.home() / 'Library/LaunchAgents/local.proxy2vpn.console.plist'
        if enable:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(plistlib.dumps({'Label': 'local.proxy2vpn.console', 'ProgramArguments': args,
                'RunAtLoad': True, 'KeepAlive': True, 'ThrottleInterval': 15,
                'EnvironmentVariables': {'PATH': '/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin'},
                'StandardOutPath': str(home / 'console-launch.log'), 'StandardErrorPath': str(home / 'console-launch.log')}))
            # Bootstrap only if not loaded. An installer-launched console can coexist
            # temporarily; the port lock prevents a second manager from starting.
            try:
                with socket.create_connection(('127.0.0.1',port), timeout=.5): active=True
            except OSError: active=False
            if not active:
                service=f'gui/{os.getuid()}/local.proxy2vpn.console'
                loaded=subprocess.run(['launchctl','print',service],capture_output=True).returncode == 0
                command=['launchctl','kickstart',service] if loaded else ['launchctl','bootstrap',f'gui/{os.getuid()}',str(path)]
                result=subprocess.run(command,capture_output=True)
                if result.returncode: raise RuntimeError('launchd bootstrap failed; inspect console-launch.log')
        else:
            path.unlink(missing_ok=True)
            # Disable future login startup without terminating the current console.
            # The loaded user job expires at logout.
    else: raise ValueError('Login startup is implemented for Windows and macOS')
