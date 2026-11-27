"""Seal a read-only installation-binding continuation; never issue a release."""

from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.prepare_p02_observer_representative import seal_packet
from scripts.verify_k98_update_pair import build_contract_archive
from services.catalogue_observation_contract import PROTOCOL_SHA256, ObservationInstallation


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def build():
    evidence = ROOT / ".codex_artifacts/p02-observer-proof-20261119"
    prior = evidence / "packet-20261120115300322"
    receipt = (prior / "receipt.json").read_bytes()
    assert sha(receipt) == "048420e111201e0a7c6944ff2a099d7a41b3adf8ab85227b116ed87712b58c6c"
    result = json.loads(receipt)
    assert result["outcome"] == "representative-combined-categories-passed"
    assert result["connections_closed"] == 2 and len(result["checks"]) == 2
    assert all(check["passed"] for check in result["checks"])
    assert result["business_operations"] == result["production_operations"] == 0
    archive = (prior / "packet.zip").read_bytes()
    assert sha(archive) == "612734a2777d31ae09e4a48ea0db4b8f7f82a8b39503e08bead9be0b90860b3d"
    with zipfile.ZipFile(prior / "packet.zip") as source:
        old = json.loads(source.read("manifest.json"))
        assert set(source.namelist()) == {"manifest.json", *old["files"]}
        assert all(sha(source.read(name)) == value for name, value in old["files"].items())
        incarnation = old["reuse"]["sequence_identity"]
        assert json.loads(source.read("source/protocol.json")) == json.loads(
            (ROOT / "deploy/p02_observer_protocol.json").read_bytes()
        )
    installed_raw = (evidence / "packet-20261119205611983/receipt.json").read_bytes()
    assert sha(installed_raw) == "9e7e67fd4914cec25c3451a140122a1949821f962ce25c6d25fa3d9259f443ca"
    installed = json.loads(installed_raw)["checks"][1]
    assert installed["name"] == "atomic-candidate-source-and-lab-permission-install"
    assert installed["passed"] and installed["facts"]["source_batches"] == 12
    assert installed["facts"]["sequence_identity"] == incarnation
    assert old["reuse"]["generation"] == 270
    assert incarnation == [1125344265, "2026-11-19 20:57:41.937000", "2026-11-19 20:57:41.937000"]
    installation = dict(
        version=1,
        protocol_sha256=PROTOCOL_SHA256,
        server="MINI_AMD",
        database="K98_P025_D5e_Cost_20261115",
        database_id=11,
        principal="S11_ExportApplication_P02Qual",
        login=r"MINI_AMD\K98LabAdmin",
        sequence_object_id=incarnation[0],
        sequence_created=incarnation[1].replace(" ", "T"),
        sequence_modified=incarnation[2].replace(" ", "T"),
        bootstrap_generation=1,
    )
    ObservationInstallation(installation)
    packed = build_contract_archive(ROOT)
    members = {
        "contract_verifier.zip": packed,
        "Verify-NewPair.py": (ROOT / "scripts/verify_k98_update_pair.py").read_bytes(),
        "Verify-RunningRelease.py": (ROOT / "scripts/verify_k98_running_release.py").read_bytes(),
        "qualification/p02_observer/representative.py": (
            ROOT / "scripts/prove_p02_observer_binding.py"
        ).read_bytes(),
        "evidence/prior-receipt.json": receipt,
        "evidence/installation-receipt.json": installed_raw,
        "evidence/prior-manifest.json": json.dumps(old, indent=2).encode(),
    }
    for name in (
        "core/__init__.py",
        "core/recovery_sql_snapshot.py",
        "core/sql_observation.py",
        "event_calendar/__init__.py",
        "event_calendar/sql_lifecycle.py",
    ):
        members["application/" + name] = (ROOT / name).read_bytes()
    manifest = dict(
        stage="protected-observation-binding",
        database=installation["database"],
        generation=270,
        installation=installation,
        archive_sha256=sha(packed),
        qualification_only=True,
        scope="Retained installation identity; two reader calls only, no mutation or full catalogue scan.",
    )
    stamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S%f")[:17]
    return seal_packet(evidence, members, manifest, stamp)


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
