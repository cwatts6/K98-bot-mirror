"""Build a private, fixed-file recovery packet; never connect or execute recovery."""

import argparse
import hashlib
import json
from pathlib import Path
from uuid import uuid4

MEMBERS = {
    "Read-K98PublicationTiming.ps1": "scripts/Read-K98PublicationTiming.ps1",
    "recover_stranded_export.py": "scripts/recover_stranded_export.py",
    "recover_saved_export_result.py": "scripts/recover_saved_export_result.py",
    "export_saved_result_recovery.py": "services/export_saved_result_recovery.py",
    "export_saved_result_recovery_dal.py": "services/export_saved_result_recovery_dal.py",
}


def build(target, output, *, root=None):
    root = Path(root) if root else Path(__file__).resolve().parents[1]
    target, output = Path(target), Path(output)
    if not target.is_absolute() or not output.is_absolute() or target.is_symlink():
        raise ValueError("Absolute local packet paths and regular target required.")
    raw = target.read_bytes()
    if len(raw) > 65536 or not isinstance(json.loads(raw), dict):
        raise ValueError("Bounded target document required.")
    payloads = {name: (root / source).read_bytes() for name, source in MEMBERS.items()}
    payloads["recovery-target.json"] = raw
    if any(len(value) > 1024 * 1024 for value in payloads.values()):
        raise ValueError("Packet member exceeds launcher bound.")
    packet = dict(
        version=1,
        packet_id=str(uuid4()),
        members=[
            dict(name=name, sha256=hashlib.sha256(value).hexdigest())
            for name, value in sorted(payloads.items())
        ],
    )
    payloads["recovery-packet.json"] = (
        json.dumps(packet, sort_keys=True, indent=2) + "\n"
    ).encode()
    launcher = "Invoke-SavedExportResultRecovery.ps1"
    payloads[launcher] = (root / "scripts" / launcher).read_bytes()
    output.mkdir(parents=False, exist_ok=False)
    for name, value in payloads.items():
        with (output / name).open("xb") as destination:
            destination.write(value)
        if (output / name).read_bytes() != value:
            raise ValueError("Packet write readback differs; preserve partial output.")
    return dict(
        packet_id=packet["packet_id"],
        packet_sha256=hashlib.sha256(payloads["recovery-packet.json"]).hexdigest(),
        launcher_sha256=hashlib.sha256(payloads[launcher]).hexdigest(),
        members=len(payloads),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.target, args.output), sort_keys=True))
