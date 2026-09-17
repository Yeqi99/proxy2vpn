"""Build a clean stateless guest; no private runtime data enters Docker context."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--arch", choices=["x86_64", "aarch64"], default="x86_64")
    args = parser.parse_args()
    lock = json.loads((ROOT / "guest/versions.json").read_text())
    selected = lock[args.arch]
    output = ROOT / "artifacts" / args.arch
    subprocess.run(["docker", "buildx", "build", "--platform", selected["platform"],
        "-f", str(ROOT / "guest/Dockerfile"), "--build-arg", "MIHOMO_ASSET=" + selected["asset"],
        "--build-arg", "MIHOMO_SHA256=" + selected["sha256"],
        "--build-arg", "MIHOMO_VERSION=" + lock["mihomo_version"],
        "--output", "type=local,dest=" + str(output), str(ROOT)], check=True)
    manifest = {"architecture": args.arch, "mihomo_version": lock["mihomo_version"],
                "sha256": {name: hashlib.sha256((output / name).read_bytes()).hexdigest()
                           for name in ("vmlinuz", "initramfs.gz")}}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(output)


if __name__ == "__main__":
    main()
