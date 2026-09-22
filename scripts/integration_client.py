"""Disposable QEMU client tests the running gateway through the host LAN port.

Uses a second, stateless VM; no router changes, routes or interfaces on the host.
Reads credentials only from the requested private home. Test files remain there.
"""
import argparse
import gzip
import json
from pathlib import Path
import subprocess
import time
from proxy2vpn.config import load
from proxy2vpn.render import cpio
from proxy2vpn import vm


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--home", type=Path, required=True)
    p.add_argument("--assets", type=Path, required=True)
    args = p.parse_args()
    home, assets = args.home.resolve(), args.assets.resolve()
    cfg = load(home)
    gateway = cfg["subnet"].rsplit('.', 1)[0] + '.1'
    client = home / "integration"
    client.mkdir(exist_ok=True, mode=0o700)
    init = r'''#!/bin/sh
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
mkdir -p /proc /sys /dev /run /tmp /var/log
mount -t proc proc /proc
mount -t sysfs sysfs /sys
mount -t devtmpfs devtmpfs /dev
mkdir -p /dev/pts /run/xl2tpd
mount -t devpts devpts /dev/pts
exec </dev/console >/dev/console 2>&1
for m in virtio_pci virtio_net ppp_generic ppp_async; do modprobe "$m"; done
ip link set lo up
ip address add 127.0.0.1/8 dev lo 2>/dev/null || true
ip link set eth0 up
udhcpc -i eth0 -q -n
ip route add SERVER/32 via 10.0.2.2 dev eth0
xl2tpd -D >/tmp/client.log 2>&1 &
i=0
until ip link show ppp0 >/dev/null 2>&1; do
  i=$((i+1)); if [ "$i" -ge 30 ]; then cat /tmp/client.log; echo P2V_TEST_FAILED_PPP; poweroff -f; fi
  sleep 1
done
sleep 2
ip route replace default dev ppp0
echo 'nameserver GATEWAY' > /etc/resolv.conf
echo P2V_TEST_PPP_UP
code=$(curl --silent --max-time 20 -o /dev/null -w '%{http_code}' https://www.gstatic.com/generate_204)
if [ "$code" = 204 ]; then echo P2V_TEST_HTTPS_PASS; else echo P2V_TEST_HTTPS_FAIL; fi
if nslookup www.meta.com GATEWAY >/tmp/dns 2>&1; then echo P2V_TEST_DNS_PASS; else cat /tmp/dns; echo P2V_TEST_DNS_FAIL; fi
if [ UDP = true ]; then
  if nslookup example.com 1.1.1.1 >/tmp/udp 2>&1; then echo P2V_TEST_UDP_PASS; else cat /tmp/udp; echo P2V_TEST_UDP_FAIL; fi
fi
echo P2V_TEST_DONE
poweroff -f
'''.replace("SERVER", cfg["listen_ip"]).replace("GATEWAY", gateway).replace("UDP =", str(cfg["proxy"]["udp"]).lower() + " =")
    files = {"init": init,
             "etc/xl2tpd/xl2tpd.conf": f'''[global]
port = 1702
[lac test]
lns = {cfg['listen_ip']}:{cfg['listen_port']}
pppoptfile = /etc/ppp/test-options
autodial = yes
redial = no
''', "etc/ppp/test-options": f'''noauth
name {cfg['username']}
password {cfg['password']}
mtu {cfg['mtu']}
mru {cfg['mtu']}
noipdefault
noccp
noipv6
ipcp-accept-local
ipcp-accept-remote
''' }
    overlay = client / "session-initramfs.gz"
    overlay.write_bytes((assets / "initramfs.gz").read_bytes() + gzip.compress(cpio(files, executable=["init"]), mtime=0))
    test_cfg = dict(cfg, backend_port=cfg["backend_port"] + 1, protocols=['l2tp'])
    log_path = client / "guest.log"
    try:
        with log_path.open("wb") as log:
            proc = vm.popen(vm.command(test_cfg, client, assets, vm.accelerators(cfg)[0]),
                stdin=subprocess.DEVNULL, stdout=log, stderr=log)
        try:
            proc.wait(timeout=110)
        except subprocess.TimeoutExpired:
            proc.terminate(); proc.wait(timeout=10)
        log = log_path.read_text(errors="replace")
        checks = {name: marker in log for name, marker in {
            "ppp": "P2V_TEST_PPP_UP", "https": "P2V_TEST_HTTPS_PASS",
            "dns": "P2V_TEST_DNS_PASS", **({"udp": "P2V_TEST_UDP_PASS"} if cfg["proxy"]["udp"] else {})}.items()}
        report = {"checks": checks, "all_passed": all(checks.values()),
                  "transport": "independent QEMU L2TP/PPP client through host LAN UDP listener",
                  "udp_test": "DNS packet to public resolver through SOCKS5 (not gateway DNS)" if cfg["proxy"]["udp"] else "not supported in this mode",
                  "device_acceptance": "not tested"}
        (client / "report.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
        if not report["all_passed"]:
            print("Inspect private integration/guest.log")
            raise SystemExit(1)
    finally:
        overlay.unlink(missing_ok=True)


if __name__ == "__main__": main()
