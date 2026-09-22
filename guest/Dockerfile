# Build dependencies only. Docker is not used for the running VPN.
FROM alpine:3.24 AS builder
ARG MIHOMO_VERSION=v1.19.31
ARG MIHOMO_ASSET=amd64-compatible
ARG MIHOMO_SHA256=04cf9f09671704f839ddbee2e93069dc831a4123a75281e725d1d96ab9ac1afc
RUN apk add --no-cache linux-virt xl2tpd ppp iproute2 iptables curl ca-certificates kmod wireguard-tools
RUN curl -fL --retry 3 -o /tmp/mihomo.gz "https://github.com/MetaCubeX/mihomo/releases/download/${MIHOMO_VERSION}/mihomo-linux-${MIHOMO_ASSET}-${MIHOMO_VERSION}.gz" \
    && echo "${MIHOMO_SHA256}  /tmp/mihomo.gz" | sha256sum -c - \
    && gzip -dc /tmp/mihomo.gz > /usr/local/bin/mihomo \
    && chmod 755 /usr/local/bin/mihomo \
    && rm /tmp/mihomo.gz
COPY guest/init /init
COPY guest/bridge.sh /usr/local/sbin/proxy2vpn-bridge
RUN chmod 755 /init /usr/local/sbin/proxy2vpn-bridge \
    && mkdir -p /out /etc/mihomo /etc/xl2tpd /etc/ppp /run/xl2tpd \
    && cp /boot/vmlinuz-virt /out/vmlinuz \
    && apk info -vv > /out/packages.txt \
    && find . -xdev \( -path ./out -o -path ./proc -o -path ./sys -o -path ./dev -o -path ./boot -o -path ./tmp \) -prune -o -print \
       | cpio -o -H newc | gzip -1 > /out/initramfs.gz
FROM scratch AS export
COPY --from=builder /out/ /
