# Third-party components

The MIT license in this repository covers the original Proxy2VPN host code,
configuration generator, build instructions, and documentation. It does not
relicense third-party executables or the Linux guest filesystem.

No QEMU binary, Linux image, Mihomo binary, or user credentials are included in
the source distribution. The build script downloads upstream dependencies for
local use. This initial release distributes source only.

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

`guest/versions.json` pins the downloaded Mihomo release and archive checksums.
`artifacts/<architecture>/packages.txt` records the installed Alpine packages.
Their source packages and patches are available through the Alpine aports
repository for the corresponding release and package version.

Before distributing compiled guest images or bundling QEMU, include required
license notices and corresponding source for all components whose licenses
require them. A source URL alone is not a substitute for those obligations.
The default GitHub workflow deliberately uploads only the original source/wheel,
not the compiled guest image.
