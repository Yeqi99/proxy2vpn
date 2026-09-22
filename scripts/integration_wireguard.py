"""Exercise WireGuard with a second guest, without installing a host VPN adapter."""
import argparse
import gzip
import json
from pathlib import Path
import subprocess
from proxy2vpn import config, vm
from proxy2vpn.render import cpio

p=argparse.ArgumentParser()
p.add_argument('--home',type=Path,required=True)
p.add_argument('--assets',type=Path,required=True)
a=p.parse_args(); home=a.home.resolve(); assets=a.assets.resolve(); cfg=config.load(home)
base=cfg['subnet'].rsplit('.',1)[0]; keys=cfg['wireguard']
directory=home/'wg-integration'; directory.mkdir(exist_ok=True)
init='''#!/bin/sh
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
mkdir -p /proc /sys /dev /run /tmp
mount -t proc proc /proc
mount -t sysfs sysfs /sys
mount -t devtmpfs devtmpfs /dev
exec </dev/console >/dev/console 2>&1
modprobe virtio_pci; modprobe virtio_net
ip link set lo up; ip addr add 127.0.0.1/8 dev lo
ip link set eth0 up; udhcpc -i eth0 -q -n
ip route add SERVER/32 via 10.0.2.2 dev eth0
ip link add wg0 type wireguard
wg setconf wg0 /etc/wireguard/client.conf
ip address add CLIENT/32 dev wg0
ip link set wg0 mtu 1360 up
ip route replace default dev wg0
echo 'nameserver GATEWAY' > /etc/resolv.conf
sleep 2
code=$(curl --silent --max-time 25 -o /dev/null -w '%{http_code}' https://www.gstatic.com/generate_204)
[ "$code" != 204 ] || echo P2V_WG_HTTPS_PASS
nslookup www.meta.com GATEWAY >/tmp/dns 2>&1 && echo P2V_WG_DNS_PASS
nslookup example.com 1.1.1.1 >/tmp/udp 2>&1 && echo P2V_WG_UDP_PASS
wg show wg0
poweroff -f
'''.replace('SERVER',cfg['listen_ip']).replace('CLIENT',base+'.20').replace('GATEWAY',base+'.1')
files={'init':init,'etc/wireguard/client.conf':f"[Interface]\nPrivateKey = {keys['client_private']}\n\n[Peer]\nPublicKey = {keys['public']}\nAllowedIPs = 0.0.0.0/0\nEndpoint = {cfg['listen_ip']}:{cfg['wireguard_port']}\nPersistentKeepalive = 25\n"}
overlay=directory/'session-initramfs.gz'
overlay.write_bytes((assets/'initramfs.gz').read_bytes()+gzip.compress(cpio(files,executable=['init']),mtime=0))
try:
    with (directory/'guest.log').open('wb') as log:
        proc=vm.popen(vm.command(dict(cfg,protocols=['l2tp'],backend_port=cfg['backend_port']+2),directory,assets,vm.accelerators(cfg)[0]),stdin=subprocess.DEVNULL,stdout=log,stderr=log)
    try: proc.wait(timeout=100)
    except subprocess.TimeoutExpired: proc.terminate();proc.wait()
    data=(directory/'guest.log').read_text(errors='replace')
    checks={k:'P2V_WG_'+k.upper()+'_PASS' in data for k in ('https','dns','udp')}
    print(json.dumps(checks))
    (directory/'report.json').write_text(json.dumps(checks))
    if not all(checks.values()): raise SystemExit(1)
finally: overlay.unlink(missing_ok=True)
