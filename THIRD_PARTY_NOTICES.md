# Third-party components

The MIT license in this repository covers the original Proxy2VPN host code,
configuration generator, build instructions, and documentation. It does not
relicense third-party executables or the Linux guest filesystem.

The source repository contains no user credentials or third-party binaries.
The v0.2 installers include a prebuilt Linux guest. Its corresponding source,
exact Alpine build recipes/patches and verified upstream source archives are
provided as a companion download on the same release page. The installed APK
database records the exact origin and aports commit for every package.
Windows packages include 7-Zip 26.03 with its license and complete source archive.
QEMU and Python are downloaded from upstream by the installer, not bundled.

| Component | Upstream / source | License |
| --- | --- | --- |
| QEMU | https://www.qemu.org/ and https://gitlab.com/qemu-project/qemu | GPL-2.0 and component-specific licenses |
| Linux | https://www.kernel.org/ | GPL-2.0-only and exceptions |
| Alpine Linux packages | https://gitlab.alpinelinux.org/alpine/aports | Individual package licenses |
| BusyBox | https://busybox.net/ | GPL-2.0 |
| xl2tpd | https://github.com/xelerance/xl2tpd | GPL-2.0 |
| ppp | https://github.com/ppp-project/ppp | Multiple BSD/GPL licenses by file |
| Mihomo | https://github.com/MetaCubeX/mihomo/tree/v1.19.31 | GPL-3.0 |
| psutil | https://github.com/giampaolo/psutil | BSD-3-Clause |
| 7-Zip | https://github.com/ip7z/7zip | LGPL / BSD / unRAR restriction; see bundled License.txt |
| WireGuard tools | https://git.zx2c4.com/wireguard-tools | GPL-2.0 |
| cryptography | https://github.com/pyca/cryptography | Apache-2.0 / BSD-3-Clause |

`guest/versions.json` pins the downloaded Mihomo release and archive checksums.
`artifacts/<architecture>/packages.txt` records the installed Alpine packages.
Their source packages and patches are available through the Alpine aports
repository for the corresponding release and package version.

Before distributing compiled guest images or bundling QEMU, include required
license notices and corresponding source for all components whose licenses
require them. A source URL alone is not a substitute for those obligations.
Public installer releases must also attach the corresponding-source companion
produced by `scripts/collect_sources.py`; do not publish a binary-only guest release.
