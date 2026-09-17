"""Package only Git-tracked source, with a final private-state denylist."""
import hashlib
from pathlib import Path
import subprocess
import zipfile

root = Path(__file__).resolve().parents[1]
files = subprocess.check_output(["git", "ls-files", "-z"], cwd=root).decode().split("\0")
files = [f for f in files if f]
for name in files:
    if any(part in {".proxy2vpn", "private", "runtime", "artifacts", "logs", ".venv"} for part in Path(name).parts):
        raise SystemExit(f"Refusing to package private/generated path: {name}")
    if Path(name).suffix.lower() in {".qcow2", ".iso", ".gz", ".log", ".key"}:
        raise SystemExit(f"Refusing to package generated/secret file: {name}")
if not files:
    raise SystemExit("No tracked source files; review and stage the source first")
output = root / "dist"
output.mkdir(exist_ok=True)
target = output / "proxy2vpn-0.1.0-source.zip"
with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
    for name in files:
        archive.write(root / name, "proxy2vpn/" + name)
checksum = hashlib.sha256(target.read_bytes()).hexdigest()
(output / "SHA256SUMS").write_text(f"{checksum}  {target.name}\n")
print(target)
