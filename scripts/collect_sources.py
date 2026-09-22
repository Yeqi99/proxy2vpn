"""Collect exact Alpine build recipes and sources for binary guest distribution.

Uses the APK origin + aports commit recorded inside the actual image. Source
fetch/verification runs in disposable Alpine, never on the Windows/macOS host.
"""
import gzip
import json
from pathlib import Path
import subprocess
import urllib.request
import concurrent.futures
import tarfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts' / 'corresponding-source'


def entries(path):
    data = gzip.decompress(path.read_bytes()); pos = 0
    while data[pos:pos+6] == b'070701':
        header = data[pos:pos+110]
        v = [int(header[6+i*8:14+i*8],16) for i in range(13)]
        name = data[pos+110:pos+110+v[11]-1].decode().removeprefix('./')
        pos = (pos+110+v[11]+3)&~3
        body = data[pos:pos+v[6]]; pos = (pos+v[6]+3)&~3
        yield name, body


def fetch(url, path):
    if path.exists(): return
    path.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=90) as r: path.write_bytes(r.read())


def recipe(item):
    origin, commit = item
    directory = OUT / 'aports' / (origin+'-'+commit[:12])
    if (directory / 'RECIPE.json').exists(): return
    for section in ('main','community'):
        command = ['gh','api',f'repos/alpinelinux/aports/contents/{section}/{origin}?ref={commit}']
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0: break
    else: raise RuntimeError('Recipe not found: '+origin)
    items = json.loads(result.stdout)
    def retrieve(entries, dest):
        for entry in entries:
            if entry['type'] == 'file': fetch(entry['download_url'], dest / entry['name'])
            elif entry['type'] == 'dir':
                nested = subprocess.check_output(['gh','api',entry['url']], text=True)
                retrieve(json.loads(nested), dest / entry['name'])
    retrieve(items, directory)
    (directory / 'RECIPE.json').write_text(json.dumps({'origin':origin,'commit':commit,'section':section}))
    print('Recipe:',origin,flush=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    origins=set()
    for arch in ('x86_64','aarch64'):
        package_db = dict(entries(ROOT / 'artifacts' / arch / 'initramfs.gz'))['lib/apk/db/installed'].decode()
        (OUT / (arch+'-installed.txt')).write_text(package_db, encoding='utf-8')
        for entry in package_db.split('\n\n'):
            fields={line[:1]:line[2:] for line in entry.splitlines() if len(line)>2 and line[1]==':'}
            if 'o' in fields and 'c' in fields: origins.add((fields['o'],fields['c']))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool: list(pool.map(recipe, sorted(origins)))
    # Upstream fetches and checksum validation use official Alpine abuild logic.
    command = '''set -eu
apk add --no-cache abuild alpine-sdk bash curl
mkdir -p /sources/distfiles
for dir in /sources/aports/*; do
  cd "$dir"
  DISTFILES_MIRROR=https://distfiles.alpinelinux.org/distfiles/v3.24 SRCDEST=/sources/distfiles abuild -F fetch verify
done
'''
    subprocess.run(['docker','run','--rm','-v',str(OUT)+':/sources','alpine:3.24','sh','-c',command],check=True)
    fetch('https://github.com/MetaCubeX/mihomo/archive/refs/tags/v1.19.31.tar.gz', OUT / 'mihomo-v1.19.31.tar.gz')
    subprocess.run(['docker','run','--rm','-v',str(OUT)+':/sources','golang:1.25-alpine','sh','-c',
        'set -eu; cd /tmp; tar -xzf /sources/mihomo-v1.19.31.tar.gz; cd mihomo-1.19.31; go mod vendor; tar -czf /sources/mihomo-v1.19.31-vendored.tar.gz .'],check=True)
    (OUT / 'README.txt').write_text('Corresponding source for the distributed Proxy2VPN guest. Exact Alpine package origins and build commits are recorded in *-installed.txt and aports/*/RECIPE.json. distfiles contains upstream sources verified by abuild against the recipes. Mihomo source is the unmodified official v1.19.31 tag. Original guest assembly instructions are in the Proxy2VPN source repository. QEMU/Python are downloaded separately by installers and are not in this guest image.\n')
    pack()


def pack():
    def keep(info):
        parts=Path(info.name).parts
        if len(parts)>=4 and parts[1]=='aports' and parts[3] in ('src','pkg'): return None
        return None if info.name.endswith('.lock') else info
    with tarfile.open(ROOT / 'artifacts' / 'proxy2vpn-corresponding-source.tar.gz','w:gz') as tar:
        tar.add(OUT,arcname='corresponding-source',filter=keep)


if __name__ == '__main__': main()
