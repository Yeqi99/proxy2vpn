# Contributing

1. Use Python 3.11+ and install with `python -m pip install -e .`.
2. Run `python -m unittest discover -s tests -v`.
3. Build the guest using `python scripts/build_guest.py --arch x86_64` (or aarch64).
4. Test a new instance using its own `--home`, LAN UDP port and backend UDP port.
   Do not run integration tests against someone's live router profile.
5. Run `python scripts/integration_client.py --home <private-test-home> --assets <assets>`.
   This uses a disposable second VM and contacts gstatic, Meta DNS and a public
   DNS resolver; it creates no host routes and changes no router settings.
6. Stop the test instance with `proxy2vpn --home <private-test-home> down`.

When reporting compatibility, include OS/CPU, QEMU version/accelerator, router
model/firmware, upstream protocol, the exact test performed, and its result.
Distinguish successful L2TP control handshakes, PPP authentication, actual TCP/UDP
traffic, and device experience. A mocked macOS command test is not a Mac test.

Do not commit private configuration, credentials, subscriptions, user IP/MAC
addresses, guest disks, generated images or personal logs. Example addresses
use the illustrative `192.168.50.0/24` network. The source-only release packer
uses Git's tracked files so ignored state is never packaged.

## Release packages

Build both guest architectures with `scripts/build_guest.py`. Run
`scripts/collect_sources.py` to fetch exact Alpine recipes, verified source
archives and vendored Mihomo source. GitHub CLI and Docker are required.
Publish the corresponding-source archive alongside every guest binary release.

Build the wheel with `python -m build --wheel`. Windows packaging also needs
7-Zip runtime/license under `artifacts/7zip` and complete sources under
`.proxy2vpn/downloads/7zip-source.tar.xz`. Run `scripts/package_installers.py`
to assemble platform ZIPs. Review and stage public files, then run
`scripts/source_release.py` for a source ZIP. Publish checksums for all assets.

`scripts/integration_wireguard.py` uses a disposable client and separate test
profile to check HTTPS, gateway DNS and external UDP. Preserve platform
verification limits until the actual OS/hardware is tested.
