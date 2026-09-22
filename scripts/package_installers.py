"""Assemble platform one-click packages; source archive is a required companion."""
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'dist'
VERSION='0.2.0'


def main():
    if not (ROOT/'artifacts/proxy2vpn-corresponding-source.tar.gz').is_file():
        raise SystemExit('Build the corresponding source companion before packaging guest binaries')
    wheel=OUT/f'proxy2vpn-{VERSION}-py3-none-any.whl'
    for platform,arch in [('windows-x64','x86_64'),('macos-arm64','aarch64'),('macos-intel','x86_64')]:
        stage=ROOT/'build'/('installer-'+platform)
        (stage/'app').mkdir(parents=True,exist_ok=True)
        shutil.copy2(wheel,stage/'app'/wheel.name)
        (stage/'assets').mkdir(exist_ok=True)
        for name in ('vmlinuz','initramfs.gz','manifest.json','packages.txt'):
            shutil.copy2(ROOT/'artifacts'/arch/name,stage/'assets'/name)
        for name in ('LICENSE','THIRD_PARTY_NOTICES.md'):
            shutil.copy2(ROOT/name,stage/name)
        (stage/'READ-ME-FIRST.txt').write_text('Proxy2VPN 0.2.0\nWindows: double-click Install-Windows.cmd\nmacOS: open Install-Mac.command (right-click Open if macOS requires confirmation).\nThe installer downloads official Python/QEMU dependencies, starts a localhost console, and registers current-user login startup. First-time setup requires entering your existing proxy in the web page. Network access is required during installation. This is not a pre-login system service.\nGuest corresponding source: https://github.com/Yeqi99/proxy2vpn/releases/tag/v0.2.0\n',encoding='utf-8')
        if platform.startswith('windows'):
            for name in ('Install-Windows.cmd','Install-Windows.ps1'):shutil.copy2(ROOT/'installer'/name,stage/name)
            (stage/'tools').mkdir(exist_ok=True)
            for name in ('7z.exe','7z.dll','License.txt'):shutil.copy2(ROOT/'artifacts/7zip'/name,stage/'tools'/name)
            shutil.copy2(ROOT/'.proxy2vpn/downloads/7zip-source.tar.xz',stage/'tools/7zip-source.tar.xz')
        else:shutil.copy2(ROOT/'installer/Install-Mac.command',stage/'Install-Mac.command')
        target=OUT/f'proxy2vpn-{VERSION}-{platform}.zip'
        with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=5) as archive:
            for path in stage.rglob('*'):
                if not path.is_file():continue
                info=zipfile.ZipInfo('Proxy2VPN/'+path.relative_to(stage).as_posix())
                info.compress_type=zipfile.ZIP_DEFLATED
                info.external_attr=(0o100755 if path.suffix=='.command' else 0o100644)<<16
                archive.writestr(info,path.read_bytes())
        print(target)


if __name__=='__main__':main()
