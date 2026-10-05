"""Administrative manual publication for two already held ordinary processes.

This creates fresh protected manifests and a final commit receipt. It never
starts a process, connects to SQL, enrolls a file or calls a provider.
Partial files are retained; an absent commit keeps both gates held.
"""

import argparse
import os
from pathlib import Path
import runpy


def publish_pair(plan, raw, templates, bindings, handles, inspect):
    import win32security

    from core.export_execution_host import DeploymentBoundary, assert_protected_path
    from core.export_process_identity import pinned_process_alive
    from core.export_process_pair import ROLES, bind_templates, publication
    from scripts.run_export_authority import manifest_contract
    from services.export_execution_protocol import encode

    manifests = bind_templates(plan, templates, bindings)
    manifest_contract(
        manifests["authority"],
        script=Path(__file__).with_name("run_export_authority.py"),
        current_sid=plan["application_sid"],
        inspect_path=assert_protected_path,
    )
    # Validates all seven independently reviewed records, including the actual
    # Bot token profile. Existing expected metadata and operator receipts are
    # retained; this step does not learn or refresh them from a SQL connection.
    DeploymentBoundary(manifests["authority"], observe_sid=lambda: plan["application_sid"])
    paths = [*plan["manifests"].values(), plan["commit_file"]]
    for path in paths:
        inspect(Path(path).parent, private=True)
        if Path(path).exists():
            raise ValueError("Publication destination already exists; retain it, do not overwrite.")

    def write_new(path, value):
        with Path(path).open("xb") as destination:
            destination.write(encode(value))
            destination.flush()
            os.fsync(destination.fileno())
        owner = win32security.ConvertStringSidToSid("S-1-5-32-544")
        win32security.SetNamedSecurityInfo(str(path), 1, 1, owner, None, None, None)
        inspect(path, private=True)

    for role in ROLES:
        if not pinned_process_alive(handles[role], bindings[role]):
            raise ValueError("Held process exited; no publication or replacement is admitted.")
        write_new(plan["manifests"][role], manifests[role])
    for role in ROLES:
        if not pinned_process_alive(handles[role], bindings[role]):
            raise ValueError("Held process exited during publication; retain partial files.")
    write_new(plan["commit_file"], publication(raw, manifests))
    return publication(raw, manifests)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Manual S11 process-pair rebinding")
    parser.add_argument("--plan", required=True)
    parser.add_argument("--authority-pid", required=True, type=int)
    parser.add_argument("--bot-pid", required=True, type=int)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--operator-hold-confirmed", action="store_true")
    args = parser.parse_args(argv)
    if args.apply and not args.operator_hold_confirmed:
        raise ValueError("Actual hold until completion or reconciliation required.")
    import ctypes

    if not ctypes.windll.shell32.IsUserAnAdmin():
        raise ValueError("Administrative publication required; application remains unelevated.")
    gate = runpy.run_path(str(Path(__file__).with_name("run_export_process_gate.py")))
    plan, raw, inspect = gate["trusted_launch_plan"](args.plan)
    templates = gate["load_templates"](plan, inspect)
    import win32api

    from core.export_process_identity import process_snapshot, validate_process_bindings
    from core.export_process_pair import verify_role

    handles, bindings = {}, {}
    try:
        for role in ("authority", "bot"):
            pid = getattr(args, role + "_pid")
            handle = win32api.OpenProcess(0x1000 | 0x100000, False, pid)
            handles[role] = handle
            bindings[role] = process_snapshot(handle)
            verify_role(bindings[role], role, plan)
        validate_process_bindings(bindings, plan["application_sid"])
        if args.apply:
            commit = publish_pair(plan, raw, templates, bindings, handles, inspect)
        else:
            commit = None
        import json

        print(
            json.dumps(
                {
                    "stage": (
                        "COMPLETED_MANUAL_PAIR_PUBLICATION"
                        if args.apply
                        else "READ_ONLY_PAIR_IDENTITY"
                    ),
                    "process_bindings": bindings,
                    "publication": commit,
                    "sql_connection_attempted": False,
                    "provider_called": False,
                }
            ),
            flush=True,
        )
        return 0
    finally:
        for handle in handles.values():
            handle.Close()


if __name__ == "__main__":
    raise SystemExit(main())
