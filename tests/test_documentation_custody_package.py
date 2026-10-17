import hashlib
import json

import pytest

from scripts import package_k98_documentation_repair as package


@pytest.fixture
def evidence(tmp_path, monkeypatch):
    sid = "S-1-5-21-1-2-3-1001"

    def row(name, directory):
        flags = "OICIID" if directory else "ID"
        return {
            "path": package.ROOT + ("/" + name if name else ""),
            "status": "OBSERVED_METADATA_ONLY",
            "directory": directory,
            "attributes": 16 if directory else 32,
            "owner_sid": sid,
            "group_sid": sid,
            "access_protected": False,
            "length": None if directory else len(b"reviewed documentation\n"),
            "sddl": f"O:{sid}G:{sid}D:AI(A;{flags};FA;;;SY)"
            f"(A;{flags};FA;;;BA)(A;{flags};0x1200a9;;;{sid})",
            "aces": [
                {
                    "sid": trustee,
                    "rights": 1179817 if trustee == sid else 2032127,
                    "type": "Allow",
                    "inherited": True,
                    "inheritance": "ContainerInherit, ObjectInherit" if directory else "None",
                    "propagation": "None",
                }
                for trustee in ("S-1-5-18", "S-1-5-32-544", sid)
            ],
        }

    names = [f"archive/file-{number}.md" for number in range(357)]
    report = {
        "stage": "COLLECTED_METADATA_NOT_REPAIR_APPROVAL",
        "host": "MINI_AMD",
        "expected_before": package.BEFORE,
        "expected_target": package.TARGET,
        "errors": [],
        "records": [row("", True), row("archive", True)] + [row(name, False) for name in names],
    }
    tree = b"".join(
        f"100644 blob {index:040x}\tdocs/task_packs/{name}\0".encode()
        for index, name in enumerate(names)
    )
    raw = b"reviewed documentation\n"

    def git(args, **kwargs):
        assert kwargs["timeout"] == 30
        if "ls-tree" in args:
            return tree
        if "cat-file" in args:
            return raw
        assert args[-1] == package.TARGET + ":scripts/K98-SourceUpdate.ps1"
        return b"# authenticated fixture library\n"

    monkeypatch.setattr(package.subprocess, "check_output", git)
    source = tmp_path / "source"
    source.mkdir()
    (source / "Repair-K98DocumentationCustody.ps1").write_text(
        "$planHash='__PLAN_SHA256__';$libraryHash='__LIBRARY_SHA256__'\n"
    )
    diagnostic = tmp_path / "diagnostic.json"

    def build():
        diagnostic.write_text(json.dumps(report))
        return package.build(diagnostic, tmp_path, tmp_path / "out", source)

    return report, build, tmp_path, raw


def test_exact_inventory_hashes_and_payload_pins(evidence):
    _, build, directory, raw = evidence
    result = build()
    folder = directory / "out"
    plan_raw = (folder / "CustodyRepairPlan.json").read_bytes()
    plan = json.loads(plan_raw)
    assert result["manifest_sha256"] == hashlib.sha256(plan_raw).hexdigest()
    assert len(plan["entries"]) == 358
    files = [entry for entry in plan["entries"] if not entry["directory"]]
    assert len(files) == 357
    assert files[0]["hashes"] == sorted(
        hashlib.sha256(value).hexdigest() for value in (raw, raw.replace(b"\n", b"\r\n"))
    )
    script = (folder / "Repair-K98DocumentationCustody.ps1").read_text()
    assert result["manifest_sha256"] in script
    assert result["library_sha256"] in script
    assert "__PLAN" not in script
    with pytest.raises(FileExistsError):
        build()


@pytest.mark.parametrize(
    "mutation",
    [
        lambda r: r.update(host="different"),
        lambda r: r.update(expected_target="0" * 40),
        lambda r: r.update(errors=["partial"]),
        lambda r: r["records"].pop(),
        lambda r: r["records"].append(r["records"][-1]),
        lambda r: r["records"][2].update(attributes=1024),
        lambda r: r["records"][2].update(length=999999),
        lambda r: r["records"][2].update(owner_sid="S-1-5-32-545"),
        lambda r: r["records"][2].update(sddl="O:BAG:BAD:(A;;FA;;;WD)"),
        lambda r: r["records"][2]["aces"][-1].update(rights=2032127),
        lambda r: r["records"][2]["aces"][-1].update(propagation="InheritOnly"),
        lambda r: r["records"][2].update(path=package.ROOT + "/untracked.md"),
    ],
)
def test_incomplete_or_unreviewed_evidence_refused_before_output(evidence, mutation):
    report, build, directory, _ = evidence
    mutation(report)
    with pytest.raises(ValueError):
        build()
    assert not (directory / "out").exists()
