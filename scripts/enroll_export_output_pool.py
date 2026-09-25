"""Explicit G4-only fresh-file enrollment. No startup, import or Bot IPC action."""

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
    from services.export_enrollment_service import EnrollmentPlan
    from services.export_execution_protocol import decode, encode
    from services.export_runtime_composition import enrollment_profile

    profile = enrollment_profile(manifest["enrollment_profile"])
    plan = EnrollmentPlan(decode(plan_bytes))
    value = plan.value()
    if (
        value["manifest_sha256"] != hashlib.sha256(manifest_bytes).hexdigest()
        or value["credential_profile_sha256"] != hashlib.sha256(encode(profile)).hexdigest()
        or value["owner_email"] != profile["owner_email"]
        or value["editor_email"] != manifest["service_account_email"]
        or value["project_id"] != manifest["project_id"]
        or value["storage_owner"] != manifest["storage_owner"]
    ):
        raise ValueError("Protected enrollment plan differs from the exact deployed profile.")
    return plan


def main(argv=None):
    parser = argparse.ArgumentParser(description="Explicit S11 G4 fresh private-file enrollment")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--actor", required=True)
    parser.add_argument("--reason", required=True)
    parser.add_argument(
        "--authorize-operation", choices=["S11_CREATE_PRIVATE_OUTPUT_POOL"], required=True
    )
    args = parser.parse_args(argv)
    bootstrap(args.manifest)
    from core.export_execution_host import (
        PrivateEvidenceStore,
        WindowsExecutionHost,
        assert_protected_path,
        current_sid,
    )
    from scripts.run_export_authority import connection_factory, manifest_contract
    from services.export_coordination_dal import ExportCoordinationDAL
    from services.export_enrollment_service import OutputEnrollment
    from services.export_execution_authority import ExportExecutionAuthority
    from services.export_execution_dal import ExportExecutionDAL
    from services.export_execution_protocol import decode
    from services.export_request_budget import RequestBudget
    from services.export_runtime_composition import verify_installation_contract

    raw = assert_protected_path(args.manifest, private=True).read_bytes()
    manifest = manifest_contract(
        decode(raw),
        script=__file__,
        current_sid=current_sid(),
        inspect_path=assert_protected_path,
        enrollment=True,
    )
    plan = approved_plan(manifest, raw, assert_protected_path(args.plan, private=True).read_bytes())
    connect = connection_factory(manifest)
    dal = ExportExecutionDAL(connect)
    verify_installation_contract(dal.installation_snapshot(), manifest["sql_contract"])
    session_id = str(uuid4())
    host = WindowsExecutionHost(
        python=manifest["python"],
        child_script=manifest["child_script"],
        manifest=args.manifest,
        authority_sid=manifest["authority_sid"],
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
        )
        OutputEnrollment(plan=plan, authority=authority, dal=dal, store=store).run(
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
