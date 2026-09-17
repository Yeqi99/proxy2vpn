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
