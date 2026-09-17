#!/bin/sh
set -eu
. /etc/proxy2vpn.env
sysctl -w net.ipv4.ip_forward=1
sysctl -w net.ipv4.conf.all.rp_filter=0
sysctl -w net.ipv4.conf.default.rp_filter=0
ip address add "$GATEWAY/32" dev lo 2>/dev/null || true
cleanup() { kill "$M" "${L:-}" 2>/dev/null || true; wait 2>/dev/null || true; }
trap cleanup EXIT INT TERM
mihomo -d /etc/mihomo &
M=$!
i=0
until ip link show p2v >/dev/null 2>&1; do
    i=$((i+1)); [ "$i" -lt 30 ] || exit 1
    kill -0 "$M"; sleep 1
done
ip route replace default dev p2v table 177
ip rule del priority 176 2>/dev/null || true
ip rule add priority 176 to "$SUBNET" lookup main
ip rule del priority 177 2>/dev/null || true
ip rule add priority 177 from "$SUBNET" lookup 177
iptables -P FORWARD DROP
iptables -F FORWARD
if [ "$UDP_ENABLED" = 0 ]; then
    iptables -A FORWARD -i ppp+ -p udp -j REJECT --reject-with icmp-port-unreachable
fi
iptables -A FORWARD -i ppp+ -o p2v -j ACCEPT
iptables -A FORWARD -i p2v -o ppp+ -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -t mangle -F FORWARD
iptables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu
xl2tpd -D &
L=$!
echo 'P2V_READY L2TP gateway active'
while kill -0 "$M" && kill -0 "$L"; do sleep 3; done
