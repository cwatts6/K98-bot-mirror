"""Seal one representative lab setup from the preserved read-only inventory.

This is qualification tooling, not a production migration or contract issuer.
The existing D5e database is retained with a pre-change read-only snapshot.
"""

import argparse
import ast
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.prepare_p02_observer_contract_sources import AMENDED, BASE, _definition
from scripts.verify_k98_update_pair import CONTRACT_ARCHIVE_MEMBERS
from services.catalogue_observation_dal import canonical_module
from services.catalogue_observation_query_dal import CATALOGUE_BATCH_QUERIES
from services.export_execution_dal import legacy_definition_hash
from services.export_sql_direct_permissions import application_grant_rows

DATABASE = "K98_P025_D5e_Cost_20261115"
INVENTORY = "packet-20261119175737420/boundary-20261119203920117.json"
INVENTORY_SHA = "7e4f9ec98b384fcc1b951aa3530e3da0a17521f1a666ffc6e45df603b454d65f"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", value):
        raise ValueError("Closed source-plan SQL identifier required")
    return "[" + value + "]"


def seal_packet(evidence, members, manifest, stamp):
    manifest["files"] = {name: sha(raw) for name, raw in sorted(members.items())}
    members["manifest.json"] = json.dumps(manifest, indent=2).encode()
    output = evidence / ("packet-" + stamp)
    output.mkdir()
    with zipfile.ZipFile(output / "packet.zip", "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, raw in sorted(members.items()):
            archive.writestr(name, raw)
    seal = dict(
        archive=str(output / "packet.zip"),
        sha256=sha((output / "packet.zip").read_bytes()),
        guest_directory="Q:\\P02Observer\\" + stamp,
        database=DATABASE,
    )
    (output / "seal.json").write_text(json.dumps(seal, indent=2), encoding="utf-8")
    return seal


def publisher_permission_continuation(sql_root, evidence):
    """Resume only the exact entry denial, with zero commits and settled cleanup."""
    previous = evidence / "packet-20261120094020306"
    receipt_raw = (previous / "receipt.json").read_bytes()
    assert sha(receipt_raw) == "988c869cb3f563fbe5821da564f7c0754656bab88594b62c272aaa1e6e310682"
    receipt = json.loads(receipt_raw)
    assert receipt["outcome"] == "failed" and receipt["connections_closed"] == 3
    assert receipt["publisher_dispatches"] == receipt["business_operations"] == 1
    assert receipt["publisher_commits"] == receipt["production_operations"] == 0
    assert not receipt.get("publisher_cleanup_unknown")
    assert len(receipt["checks"]) == 3 and all(r["passed"] for r in receipt["checks"][:2])
    assert not receipt["checks"][2]["passed"]
    assert receipt["first_failure"]["type"] == "ProgrammingError"
    assert (
        "EXECUTE permission was denied on the object 'sp_ExcelOutput_ByKVK'"
        in receipt["first_failure"]["detail"]
    )
    assert "(229)" in receipt["first_failure"]["detail"]
    assert (
        sha((previous / "packet.zip").read_bytes())
        == "270d49e7b7c0508de4c6f18912ce2c50a958e26b851120d759791c41f4bdc903"
    )
    with zipfile.ZipFile(previous / "packet.zip") as archive:
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["stage"] == "representative-publisher-overlap"
        assert manifest["database"] == DATABASE and manifest["reuse"]["generation"] == 238
        assert set(archive.namelist()) == {"manifest.json", *manifest["files"]}
        members = {name: archive.read(name) for name in manifest["files"]}
        assert all(sha(raw) == manifest["files"][name] for name, raw in members.items())
    helper = "qualification/p02_observer/publisher_overlap.py"
    for name, raw in members.items():
        if name.startswith("bot/"):
            assert (ROOT / name[4:]).read_bytes() == raw, name
        elif name.startswith("qualification/") and name != helper:
            assert (sql_root / name).read_bytes() == raw, name
    members[helper] = (sql_root / helper).read_bytes()
    members["evidence/failed-publisher-entry-receipt.json"] = receipt_raw
    manifest["reuse"]["receipt_sha256"] = sha(receipt_raw)
    manifest["publisher_entry_permission"] = (
        "One child EXECUTE grant inside the publication transaction; revoke before commit; "
        "rollback removes it on failure. Lab fixture only, no parent-flow acceptance."
    )
    stamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S%f")[:17]
    return seal_packet(evidence, members, manifest, stamp)


def publisher_after_commit_continuation(sql_root, evidence):
    """Retain the committed actor-first case; dispatch only the unfinished order."""
    previous = evidence / "packet-20261120095412651"
    expected = {
        "receipt.json": "bec696ca79c8ad7a35eb2efe6bfaa120d14ac10ec52ad7f47a38dcfc199ae23f",
        "publisher-actor-first-commit.json": "427dbe8c594f24e8ca8aa05825a606a18179ff47beebf205bec9eba69a5fc794",
        "publisher-actor-first-output.json": "30b67b327427d9dfd7967d9f67486ba8fc6b8bfeec1af393317d7f5a677de2dc",
        "publisher-actor-first-observation.json": "3509f14f53fc76c7d63c05f9e1c0743fab444668c573e5802c9c537e4b2e2468",
    }
    saved = {name: (previous / name).read_bytes() for name in expected}
    assert all(sha(raw) == expected[name] for name, raw in saved.items())
    receipt = json.loads(saved["receipt.json"])
    assert receipt["outcome"] == "failed" and receipt["connections_closed"] == 4
    assert receipt["publisher_dispatches"] == receipt["publisher_commits"] == 1
    assert receipt["business_operations"] == 1 and receipt["production_operations"] == 0
    assert not receipt.get("publisher_cleanup_unknown")
    assert len(receipt["checks"]) == 3 and all(r["passed"] for r in receipt["checks"][:2])
    assert not receipt["checks"][2]["passed"]
    assert receipt["first_failure"]["type"] == "AssertionError"
    facts = ast.literal_eval(receipt["first_failure"]["detail"])
    assert facts["order"] == "actor-first" and facts["committed_once"]
    assert facts["cleanup"] == "acknowledged" and facts["queued_work_unchanged"]
    assert facts["observation_seconds"] < 15 and facts["total_seconds"] < 45
    commit = json.loads(saved["publisher-actor-first-commit.json"])
    output = json.loads(saved["publisher-actor-first-output.json"])
    observed = json.loads(saved["publisher-actor-first-observation.json"])
    assert (
        commit["committed"]
        and commit["publisher_cleanup"] == commit["observer_cleanup"] == "acknowledged"
    )
    assert commit["temporary_child_entry"] == "transaction-local grant removed before commit"
    assert len(output["rows"]) == facts["output_rows"] == 415
    assert observed["boundary"]["generation"] == facts["observation_generation"] == 254
    slow = [r for r in observed["timings"] if r["native_seconds"] > 0.250]
    assert (
        len(slow) == 1
        and slow[0]["statement_sha256"]
        == "75da817e053978bffe3d33436b57e574307f585f23980e761f964b5751aac5e8"
    )
    assert (
        sha((previous / "packet.zip").read_bytes())
        == "6ad2cce7a0e4e642547ba4ad1772af929f409730de3c41f0b1c66de67333015a"
    )
    with zipfile.ZipFile(previous / "packet.zip") as archive:
        manifest = json.loads(archive.read("manifest.json"))
        assert set(archive.namelist()) == {"manifest.json", *manifest["files"]}
        members = {name: archive.read(name) for name in manifest["files"]}
        assert all(sha(raw) == manifest["files"][name] for name, raw in members.items())
    batch_path = "bot/services/catalogue_observation_batches.py"
    for name, raw in members.items():
        if name.startswith("bot/") and name != batch_path:
            assert (ROOT / name[4:]).read_bytes() == raw, name
    old_tree, new_tree = (
        ast.parse(raw) for raw in (members[batch_path], (ROOT / batch_path[4:]).read_bytes())
    )
    widths = []
    for tree in (old_tree, new_tree):
        node = next(
            n
            for n in tree.body
            if isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "_WIDTHS" for t in n.targets)
        )
        widths.append(ast.literal_eval(node.value))
        tree.body.remove(node)
    assert "metadata.objects" not in widths[0]
    widths[0]["metadata.objects"] = 192
    assert widths[0] == widths[1] and ast.dump(old_tree) == ast.dump(new_tree)
    members[batch_path] = (ROOT / batch_path[4:]).read_bytes()
    for name in ("representative.py", "publisher_overlap.py"):
        path = "qualification/p02_observer/" + name
        members[path] = (sql_root / path).read_bytes()
    for name, raw in saved.items():
        members[
            "evidence/" + ("failed-publisher-cost-receipt.json" if name == "receipt.json" else name)
        ] = raw
    members["evidence/representative-before.json"] = json.dumps(output["state"], indent=2).encode()
    for name in (
        "decomposed-collector-equivalence.json",
        "post-publication-collector-equivalence.json",
    ):
        raw = (evidence / name).read_bytes()
        proof = json.loads(raw)
        assert proof["passed"] and proof["rows_and_multiplicities_equal"]
        assert proof["batching_sha256"] == sha(members[batch_path])
        assert proof["source_sha256"] == sha(members["bot/services/export_execution_dal.py"])
        assert proof["source_native_sha256"] == sha(
            members["evidence/native-observation.json"]
            if name.startswith("decomposed")
            else saved["publisher-actor-first-observation.json"]
        )
        assert proof["after_queries"] == 125
        members["evidence/" + name] = raw
    from services.export_execution_dal import _METADATA_QUERIES

    query = (
        "WITH required AS (SELECT OBJECT_ID(value) AS object_id FROM OPENJSON(?)) "
        + _METADATA_QUERIES["objects"]
    )
    assert sha(query.encode()) == slow[0]["statement_sha256"]
    members["source/object-query.sql"] = query.encode()
    manifest["resume_after_actor_first"] = True
    manifest["reuse"].update(
        receipt_sha256=expected["receipt.json"],
        generation=254,
        observed_fingerprint=facts["observed_fingerprint"],
    )
    assert observed["boundary"]["identity"][9:] == manifest["reuse"]["sequence_identity"]
    stamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S%f")[:17]
    return seal_packet(evidence, members, manifest, stamp)


def publisher_final_read_packet(sql_root, evidence):
    """Zero business dispatches: finish observation after the two saved commits."""
    previous = evidence / "packet-20261120100655925"
    expected = {
        "receipt.json": "dd26939b935db14efe0c90beb7fbe5b31299cc2f2ceee3718a8604e0036bcbef",
        "publisher-observer-first-commit.json": "2a06c5b994c716ba29c69e2b1b85702cc72d710228859d6399a6c924b76a72ca",
        "publisher-observer-first-output.json": "b18c1e5cb04b839c9ff91e6170b85149c250009d2e33f3cc59b2e241cf859f79",
        "publisher-failure-state.json": "023112ee97a9bbee750b1b7d65f8486c62ba7b5a98289851a7ff5635a41e59e0",
        "publisher-object-read.json": "7579c9b66391f1bb93404e0faeef2b6fa7ac5f1797c4cc11508578d33756aeda",
    }
    saved = {name: (previous / name).read_bytes() for name in expected}
    assert all(sha(raw) == expected[name] for name, raw in saved.items())
    receipt = json.loads(saved["receipt.json"])
    assert receipt["outcome"] == "failed" and receipt["connections_closed"] == 4
    assert (
        receipt["publisher_dispatches"]
        == receipt["publisher_commits"]
        == receipt["retained_publications"]
        == 1
    )
    assert receipt["business_operations"] == 1 and receipt["production_operations"] == 0
    assert receipt["remaining_orders"] == ["observer-first"] and not receipt.get(
        "publisher_cleanup_unknown"
    )
    assert len(receipt["checks"]) == 4 and all(r["passed"] for r in receipt["checks"][:3])
    assert not receipt["checks"][3]["passed"]
    assert receipt["first_failure"]["type"] == "AssertionError"
    assert "assert output == first_output" in receipt["first_failure"]["traceback"]
    output = json.loads(saved["publisher-observer-first-output.json"])
    state = json.loads(saved["publisher-failure-state.json"])
    commit = json.loads(saved["publisher-observer-first-commit.json"])
    assert (
        commit["committed"]
        and commit["publisher_cleanup"] == commit["observer_cleanup"] == "acknowledged"
    )
    assert state["business_state"] == output["state"] and state["direct_entry_permissions"] == []
    assert len(state["sequence"]) == 1
    sequence = state["sequence"][0]
    assert sequence["current_value"] == sequence["last_used_value"] == 270
    assert (
        sha((previous / "packet.zip").read_bytes())
        == "061f5a960aa0e68d413da740ec11ef485cb9bbc6a579cedc09a660551bf6e83e"
    )
    with zipfile.ZipFile(previous / "packet.zip") as archive:
        manifest = json.loads(archive.read("manifest.json"))
        assert set(archive.namelist()) == {"manifest.json", *manifest["files"]}
        members = {name: archive.read(name) for name in manifest["files"]}
        assert all(sha(raw) == manifest["files"][name] for name, raw in members.items())
    for name, raw in members.items():
        if name.startswith("bot/"):
            assert (ROOT / name[4:]).read_bytes() == raw, name
    for name in ("representative.py", "publisher_overlap.py"):
        path = "qualification/p02_observer/" + name
        members[path] = (sql_root / path).read_bytes()
    for name, raw in saved.items():
        members[
            "evidence/"
            + ("failed-second-publisher-receipt.json" if name == "receipt.json" else name)
        ] = raw
    comparison = (evidence / "publisher-rank-comparison-20261120.json").read_bytes()
    assert sha(comparison) == "6c1c6ee86cd384f37cec54004eec99a12a3db2422fd0c9b627e49b77d724f4d2"
    members["evidence/publisher-rank-comparison.json"] = comparison
    members["evidence/representative-before.json"] = json.dumps(output["state"], indent=2).encode()
    assert [sequence[k] for k in ("object_id", "create_date", "modify_date")] == manifest["reuse"][
        "sequence_identity"
    ]
    manifest["stage"] = "representative-publisher-final-read"
    manifest.pop("resume_after_actor_first")
    manifest["reuse"].update(receipt_sha256=expected["receipt.json"], generation=270)
    stamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S%f")[:17]
    return seal_packet(evidence, members, manifest, stamp)


def combined_read_packet(sql_root, evidence):
    """Recheck only combined query transport against the passed native read."""
    previous = evidence / "packet-20261120101623191"
    expected = {
        "packet.zip": "dd4feb6474437b340aeea6f311d9c1cf51c75ebcca5727fb5d4560645ad8526e",
        "receipt.json": "e47bf23c0cb17be225eb74f1455ef4439002b262e8e9edfe2554a860e30142bc",
        "publisher-final-observation.json": "28e527331ad7a7bc68647baacd11b694459b93405d37939c4c26e6b1c514c6b8",
    }
    saved = {name: (previous / name).read_bytes() for name in expected}
    assert all(sha(raw) == expected[name] for name, raw in saved.items())
    receipt = json.loads(saved["receipt.json"])
    assert receipt["outcome"] == "representative-publisher-poststate-passed"
    assert receipt["connections_closed"] == 2 and all(r["passed"] for r in receipt["checks"])
    assert receipt["business_operations"] == receipt["production_operations"] == 0
    assert receipt["publisher_dispatches"] == receipt["publisher_commits"] == 0
    with zipfile.ZipFile(previous / "packet.zip") as archive:
        manifest = json.loads(archive.read("manifest.json"))
        assert set(archive.namelist()) == {"manifest.json", *manifest["files"]}
        members = {name: archive.read(name) for name in manifest["files"]}
        assert all(sha(raw) == manifest["files"][name] for name, raw in members.items())
    for name, raw in members.items():
        if name.startswith("bot/"):
            assert (ROOT / name[4:]).read_bytes() == raw, name
    for name in ("representative.py", "combined_read.py"):
        path = "qualification/p02_observer/" + name
        members[path] = (sql_root / path).read_bytes()
    for name in (
        "services/catalogue_observation_batch_dal.py",
        "scripts/verify_k98_running_release.py",
    ):
        members["bot/" + name] = (ROOT / name).read_bytes()
    members["evidence/combined-baseline.json"] = saved["publisher-final-observation.json"]
    members["evidence/passed-final-read-receipt.json"] = saved["receipt.json"]
    proof_raw = (evidence / "combined-collector-proof-20261120103100982.json").read_bytes()
    proof = json.loads(proof_raw)
    assert proof["passed"] and proof["complete_rows_permissions_lifecycle_equal"]
    assert proof["readonly_branch_returns_before_publication"]
    for field, name in (
        ("adapter_sha256", "bot/services/catalogue_observation_batch_dal.py"),
        ("harness_sha256", "qualification/p02_observer/representative.py"),
        ("helper_sha256", "qualification/p02_observer/combined_read.py"),
        ("baseline_sha256", "evidence/combined-baseline.json"),
    ):
        assert proof[field] == sha(members[name]), field
    assert proof["harness_cases"] == ["pass", "cost-failure", "first-error-preserved"]
    members["evidence/combined-offline-proof.json"] = proof_raw
    manifest["stage"] = "representative-combined-read"
    manifest["reuse"]["receipt_sha256"] = expected["receipt.json"]
    manifest["scope"] = (
        "One read-only full collector with paired query/boundary dispatch and the actual "
        "verifier budget owner; no publication, maintenance, installation or permission change."
    )
    stamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S%f")[:17]
    return seal_packet(evidence, members, manifest, stamp)


def combined_categories_packet(sql_root, evidence, proof_path):
    """Retain full parity; qualify only the two categories that missed cost."""
    previous = evidence / "packet-20261120103225699"
    hashes = {
        "packet.zip": "1f18e6fa07bead25e09ee6df1c993ae8d02e06b112162da3c8b821e2ff660526",
        "receipt.json": "97fe418652c62dc940e2adc915bbe575f5e43866c54f5c7fad1b73d7a1662063",
        "catalogue-cost-result.json": "e1e416cfebb4ad03611e8f4a70c97b26928cd924f768f473f22f60d8b74cb8bf",
        "catalogue-timings.json": "f366ed08386ac07e038f55910100a257330c98546b17ffcd071d2840b79934b4",
        "combined-observation.json": "de8bb1eb5acfdf0e1ae8a3ecdfd9ecebb510593ecb6bf23c35d9dac1ddd138b4",
        "combined-budget.json": "1f90e677a4e8b3a7f25ac6b88a62bd0c655c7e023be2f51447b10fc47bacd93a",
    }
    saved = {name: (previous / name).read_bytes() for name in hashes}
    assert all(sha(raw) == hashes[name] for name, raw in saved.items())
    receipt = json.loads(saved["receipt.json"])
    cost = json.loads(saved["catalogue-cost-result.json"])
    timings = json.loads(saved["catalogue-timings.json"])
    budget = json.loads(saved["combined-budget.json"])
    assert receipt["outcome"] == "failed" and receipt["connections_closed"] == 2
    assert len(receipt["checks"]) == 2 and receipt["checks"][0]["passed"]
    assert not receipt["checks"][1]["passed"]
    assert receipt["first_failure"]["type"] == "AssertionError"
    assert ast.literal_eval(receipt["first_failure"]["detail"]) == cost
    assert receipt["business_operations"] == receipt["production_operations"] == 0
    assert cost["all_rows_permissions_lifecycle_equal"] and cost["observation_seconds"] < 15
    assert cost["generation"] == 270 and cost["cleanup"] == "acknowledged"
    assert budget["first_failure"] is None and all(c["closed"] for c in budget["connections"])
    assert len(timings) == 128 and len(budget["statements"]) == 129
    slow = [r for r in timings if r["native_seconds"] > 0.250]
    assert [r["ordinal"] for r in slow] == [66, 67, 120]
    assert {r["statement_sha256"] for r in slow} == {
        "6efc90d4339a8b0f2ff8fb65764f2d5c58894c9790e12cc9c25458efb66b5a8f",
        "1c22b9742223760ccf69f17c1e48edf17901a2f99943365fc5c80ca8151350dd",
    }
    with zipfile.ZipFile(previous / "packet.zip") as archive:
        manifest = json.loads(archive.read("manifest.json"))
        assert set(archive.namelist()) == {"manifest.json", *manifest["files"]}
        members = {name: archive.read(name) for name in manifest["files"]}
        assert all(sha(raw) == manifest["files"][name] for name, raw in members.items())
    changed = {"services/catalogue_observation_batches.py", "services/export_execution_dal.py"}
    for name, raw in list(members.items()):
        if name.startswith("bot/"):
            current = (ROOT / name[4:]).read_bytes()
            if name[4:] not in changed:
                assert current == raw, name
            else:
                old, new = ast.parse(raw), ast.parse(current)
                if name.endswith("export_execution_dal.py"):

                    def strings(tree):
                        return [
                            n.value
                            for n in ast.walk(tree)
                            if isinstance(n, ast.Constant) and isinstance(n.value, str)
                        ]

                    assert strings(old) == strings(new)  # All query text/fields unchanged.
                else:

                    def values(tree):
                        return {
                            n.targets[0].id: ast.literal_eval(n.value)
                            for n in tree.body
                            if isinstance(n, ast.Assign)
                        }

                    before, after = values(old), values(new)
                    assert all(after[k] == v for k, v in before.items())
                    assert after["_COMBINED_WIDTHS"] == {
                        "metadata.indexes": 64,
                        "identity.default_constraints": 128,
                    }
                members[name] = current
    for name in ("representative.py", "combined_read.py"):
        path = "qualification/p02_observer/" + name
        members[path] = (sql_root / path).read_bytes()
    proof_path = Path(proof_path).resolve()
    assert proof_path.parent == evidence.resolve()
    proof_raw = proof_path.read_bytes()
    proof = json.loads(proof_raw)
    assert proof["passed"] and proof["complete_rows_permissions_lifecycle_equal"]
    assert proof["odbc_dispatches"] == 133 and proof["focused_dispatches"] == 14
    assert proof["harness_cases"] == [
        "full-pass",
        "focused-pass",
        "cost-failure",
        "first-error-preserved",
    ]
    assert proof["readonly_branch_returns_before_publication"]
    for field, name in (
        ("collector_sha256", "bot/services/export_execution_dal.py"),
        ("batching_sha256", "bot/services/catalogue_observation_batches.py"),
        ("adapter_sha256", "bot/services/catalogue_observation_batch_dal.py"),
        ("harness_sha256", "qualification/p02_observer/representative.py"),
        ("helper_sha256", "qualification/p02_observer/combined_read.py"),
        ("baseline_sha256", "evidence/combined-baseline.json"),
    ):
        assert proof[field] == sha(members[name]), field
    members["evidence/combined-categories-offline-proof.json"] = proof_raw
    for name in (
        "receipt.json",
        "catalogue-cost-result.json",
        "catalogue-timings.json",
        "combined-budget.json",
    ):
        members["evidence/failed-combined-" + name] = saved[name]
    manifest["stage"] = "representative-combined-categories"
    manifest["reuse"]["receipt_sha256"] = hashes["receipt.json"]
    manifest["scope"] = (
        "Only the two remaining combined catalogue categories; no full scan, installation, permissions, publication or maintenance."
    )
    stamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S%f")[:17]
    return seal_packet(evidence, members, manifest, stamp)


def build(sql_root, resume_from=None, combined_proof=None):
    sql_root = Path(sql_root).resolve()
    evidence = ROOT / ".codex_artifacts/p02-observer-proof-20261119"
    if (
        resume_from is not None
        and Path(resume_from).resolve() == (evidence / "packet-20261120103225699").resolve()
    ):
        return combined_categories_packet(sql_root, evidence, combined_proof)
    if (
        resume_from is not None
        and Path(resume_from).resolve() == (evidence / "packet-20261120101623191").resolve()
    ):
        return combined_read_packet(sql_root, evidence)
    if (
        resume_from is not None
        and Path(resume_from).resolve() == (evidence / "packet-20261120100655925").resolve()
    ):
        return publisher_final_read_packet(sql_root, evidence)
    if (
        resume_from is not None
        and Path(resume_from).resolve() == (evidence / "packet-20261120095412651").resolve()
    ):
        return publisher_after_commit_continuation(sql_root, evidence)
    if (
        resume_from is not None
        and Path(resume_from).resolve() == (evidence / "packet-20261120094020306").resolve()
    ):
        return publisher_permission_continuation(sql_root, evidence)
    raw = (evidence / INVENTORY).read_bytes()
    if sha(raw) != INVENTORY_SHA:
        raise ValueError("Representative inventory changed")
    inventory = json.loads(raw)
    prior = next(row for row in inventory["databases"] if row["database"] == DATABASE)
    assert inventory["connections_closed"] == 2 and inventory["sql_mutations"] == 0
    assert not any(k in prior for k in ("failure", "cleanup_failure"))
    assert prior["active_sessions"] == prior["observer_objects"] == prior["lab_actor"] == []
    assert all(r["State"] == "complete" for r in prior["maintenance"] + prior["kvk_work"])
    stamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S%f")[:17]
    snapshot = "K98_P02Observer_D5eBefore_" + stamp
    members = {"evidence/representative-inventory.json": raw}
    failed_path = evidence / "packet-20261119205253436/receipt.json"
    failed_raw = failed_path.read_bytes()
    if sha(failed_raw) != "dfdaec6d401a7e94d3f6321f749172e37edd6fcf5bc5ef6fe717d6f28109a833":
        raise ValueError("Retained representative preflight failure differs")
    failure = json.loads(failed_raw)
    assert failure["outcome"] == "failed" and failure["connections_closed"] == 1
    assert len(failure["checks"]) == 1 and not failure["checks"][0]["passed"]
    members["evidence/failed-name-preflight.json"] = failed_raw
    modules = {r["ObjectName"]: r for r in prior["selected_modules"]}
    old = json.loads((ROOT / "deploy/p02_d4_legacy_source.json").read_bytes())
    old_modules = {r["name"]: r for r in old["modules"]}
    install = []
    for name in sorted(AMENDED):
        relative = "sql_schema/" + name + ".StoredProcedure.sql"
        base = subprocess.check_output(
            [
                "git",
                "-c",
                "safe.directory=" + str(sql_root),
                "-C",
                str(sql_root),
                "show",
                BASE + ":" + relative,
            ],
            timeout=15,
        )
        if sha(base) != old_modules[name]["source_sha256"]:
            raise ValueError("Unbound predecessor SQL root: " + name)
        if legacy_definition_hash(modules[name]["definition"]) not in (
            old_modules[name]["definition_sha256"],
            *old_modules[name].get("compatible_definition_sha256", []),
        ):
            raise ValueError("Installed representative root differs from D4: " + name)
        member = "sql/" + name + ".StoredProcedure.sql"
        body = _definition((sql_root / relative).read_bytes(), "PROCEDURE")
        members[member] = body.encode()
        install.append(member)
    protocol = json.loads((evidence / "source-plan-02/p02_observer_protocol.json").read_bytes())
    protocol_sources = []
    for row in protocol["modules"]:
        source = (sql_root / row["path"]).read_bytes()
        assert sha(source) == row["raw_source_sha256"]
        member = "sql/" + Path(row["path"]).name
        members[member] = source
        protocol_sources.append(member)
    sequence = "sql/dbo.P02ObservationGeneration.Sequence.sql"
    members[sequence] = (sql_root / protocol["sequence"]["path"]).read_bytes()
    assert sha(members[sequence]) == protocol["sequence"]["raw_source_sha256"]
    order = [sequence] + [n for n in protocol_sources if ".StoredProcedure." in n]
    order += [n for n in protocol_sources if ".Trigger." in n]
    order += install + [n for n in protocol_sources if ".DatabaseTrigger." in n]
    # Only the existing, source-pinned application grants, on one new lab user.
    grant_plan = json.loads((ROOT / "deploy/s11_application_grants.json").read_bytes())
    application_grant_rows()  # Authenticate the existing reviewed grant resource.
    grant_lines = [
        "CREATE USER [S11_ExportApplication_P02Qual] FOR LOGIN [S11_ExportApplication_P02Qual] WITH DEFAULT_SCHEMA=[dbo];"
    ]
    for role in grant_plan["roles"]:
        grant_lines.append(
            "ALTER ROLE " + identifier(role) + " ADD MEMBER [S11_ExportApplication_P02Qual];"
        )
    for permission in grant_plan["database_permissions"]:
        assert permission in {"CONNECT", "VIEW DEFINITION"}
        grant_lines.append("GRANT " + permission + " TO [S11_ExportApplication_P02Qual];")
    for row in grant_plan["grants"]:
        assert row["permission"] in {
            "SELECT",
            "INSERT",
            "UPDATE",
            "DELETE",
            "EXECUTE",
            "REFERENCES",
        }
        target = ".".join(identifier(part) for part in row["object"].split("."))
        column = " (" + identifier(row["column"]) + ")" if "column" in row else ""
        grant_lines.append(
            "GRANT "
            + row["permission"]
            + " ON OBJECT::"
            + target
            + column
            + " TO [S11_ExportApplication_P02Qual];"
        )
    grant_lines.append(
        (sql_root / "qualification/p02_observer/lifecycle_permissions.sql").read_text()
    )
    members["sql/lab-application-grants.sql"] = ("\n".join(grant_lines) + "\n").encode()
    order.append("sql/lab-application-grants.sql")
    members["sql/preserve-d5e.sql"] = (
        "CREATE DATABASE ["
        + snapshot
        + "] ON (NAME=N'ROK_TRACKER',FILENAME=N'"
        + "Q:\\D5eCost-20261115\\"
        + snapshot
        + ".ss') AS SNAPSHOT OF ["
        + DATABASE
        + "];\n"
    ).encode()
    names = set(CONTRACT_ARCHIVE_MEMBERS) | {
        "services/catalogue_observation_dal.py",
        "services/catalogue_observation_batches.py",
        "services/catalogue_observation_query_dal.py",
        "services/catalogue_observation_columns_dal.py",
        "scripts/inspect_p02_observer_query_plans.py",
        "services/application_observation_admission.py",
        "event_calendar/sql_lifecycle.py",
        "core/recovery_sql_snapshot.py",
        "core/sql_observation.py",
        "core/sql_operation_policy.py",
        "services/legacy_snapshot_admission.py",
        "services/sql_lock_holder_diagnostics.py",
    }
    for name in sorted(names):
        members["bot/" + name] = (ROOT / name).read_bytes()
    for name in ("representative.py", "publisher_overlap.py"):
        path = "qualification/p02_observer/" + name
        members[path] = (sql_root / path).read_bytes()
    members["source/protocol.json"] = json.dumps(protocol).encode()
    scope = json.loads(
        (evidence / "source-plan-02/p02_observer_activation_scope.json").read_bytes()
    )
    members["source/activation-scope.json"] = json.dumps(scope).encode()
    # Whole-database collection does not use a lab alias to bypass the protected
    # ROK_TRACKER validator. Final protected-contract acceptance is a later gate.
    manifest = dict(
        version=1,
        stage="representative-install-and-recovery",
        database=DATABASE,
        snapshot=snapshot,
        install_sources=order,
        inventory_sha256=INVENTORY_SHA,
        root_definitions={
            name: canonical_module(members["sql/" + name + ".StoredProcedure.sql"].decode())
            for name in AMENDED
        },
        files={name: sha(raw) for name, raw in sorted(members.items())},
    )
    if resume_from is not None:
        previous = Path(resume_from).resolve()
        cost = previous == (evidence / "packet-20261119210128575").resolve()
        batched = previous == (evidence / "packet-20261119211229214").resolve()
        corrected = previous == (evidence / "packet-20261119212931149").resolve()
        publisher = previous == (evidence / "packet-20261120092046573").resolve()
        identity_columns = (
            publisher or previous == (evidence / "packet-20261120091357000").resolve()
        )
        identity_queries = (
            identity_columns or previous == (evidence / "packet-20261120090135760").resolve()
        )
        margin_batches = (
            identity_queries or previous == (evidence / "packet-20261120085503978").resolve()
        )
        authority_batches = (
            margin_batches or previous == (evidence / "packet-20261120085133167").resolve()
        )
        full_cost = (
            authority_batches or previous == (evidence / "packet-20261120084435562").resolve()
        )
        reduced_columns = full_cost or previous == (evidence / "packet-20261119221348528").resolve()
        direct_columns = (
            reduced_columns or previous == (evidence / "packet-20261119220945942").resolve()
        )
        column_plan = (
            direct_columns or previous == (evidence / "packet-20261119215320782").resolve()
        )
        columns = column_plan or previous == (evidence / "packet-20261119214319853").resolve()
        if (
            not (cost or batched or corrected or columns)
            and previous != (evidence / "packet-20261119205611983").resolve()
        ):
            raise ValueError("Only the verified representative installation can be resumed")
        receipt_raw = (previous / "receipt.json").read_bytes()
        expected_receipt = (
            "a79b1428eb52fc7b561fb21a6a99d949cde7e897d5a387be22e87532720c772e"
            if reduced_columns
            else (
                "17bfae3965c7d086e739871fcb9f4802295afe65e434f390237c4fbfa462f98e"
                if direct_columns
                else (
                    "201cdb9d145c3fd1efbe2f042d32132b8e0914f9ca52075f4e8001cd9ca8dbe0"
                    if column_plan
                    else (
                        "6a83c38f78aed7ab4bdadbd7a3669691100ddea9eecde4defac7001a8d475faa"
                        if columns
                        else (
                            "7fc6fbdd5d4c0f725a4810f576417f5cb372110ca5cd28dc432e72c0378b3bd7"
                            if corrected
                            else (
                                "308bea9981d7458fdf34da82e8717c9b46c57fbe8f2b537adb88f699c619ce58"
                                if batched
                                else (
                                    "32bfeb1b097c4e1f4ed565ba7c33117bb1ae32820a5b7f9adaefa804caed0450"
                                    if cost
                                    else "9e7e67fd4914cec25c3451a140122a1949821f962ce25c6d25fa3d9259f443ca"
                                )
                            )
                        )
                    )
                )
            )
        )
        if full_cost:
            expected_receipt = "0073eaad0170230a692f9ce8ce16161ba02c43bf03363ac731b66651566e02bc"
        if authority_batches:
            expected_receipt = "66adb2d10fd6731458aa623f5822f5c274f18e5bee5c127ae3a4fcc8d1d582cf"
        if margin_batches:
            expected_receipt = "75a5ac439358bf091b48871f45d8b4d799123ab1792a905bc2527d2f4a36b572"
        if identity_queries:
            expected_receipt = "2e801f8e053d56c3076dde419451ee0fa85e830e6727d0c7219581f63464c7d2"
        if identity_columns:
            expected_receipt = "ecf21b2659155aab4425a07bd5d7e3ecac035f242391b605a875a7ce2667268f"
        if publisher:
            expected_receipt = "c788b6d6fc66e29b5cd62158b933b16eb1c71d5ec4540f9694267baa330f5347"
        if sha(receipt_raw) != expected_receipt:
            raise ValueError("Retained installation receipt differs")
        receipt = json.loads(receipt_raw)
        if publisher:
            assert (
                receipt["outcome"] == "representative-query-correction-passed"
                and receipt["connections_closed"] == 2
            )
            assert len(receipt["checks"]) == 2 and all(r["passed"] for r in receipt["checks"])
            assert receipt["checks"][1]["facts"]["categories"] == {"identity.columns": 4949}
        elif authority_batches:
            assert receipt["outcome"] == "failed" and receipt["connections_closed"] == 2
            assert len(receipt["checks"]) == 2 and receipt["checks"][0]["passed"]
            assert receipt["checks"][1]["name"] == (
                "identity-query-parity-and-cost"
                if identity_columns
                else "representative-per-statement-cost-gate"
            )
            assert not receipt["checks"][1]["passed"]
            assert receipt["first_failure"]["type"] == "AssertionError"
        elif full_cost:
            assert receipt["outcome"] == "representative-query-correction-passed"
            assert receipt["connections_closed"] == 2
            assert len(receipt["checks"]) == 2 and all(r["passed"] for r in receipt["checks"])
            assert receipt["checks"][1]["name"] == "decomposed-column-parity-and-cost"
        elif batched or corrected or columns:
            assert receipt["outcome"] == "failed" and receipt["connections_closed"] == 2
            assert len(receipt["checks"]) == 2 and receipt["checks"][0]["passed"]
            assert receipt["checks"][1]["name"] == (
                "decomposed-column-parity-and-cost"
                if column_plan
                else (
                    "four-corrected-catalogue-query-parity-and-cost"
                    if columns
                    else "representative-per-statement-cost-gate"
                )
            )
            assert not receipt["checks"][1]["passed"]
            assert receipt["first_failure"]["type"] == "AssertionError"
        elif cost:
            assert (
                receipt["outcome"] == "representative-reader-cases-passed"
                and receipt["connections_closed"] == 4
            )
            assert len(receipt["checks"]) == 4 and all(r["passed"] for r in receipt["checks"])
        else:
            assert receipt["outcome"] == "failed" and receipt["connections_closed"] == 3
            assert len(receipt["checks"]) == 3 and all(r["passed"] for r in receipt["checks"][:2])
            assert (
                receipt["first_failure"]["detail"]
                == "Explicit supported fingerprint format and pinned scope required."
            )
        with zipfile.ZipFile(previous / "packet.zip") as installed:
            prior_manifest = json.loads(installed.read("manifest.json"))
            if columns:
                expected_archive = (
                    "0c3682ddcc20f811933ebbbfed7920af0f89b3da1f2db3132f95bf46e72f3076"
                    if reduced_columns
                    else (
                        "d472d20c269616640af3f6c8848580ae26f131913d2ee516f2d4c4beb12cd6bb"
                        if direct_columns
                        else (
                            "49af59742449d20e89e59da9d1f77efb4f51adb548e415768c285bdfca4b213b"
                            if column_plan
                            else "5b3cc258bfb52e312045f862c0a134b51a4d0b3dd31f5032226b7b7e3767b3d3"
                        )
                    )
                )
                if full_cost:
                    expected_archive = (
                        "be754c53a674e6b48d4d442104adf3fcefb7df1c603f96108129e4d47ce7042c"
                    )
                    if authority_batches:
                        expected_archive = (
                            "b1c120b2d73de77bcf7aa8ba842995025e886559a2886a190477152e0cac492c"
                        )
                    if margin_batches:
                        expected_archive = (
                            "3e95e38e2a7dd7ca43b369c6158fe45048c623b807f4d26ab762d3a853cfdf92"
                        )
                    if identity_queries:
                        expected_archive = (
                            "1db8f707cb590975aaa71031bd6740bdcc0bd698b2f16cc423f41ce498737c3b"
                        )
                    if identity_columns:
                        expected_archive = (
                            "dae92076de4ad0bf84096166caa10ba929d738e9d8cb2ae46982ef5542e9659a"
                        )
                    if publisher:
                        expected_archive = (
                            "6a051fa7150f31cb1397575e75415749b901edb6a0b48d1598ce821917611a3e"
                        )
                    for name in (
                        "export_execution_dal",
                        "catalogue_observation_batches",
                        "catalogue_observation_query_dal",
                        "catalogue_observation_columns_dal",
                    ):
                        path = "bot/services/" + name + ".py"
                        if (
                            identity_columns
                            and not publisher
                            and name == "catalogue_observation_columns_dal"
                        ):
                            trees = [
                                ast.parse(raw) for raw in (installed.read(path), members[path])
                            ]
                            trees[1].body = [
                                n
                                for n in trees[1].body
                                if not (
                                    isinstance(n, ast.FunctionDef)
                                    and n.name == "identity_column_query"
                                )
                            ]
                            assert ast.dump(trees[0]) == ast.dump(trees[1])
                            continue
                        if (
                            identity_queries
                            and not publisher
                            and name
                            in {
                                "export_execution_dal",
                                "catalogue_observation_query_dal",
                            }
                        ):
                            # Default dispatch equivalence and the complete candidate
                            # projection are authenticated below; original overrides
                            # are independently checked unchanged against this archive.
                            continue
                        if (
                            authority_batches
                            and (not identity_queries or identity_columns)
                            and not publisher
                            and name == "catalogue_observation_batches"
                        ):
                            trees = [
                                ast.parse(raw) for raw in (installed.read(path), members[path])
                            ]
                            widths = []
                            for tree in trees:
                                node = next(
                                    n
                                    for n in tree.body
                                    if isinstance(n, ast.Assign)
                                    and any(
                                        isinstance(t, ast.Name) and t.id == "_WIDTHS"
                                        for t in n.targets
                                    )
                                )
                                widths.append(ast.literal_eval(node.value))
                                tree.body.remove(node)
                            assert ast.dump(trees[0]) == ast.dump(trees[1])
                            if identity_columns:
                                assert widths[0]["identity.columns"] == 64
                                widths[0]["identity.columns"] = 48
                            elif margin_batches:
                                assert widths[0]["metadata.indexes"] == 192
                                assert (
                                    "metadata.checks" not in widths[0]
                                    and "identity.checks" not in widths[0]
                                )
                                widths[0].update(
                                    {
                                        "metadata.indexes": 96,
                                        "metadata.checks": 128,
                                        "identity.checks": 128,
                                    }
                                )
                            else:
                                assert (
                                    widths[0]["object_permissions"]
                                    == widths[0]["column_permissions"]
                                    == 128
                                )
                                widths[0].update(object_permissions=32, column_permissions=64)
                            assert widths[0] == widths[1]
                            continue
                        assert members[path] == installed.read(path), path
                assert sha((previous / "packet.zip").read_bytes()) == expected_archive
                tree = ast.parse(installed.read("bot/services/catalogue_observation_query_dal.py"))
                assert all(isinstance(node, (ast.Assign, ast.Expr)) for node in tree.body)
                assert not any(
                    isinstance(node, (ast.Call, ast.Attribute)) for node in ast.walk(tree)
                )
                inherited = {"__builtins__": {}}
                exec(compile(tree, "sealed-prior-queries", "exec"), inherited)
                if identity_columns:
                    from services.catalogue_observation_query_dal import IDENTITY_BATCH_QUERIES

                    prior_identity = inherited["IDENTITY_BATCH_QUERIES"]
                    passed_cost_raw = (
                        installed.read("evidence/identity-query-first-cost.json")
                        if publisher
                        else (previous / "catalogue-cost-result.json").read_bytes()
                    )
                    passed_timing_raw = (
                        installed.read("evidence/identity-query-first-timings.json")
                        if publisher
                        else (previous / "catalogue-timings.json").read_bytes()
                    )
                    passed_cost = json.loads(passed_cost_raw)
                    assert (
                        passed_cost["native_rows_and_multiplicities_equal"]
                        and passed_cost["business_state_unchanged"]
                    )
                    prior_timings = json.loads(passed_timing_raw)["statements"]
                    for category in ("identity.default_constraints", "identity.dependencies"):
                        assert prior_identity[category] == IDENTITY_BATCH_QUERIES[category]
                        measured = [
                            r
                            for r in prior_timings
                            if r["statement_sha256"] == sha(prior_identity[category].encode())
                        ]
                        assert len(measured) == 1 and 0 < measured[0]["native_seconds"] <= 0.250
                    members["evidence/identity-query-first-cost.json"] = passed_cost_raw
                    members["evidence/identity-query-first-timings.json"] = passed_timing_raw
                assert all(
                    inherited["CATALOGUE_BATCH_QUERIES"][key] == value
                    for key, value in CATALOGUE_BATCH_QUERIES.items()
                )
                timing_raw = (
                    installed.read("evidence/prior-corrected-query-timings.json")
                    if column_plan
                    else (previous / "catalogue-timings.json").read_bytes()
                )
                prior_cost_raw = (
                    installed.read("evidence/prior-corrected-query-cost.json")
                    if column_plan
                    else (previous / "catalogue-cost-result.json").read_bytes()
                )
                if column_plan:
                    members["evidence/decomposed-column-first-cost.json"] = (
                        installed.read("evidence/decomposed-column-first-cost.json")
                        if authority_batches
                        else (previous / "catalogue-cost-result.json").read_bytes()
                    )
                    members["evidence/decomposed-column-first-plans.json"] = (
                        installed.read("evidence/decomposed-column-first-plans.json")
                        if authority_batches
                        else (previous / "catalogue-query-plans.json").read_bytes()
                    )
                    if authority_batches:
                        members["evidence/full-collector-first-cost.json"] = (
                            previous / "catalogue-cost-result.json"
                        ).read_bytes()
                        members["evidence/full-collector-first-timings.json"] = (
                            previous / "catalogue-timings.json"
                        ).read_bytes()
                prior_cost = json.loads(prior_cost_raw)
                assert (
                    prior_cost["native_rows_and_multiplicities_equal"]
                    and prior_cost["business_state_unchanged"]
                )
                timing_rows = json.loads(timing_raw)["statements"]
                accepted = {}
                for category, query in CATALOGUE_BATCH_QUERIES.items():
                    measured = [
                        r for r in timing_rows if r["statement_sha256"] == sha(query.encode())
                    ]
                    assert (
                        len(measured)
                        == {"metadata.indexes": 3, "identity.indexes": 2, "metadata.checks": 1}[
                            category
                        ]
                    )
                    assert all(0 < r["native_seconds"] <= 0.250 for r in measured)
                    accepted[category] = dict(
                        query_sha256=sha(query.encode()),
                        maximum_seconds=max(r["native_seconds"] for r in measured),
                    )
                members["evidence/prior-corrected-query-timings.json"] = timing_raw
                members["evidence/prior-corrected-query-cost.json"] = prior_cost_raw
                members["evidence/retained-query-acceptance.json"] = json.dumps(
                    accepted, indent=2
                ).encode()
            assert all(members[n] == installed.read(n) for n in manifest["install_sources"])
            before_raw = (
                installed.read("evidence/representative-before.json")
                if cost or batched or corrected or columns
                else (previous / "representative-before.json").read_bytes()
            )
        manifest["stage"] = (
            "representative-columns-correction"
            if columns
            else (
                "representative-query-correction"
                if corrected
                else (
                    "representative-batched-cost-read"
                    if batched
                    else "representative-cost-read" if cost else "representative-reader-resume"
                )
            )
        )
        if full_cost:
            manifest["stage"] = "representative-complete-cost-read"
        if identity_queries:
            manifest["stage"] = "representative-identity-correction"
            manifest["identity_columns_only"] = identity_columns
            plan_raw = (
                evidence / "packet-20261119175737420/boundary-20261120090516597.json"
            ).read_bytes()
            assert (
                sha(plan_raw) == "70ad98a7e84a1e2801d250b3371dfd5d39d9f6a15c74f2760e16571ce5d965b6"
            )
            plan = json.loads(plan_raw)
            assert plan["outcome"] == "observed" and plan["connections_closed"] == 1
            assert plan["sql_mutations"] == plan["catalogue_replays"] == 0
            assert plan["sequence"][0]["Generation"] == 238
            members["evidence/identity-query-plans.json"] = plan_raw
        if publisher:
            manifest["stage"] = "representative-publisher-overlap"
            contracts = {}
            for name in (
                "dbo.sp_Build_Prekvk_And_Honor_Rankings",
                "dbo.sp_Refresh_View_EXCEL_FOR_KVK_All",
                "dbo.usp_RecordKvkFinalReportCompletion",
                "dbo.usp_MaintenanceKvkDue",
                "dbo.usp_MaintenanceDue",
                "dbo.v_ReportGovernorNames",
            ):
                row = old_modules[name]
                relative = row.get("path")
                if name == "dbo.v_ReportGovernorNames":
                    relative = "sql_schema/dbo.v_ReportGovernorNames.View.sql"
                assert relative is not None
                raw_source = subprocess.check_output(
                    [
                        "git",
                        "-c",
                        "safe.directory=" + str(sql_root),
                        "-C",
                        str(sql_root),
                        "show",
                        BASE + ":" + relative,
                    ],
                    timeout=15,
                )
                work_source = (sql_root / relative).read_bytes()
                assert work_source.replace(b"\r\n", b"\n") == raw_source.replace(
                    b"\r\n", b"\n"
                ), name
                # Existing source pins include both Windows checkout and Git
                # transport bytes. Admit only the actual pinned byte form.
                if "source_sha256" in row:
                    if sha(work_source) == row["source_sha256"]:
                        raw_source = work_source
                    assert sha(raw_source) == row["source_sha256"], name
                else:
                    assert name == "dbo.v_ReportGovernorNames"  # Git BASE pins this source.
                contracts[name] = dict(
                    definition_hashes=[
                        row["definition_sha256"],
                        *row.get("compatible_definition_sha256", []),
                    ],
                    execute_as=row["execute_as"],
                    source_sha256=sha(raw_source),
                )
                members["source/publisher/" + Path(relative).name + ".raw"] = raw_source
            members["source/publisher-contracts.json"] = json.dumps(contracts, indent=2).encode()
        manifest["snapshot"] = prior_manifest["snapshot"]
        manifest["reuse"] = dict(
            receipt_sha256=sha(receipt_raw),
            generation=(
                prior_manifest["reuse"]["generation"]
                if cost or batched or corrected or columns
                else receipt["checks"][1]["facts"]["generation"]
            ),
            sequence_identity=(
                prior_manifest["reuse"]["sequence_identity"]
                if cost or batched or corrected or columns
                else receipt["checks"][1]["facts"]["sequence_identity"]
            ),
        )
        if batched or corrected or columns:
            manifest["reuse"]["observed_fingerprint"] = prior_manifest["reuse"][
                "observed_fingerprint"
            ]
            observed = (
                evidence / "packet-20261119210128575/representative-observation.json"
            ).read_bytes()
            assert (
                sha(observed) == "9f7620d32208a62158ae6d4277d948d1cae95883e369897bed94d571fe35f923"
            )
            members["evidence/native-observation.json"] = observed
            for proof_name in (
                "collector-extraction-equivalence.json",
                (
                    "decomposed-collector-equivalence.json"
                    if columns
                    else (
                        "scope-first-collector-equivalence.json"
                        if corrected
                        else "batched-collector-equivalence.json"
                    )
                ),
            ):
                proof_raw = (evidence / proof_name).read_bytes()
                proof = json.loads(proof_raw)
                assert proof["passed"] and proof["source_sha256"] == sha(
                    members["bot/services/export_execution_dal.py"]
                )
                if proof_name.startswith(("batched", "scope-first", "decomposed")):
                    assert proof["batching_sha256"] == sha(
                        members["bot/services/catalogue_observation_batches.py"]
                    )
                    assert proof["source_native_sha256"] == sha(observed)
                    if corrected or columns:
                        assert proof["query_source_sha256"] == sha(
                            members["bot/services/catalogue_observation_query_dal.py"]
                        )
                    if identity_queries:
                        assert proof["identity_changed_query_categories"] == [
                            "identity.columns",
                            "identity.default_constraints",
                            "identity.dependencies",
                        ]
                    if columns:
                        assert proof["column_source_sha256"] == sha(
                            members["bot/services/catalogue_observation_columns_dal.py"]
                        )
                members["evidence/" + proof_name] = proof_raw
            if corrected or columns:
                plans = (
                    evidence / "packet-20261119175737420/boundary-20261119213700539.json"
                ).read_bytes()
                assert (
                    sha(plans) == "59b1a163a10665f75b8aead40c6745c7f348bd0db5cefc5befcd904b2249d7b0"
                )
                members["evidence/retained-query-plans.json"] = plans
        elif cost:
            manifest["reuse"]["observed_fingerprint"] = receipt["checks"][1]["facts"][
                "observed_fingerprint"
            ]
        members["evidence/installed-representative-receipt.json"] = receipt_raw
        members["evidence/representative-before.json"] = before_raw
        # No snapshot or installation batch is dispatched by the resume stage.
        members.pop("sql/preserve-d5e.sql")
        manifest["files"] = {name: sha(raw) for name, raw in sorted(members.items())}
    # Materialize every SQL batch, including generated grants/snapshot identifiers,
    # for ScriptDom before sealing. Python literal SQL is added by the validator.
    return seal_packet(evidence, members, manifest, stamp)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sql-root", required=True)
    parser.add_argument("--resume-from")
    parser.add_argument("--combined-proof")
    args = parser.parse_args()
    print(json.dumps(build(args.sql_root, args.resume_from, args.combined_proof), indent=2))
