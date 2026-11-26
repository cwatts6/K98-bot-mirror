"""Seal current local Bot/SQL candidate bytes for the isolated feasibility run."""

import argparse
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.verify_k98_update_pair import CONTRACT_ARCHIVE_MEMBERS


def build(sql_root, resume_from=None):
    stamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S%f")[:17]
    output = ROOT / ".codex_artifacts" / "p02-observer-proof-20261119" / ("packet-" + stamp)
    output.mkdir()
    sql_root = Path(sql_root).resolve()
    schema = sql_root / "sql_schema"
    modules = [
        "dbo.usp_P02BeginCatalogueMutation.StoredProcedure.sql",
        "dbo.usp_P02EndCatalogueMutation.StoredProcedure.sql",
        "dbo.usp_P02ReadObservationBoundary.StoredProcedure.sql",
        "dbo.tr_P02HeaderObservation.Trigger.sql",
        "dbo.tr_P02KvkWorkObservation.Trigger.sql",
        "dbo.tr_P02MaintenanceObservation.Trigger.sql",
        "tr_P02CatalogueObservation.DatabaseTrigger.sql",
    ]
    sources = [
        "dbo.KVKFinalReportHeader.Table.sql",
        "dbo.MaintenanceKvkWork.Table.sql",
        "dbo.MaintenanceWork.Table.sql",
        "dbo.MaintenanceConfigurationWork.Table.sql",
        "dbo.P02ObservationGeneration.Sequence.sql",
        *modules[:-1],
        "dbo.usp_MaintenanceKvkOutput.StoredProcedure.sql",
        "dbo.usp_RunMaintenance.StoredProcedure.sql",
        modules[-1],
    ]
    members = {"sql/" + name: (schema / name).read_bytes() for name in sources}
    names = set(CONTRACT_ARCHIVE_MEMBERS) | {
        "services/catalogue_observation_dal.py",
        "services/application_observation_admission.py",
        "event_calendar/sql_lifecycle.py",
        "core/recovery_sql_snapshot.py",
        "core/sql_observation.py",
    }
    for name in sorted(names):
        members["bot/" + name] = (ROOT / name).read_bytes()
    members["qualification/p02_observer/prove.py"] = (
        sql_root / "qualification/p02_observer/prove.py"
    ).read_bytes()
    for name in ("permissions.py", "integration.py", "reuse.py", "lifecycle_permissions.sql"):
        member = "qualification/p02_observer/" + name
        members[member] = (sql_root / member).read_bytes()
    evidence_root = ROOT / ".codex_artifacts/p02-observer-proof-20261119"
    inventory = json.loads((evidence_root / "observer-sql-inventory.json").read_text())
    grammar = json.loads(
        (evidence_root / "observer-sql-grammar-resume.json").read_text(encoding="utf-8-sig")
    )
    if grammar.get("passed") is not True or {
        (row["id"], row["sha256"]) for row in grammar["statements"]
    } != {(row["id"], row["sha256"]) for row in inventory["statements"]}:
        raise ValueError("Exact successful SQL grammar evidence required")
    for source, expected_hash in inventory["source_hashes"].items():
        raw = members[source] if source.startswith("sql/") else Path(source).read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected_hash:
            raise ValueError("SQL inventory source changed: " + source)
    for name in (
        "observer-sql-inventory.json",
        "observer-sql-grammar-resume.json",
        "observer-sql-collation.json",
        "collector-extraction-equivalence.json",
    ):
        members["evidence/" + name] = (evidence_root / name).read_bytes()
    manifest = {
        "version": 1,
        "database": "K98_P02Observer_" + stamp,
        "install_sources": ["sql/" + name for name in sources],
        "protocol_sources": ["sql/" + name for name in modules],
        "files": {name: hashlib.sha256(raw).hexdigest() for name, raw in sorted(members.items())},
    }
    if resume_from is not None:
        previous = Path(resume_from).resolve()
        raw_receipt = (previous / "receipt.json").read_bytes()
        receipt = json.loads(raw_receipt)
        integration = previous.name == "packet-20261119191942580"
        reader_installed = previous.name == "packet-20261119194043976"
        metadata_reuse = previous.name == "packet-20261119194526993"
        if receipt["database"] != "K98_P02Observer_20261119175737420" or receipt["outcome"] != (
            "core-protocol-cases-passed" if integration or metadata_reuse else "failed"
        ):
            raise ValueError("Only the diagnosed local fixture may be resumed")
        amend = previous.name == "packet-20261119184919948"
        installed_permissions = previous.name == "packet-20261119191215522"
        permissions = installed_permissions or previous.name == "packet-20261119185737622"
        if metadata_reuse:
            if (
                receipt["connections_closed"] != 2
                or len(receipt["checks"]) != 3
                or not all(row["passed"] for row in receipt["checks"])
                or receipt["checks"][-1]["name"]
                != "fresh-denial-health-refuses-drift-and-recovers-after-restoration"
                or receipt["checks"][-1]["facts"]["restored_and_read"] != 84
            ):
                raise ValueError("The retained collector/health acceptance differs")
        elif reader_installed:
            if (
                receipt["connections_closed"] != 2
                or len(receipt["checks"]) != 2
                or receipt["checks"][0]["passed"] is not True
                or receipt["checks"][0]["facts"]["generation"] != 82
                or receipt["checks"][1]["passed"] is not False
                or receipt["checks"][1]["name"]
                != "actual-actor-complete-collector-checkpoints-and-lifecycle"
                or "sql_expression_dependencies" not in receipt["first_failure"]["detail"]
                or "(229)" not in receipt["first_failure"]["detail"]
            ):
                raise ValueError("The retained metadata permission failure differs")
            grants = json.loads((ROOT / "deploy/s11_application_grants.json").read_text())["grants"]
            matching = [g for g in grants if g["object"].startswith("sys.")]
            if (
                len(matching) != 1
                or matching[0]["object"] != "sys.sql_expression_dependencies"
                or matching[0]["permission"] != "SELECT"
                or "column" in matching[0]
            ):
                raise ValueError("Exact existing metadata permission required")
        elif integration:
            if (
                receipt["connections_closed"] != 3
                or len(receipt["checks"]) != 6
                or not all(row["passed"] for row in receipt["checks"])
                or receipt["checks"][-1]["name"]
                != "drop-select-into-commit-and-rollback-observation"
                or receipt["checks"][-1]["facts"]["transactions"][-1]["generation"][-1] != 80
            ):
                raise ValueError("The retained permission/replacement acceptance differs")
        elif installed_permissions:
            if (
                receipt["connections_closed"] != 3
                or len(receipt["checks"]) != 3
                or not all(row["passed"] for row in receipt["checks"][:2])
                or receipt["checks"][-1]["passed"] is not False
                or receipt["checks"][-1]["name"]
                != "actual-restricted-lab-principal-and-observer-read"
                or receipt["first_failure"]["type"] != "AssertionError"
            ):
                raise ValueError("The retained permission-query failure differs")
            diagnosis_path = (
                evidence_root / "packet-20261119175737420/boundary-20261119191618942.json"
            )
            diagnosis = json.loads(diagnosis_path.read_bytes())
            if (
                diagnosis["outcome"] != "observed"
                or diagnosis["cleanup"] != "closed"
                or diagnosis["impersonation_reverted"] is not True
                or [row["value"] for row in diagnosis["actual_actor"]]
                != [
                    "P02ObserverApplication",
                    "S11_ExportApplication_P02Qual",
                    13,
                    0,
                    0,
                    None,
                    0,
                    0,
                    0,
                    1,
                ]
            ):
                raise ValueError("Read-only permission diagnosis differs")
            members["evidence/permission-query-diagnosis.json"] = diagnosis_path.read_bytes()
        elif permissions:
            if (
                receipt["connections_closed"] != 4
                or len(receipt["checks"]) != 8
                or not all(row["passed"] for row in receipt["checks"][:7])
                or receipt["checks"][-1]["passed"] is not False
                or receipt["checks"][-1]["name"] != "direct-lifecycle-truncate-coverage"
                or receipt["first_failure"]["detail"]
                != "TRUNCATE bypasses invalidation; enforced entry/permission coverage required"
            ):
                raise ValueError("The retained lifecycle bypass failure differs")
        elif amend:
            if (
                receipt["connections_closed"] != 4
                or len(receipt["checks"]) != 5
                or not all(row["passed"] for row in receipt["checks"][:4])
                or receipt["checks"][-1]["passed"] is not False
                or receipt["checks"][-1]["name"]
                != "mixed-candidate-discarded-and-full-current-metadata-read"
                or "3918" not in receipt["first_failure"]["detail"]
            ):
                raise ValueError("The retained trigger-enrollment failure differs")
        elif (
            receipt["connections_closed"] != 5
            or len(receipt["checks"]) != 1
            or receipt["checks"][0]["name"] != "isolated-source-installation"
            or receipt["checks"][0]["passed"] is not True
            or receipt["first_failure"]["type"] != "ObservationContractError"
        ):
            raise ValueError("The retained initial boundary failure differs")
        changes = []
        permitted = {"sql/" + name for name in modules if "Trigger.sql" in name}
        if integration:
            permitted = {"sql/dbo.usp_P02ReadObservationBoundary.StoredProcedure.sql"}
        with zipfile.ZipFile(previous / "packet.zip") as archive:
            if installed_permissions:
                permission_path = "qualification/p02_observer/lifecycle_permissions.sql"
                if archive.read(permission_path) != members[permission_path]:
                    raise ValueError("Installed permission fragment changed")
            for name in manifest["install_sources"]:
                if archive.read(name) != members[name]:
                    if not (amend or integration) or name not in permitted:
                        raise ValueError("Unexpected installed SQL change: " + name)
                    changes.append(name)
                if name in manifest["protocol_sources"]:
                    members["before/" + name] = archive.read(name)
        if (amend or integration) and set(changes) != permitted:
            raise ValueError("Exact reviewed module amendments required")
        manifest["database"] = receipt["database"]
        manifest["reuse"] = {
            "receipt_sha256": hashlib.sha256(raw_receipt).hexdigest(),
            "database_id": 13,
            "sequence_object_id": 1557580587,
            "generation": (
                84
                if metadata_reuse
                else (
                    82
                    if reader_installed
                    else (
                        80
                        if integration or reader_installed
                        else (
                            60
                            if installed_permissions
                            else (None if permissions else (5 if amend else 1))
                        )
                    )
                )
            ),
            "permissions_installed": installed_permissions
            or integration
            or reader_installed
            or metadata_reuse,
            "reader_installed": reader_installed or metadata_reuse,
            "metadata_grant": (
                {"object": "sys.sql_expression_dependencies", "permission": "SELECT"}
                if reader_installed
                else None
            ),
            "stage": (
                "metadata-reuse"
                if metadata_reuse
                else (
                    "collector-integration"
                    if integration or reader_installed
                    else (
                        "lifecycle-permissions"
                        if permissions
                        else ("trigger-enrollment" if amend else "initial-boundary")
                    )
                )
            ),
            "amendments": changes,
            "previous_protocol_sources": [
                "before/" + name for name in manifest["protocol_sources"]
            ],
        }
        manifest["files"] = {
            name: hashlib.sha256(raw).hexdigest() for name, raw in sorted(members.items())
        }
    members["manifest.json"] = json.dumps(manifest, indent=2).encode()
    archive_path = output / "packet.zip"
    with zipfile.ZipFile(archive_path, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, raw in sorted(members.items()):
            archive.writestr(name, raw)
    metadata = {
        "archive": str(archive_path),
        "sha256": hashlib.sha256(archive_path.read_bytes()).hexdigest(),
        "guest_directory": "Q:\\P02Observer\\" + stamp,
        "database": manifest["database"],
    }
    (output / "seal.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sql-root", required=True)
    parser.add_argument("--resume-from")
    arguments = parser.parse_args()
    build(arguments.sql_root, arguments.resume_from)
