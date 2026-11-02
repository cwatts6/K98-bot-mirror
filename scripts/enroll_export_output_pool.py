"""Explicit G4-only manual-file registration. No startup, import or Bot IPC action."""

import argparse
import hashlib
from pathlib import Path
import socket
from uuid import uuid4


def bootstrap(manifest_path):
    import runpy

    launcher = Path(__file__).absolute().with_name("run_export_authority.py")
    runpy.run_path(str(launcher))["bootstrap"](manifest_path, script=__file__)


def approved_plan(manifest, manifest_bytes, plan_bytes):
    from services.export_execution_protocol import decode, encode
    from services.export_manual_enrollment import ManualEnrollmentPlan, manual_profile

    profile = manual_profile(manifest)
    plan = ManualEnrollmentPlan(decode(plan_bytes))
    value = plan.value()
    if (
        value["manifest_sha256"] != hashlib.sha256(manifest_bytes).hexdigest()
        or value["credential_profile_sha256"] != hashlib.sha256(encode(profile)).hexdigest()
        or value["editor_email"] != manifest["service_account_email"]
        or value["project_id"] != manifest["project_id"]
        or value["storage_owner"] != manifest["storage_owner"]
    ):
        raise ValueError("Protected enrollment plan differs from the exact deployed profile.")
    from services.export_runtime_composition import RuntimeRegistration

    registered = RuntimeRegistration(manifest["runtime_registration"]).value()
    targets = [f["file_id"] for f in value["files"]]
    pools = [p for p in registered["pools"] if targets == [p["index_file_id"], *p["slot_file_ids"]]]
    excluded = set(registered["protected_file_ids"])
    for pool in registered["pools"]:
        if pool not in pools:
            excluded.update([pool["index_file_id"], *pool["slot_file_ids"]])
    if (
        len(pools) != 1
        or value["owner_email"] != pools[0]["owner_email"]
        or value["account"] != registered["account"]
        or value["protected_file_ids"] != sorted(excluded)
    ):
        raise ValueError("Manual plan differs from registered pool/owner/protected exclusions.")
    return plan


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Explicit S11 G4 registration of manually created files with an exact access policy"
    )
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--actor", required=True)
    parser.add_argument("--reason", required=True)
    parser.add_argument(
        "--authorize-operation", choices=["S11_REGISTER_MANUAL_OUTPUT_POOL"], required=True
    )
    args = parser.parse_args(argv)
    bootstrap(args.manifest)
    from core.export_execution_host import (
        DeploymentBoundary,
        PrivateEvidenceStore,
        WindowsExecutionHost,
        assert_protected_path,
        current_sid,
    )
    from core.export_process_identity import TRUST_MODEL
    from scripts.run_export_authority import connection_factory, manifest_contract
    from services.export_coordination_dal import ExportCoordinationDAL
    from services.export_execution_authority import ExportExecutionAuthority
    from services.export_execution_dal import ExportExecutionDAL, installation_migrations
    from services.export_execution_protocol import decode
    from services.export_manual_enrollment import ManualOutputEnrollment
    from services.export_request_budget import RequestBudget
    from services.export_runtime_composition import verify_installation_contract

    raw = assert_protected_path(args.manifest, private=True).read_bytes()
    manifest = manifest_contract(
        decode(raw),
        script=__file__,
        current_sid=current_sid(),
        inspect_path=assert_protected_path,
        enrollment=False,
    )
    plan = approved_plan(manifest, raw, assert_protected_path(args.plan, private=True).read_bytes())
    boundary = DeploymentBoundary(manifest)
    boundary.recheck()
    connect = connection_factory(manifest)
    dal = ExportExecutionDAL(connect)
    verify_installation_contract(
        dal.installation_snapshot(migrations=installation_migrations(manifest["sql_contract"])),
        manifest["sql_contract"],
    )
    session_id = str(uuid4())
    host = WindowsExecutionHost(
        python=manifest["python"],
        child_script=manifest["child_script"],
        manifest=args.manifest,
        authority_sid=manifest["authority_sid"],
        **(
            {
                "native_python": manifest["process_bindings"]["authority"]["executable"],
                "native_python_sha256": manifest["process_bindings"]["authority"]["sha256"],
            }
            if manifest.get("trust_model") == TRUST_MODEL
            else {}
        ),
    )
    store = PrivateEvidenceStore(manifest["evidence_root"], manifest["storage_owner"])
    session = dal.transition(
        "session",
        SessionID=session_id,
        Action="open",
        ExpectedVersion=0,
        HostIdentity=socket.gethostname(),
        BootID=str(uuid4()),
        ExecutableHash=hashlib.sha256(Path(manifest["python"]).read_bytes()).digest(),
        ManifestHash=hashlib.sha256(raw).digest(),
    )
    authority = None
    try:
        budget_dal = ExportCoordinationDAL(
            connect, preparations=True, output_operations=True, execution_evidence=True
        )
        authority = ExportExecutionAuthority(
            dal=dal,
            store=store,
            host=host,
            session_id=session_id,
            budget_factory=lambda account: RequestBudget(budget_dal, account),
            enrollment_plan=plan,
            dispatch_guard=boundary.recheck,
        )
        ManualOutputEnrollment(plan=plan, authority=authority, dal=dal, store=store).run(
            actor=args.actor, reason=args.reason
        )
    finally:
        # Construction opens no streams; once constructed, require a proven drain.
        drained = authority is None or authority.drain()
        if drained:
            dal.transition(
                "session", SessionID=session_id, Action="close", ExpectedVersion=session["Version"]
            )
    return 0 if drained else 1


if __name__ == "__main__":
    raise SystemExit(main())
