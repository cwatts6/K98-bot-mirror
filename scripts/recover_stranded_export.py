"""Protected, isolated entry point for an explicitly reviewed recovery packet.

The PowerShell launcher authenticates the installed manifest and stages the
recovery tool files outside the application source. No live source is edited.
"""

import argparse
from contextlib import ExitStack
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import runpy
import sys


class RecoveryJournal:
    names = frozenset({"review", "intent", "termination", "closure", "failure-intent", "verified"})

    def __init__(self, root, inspect):
        self.root, self.inspect = Path(root), inspect
        self.inspect(self.root, private=True, allow_current_identity=False)

    def _path(self, name):
        if name not in self.names:
            raise ValueError("Fixed recovery journal member required.")
        self.inspect(self.root, private=True, allow_current_identity=False)
        return self.root / (name + ".json")

    def read(self, name):
        path = self._path(name)
        if not path.exists():
            return None
        self.inspect(path, private=True, allow_current_identity=False)
        if path.stat().st_nlink != 1 or path.stat().st_size > 4 * 1024 * 1024:
            raise ValueError("Bounded private recovery journal required.")
        return json.loads(path.read_bytes())

    def write(self, name, value):
        from services.export_execution_protocol import encode

        existing = self.read(name)
        if existing is not None:
            if existing != value:
                raise ValueError("Recovery journal conflict; preserve prior evidence.")
            return
        raw = encode(value)
        if len(raw) > 4 * 1024 * 1024:
            raise ValueError("Recovery journal exceeds its bound.")
        with self._path(name).open("xb") as output:
            output.write(raw)
            output.flush()
            os.fsync(output.fileno())
        if self.read(name) != value:
            raise ValueError("Recovery journal readback differs.")


def load_tool(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_previous_journal(path, inspect):
    if path is not None:
        inspect(path, private=True, allow_current_identity=False)
        if (path / "intent.json").exists():
            raise ValueError("Previous recovery started; preserve its journal for review.")


def previous_journal_paths(target):
    from uuid import UUID

    values = target.get("previous_packet_ids", [])
    if not isinstance(values, list):
        raise ValueError("Previous packet identities must be a list.")
    if target.get("previous_packet_id"):
        values = [*values, target["previous_packet_id"]]
    if (
        len(values) > 8
        or any(not isinstance(v, str) or str(UUID(v)) != v for v in values)
        or len(set(values)) != len(values)
    ):
        raise ValueError("Bounded distinct canonical previous packet identities required.")
    return [Path("C:/ProgramData/K98/S11/recovery") / value / "journal" for value in values]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--action", choices=("Inspect", "Apply"), required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--journal", required=True)
    parser.add_argument("--review-token")
    args = parser.parse_args(argv)
    if not sys.flags.isolated or not sys.dont_write_bytecode:
        raise ValueError("Isolated source-only Python (-I -B) required.")
    raw = Path(args.manifest).read_bytes()
    if len(raw) > 16 * 1024 * 1024 or hashlib.sha256(raw).hexdigest() != args.manifest_sha256:
        raise ValueError("Pinned installed manifest differs.")
    manifest = json.loads(raw)
    root = Path(manifest["child_script"]).parents[1]
    launcher = root / "scripts/run_export_authority.py"
    if (
        hashlib.sha256(launcher.read_bytes()).hexdigest()
        != manifest["source_hashes"]["scripts/run_export_authority.py"]
    ):
        raise ValueError("Pinned installed bootstrap differs.")
    installed = runpy.run_path(str(launcher))
    installed["protected_path"](launcher, allow_current_identity=False)
    manifest = installed["bootstrap"](args.manifest, script=str(launcher))
    from core.export_execution_host import (
        DeploymentBoundary,
        PrivateEvidenceStore,
        assert_protected_path,
    )
    from core.export_process_identity import open_pinned_process, pinned_process_alive
    from services.export_execution_dal import ExportExecutionDAL
    from services.export_runtime_composition import RuntimeRegistration
    from services.legacy_export_closeout import LegacyExportCloseout
    from services.legacy_export_closeout_dal import LegacyExportCloseoutDAL

    boundary = DeploymentBoundary(manifest)
    tool_root = Path(__file__).resolve().parent
    for path in (
        tool_root,
        tool_root / "stranded_export_host.py",
        tool_root / "stranded_export_custody.py",
        tool_root / "stranded_export_recovery.py",
        tool_root / "stranded_export_recovery_dal.py",
        Path(args.target),
    ):
        assert_protected_path(path, private=True, allow_current_identity=False)
    target = json.loads(Path(args.target).read_bytes())
    target["manifest_sha256"] = args.manifest_sha256
    previous_journals = previous_journal_paths(target)
    # No inherited SQL overrides: only the existing protected installation's
    # dedicated application configuration may supply connection credentials.
    for key in (
        "SQL_SERVER",
        "SQL_DATABASE",
        "S11_SQL_USERNAME",
        "S11_SQL_PASSWORD",
        "PYTHON_DOTENV_DISABLED",
    ):
        os.environ.pop(key, None)
    connect = installed["connection_factory"](manifest)
    registration = RuntimeRegistration(manifest["runtime_registration"])
    registered = registration.value()
    execution = ExportExecutionDAL(connect)
    store = PrivateEvidenceStore(manifest["evidence_root"], manifest["storage_owner"])
    closeout = LegacyExportCloseout(
        dal=LegacyExportCloseoutDAL(
            connect, account=registered["account"], storage_owner=registered["storage_owner"]
        ),
        execution=execution,
        store=store,
        registration=registration,
    )
    with ExitStack() as handles:
        retained = {}
        for role, binding in manifest["process_bindings"].items():
            retained[role] = open_pinned_process(binding["pid"], binding)
            handles.callback(retained[role].Close)

        def check_boundary():
            boundary.recheck()
            for previous_journal in previous_journals:
                check_previous_journal(previous_journal, assert_protected_path)
            if hashlib.sha256(Path(args.manifest).read_bytes()).hexdigest() != args.manifest_sha256:
                raise ValueError("Installed manifest changed during recovery.")
            if not all(
                pinned_process_alive(process, manifest["process_bindings"][role])
                for role, process in retained.items()
            ):
                raise ValueError("Original process pair exited; preserve recovery evidence.")

        host_module = load_tool(tool_root / "stranded_export_host.py", "_stranded_host")
        custody_module = load_tool(tool_root / "stranded_export_custody.py", "_stranded_custody")
        service_module = load_tool(
            tool_root / "stranded_export_recovery.py",
            "_stranded_recovery",
        )
        dal_module = load_tool(tool_root / "stranded_export_recovery_dal.py", "_stranded_dal")
        journal = RecoveryJournal(args.journal, assert_protected_path)
        service = service_module.StrandedExportRecovery(
            closeout=closeout,
            execution=execution,
            coordinator=dal_module.StrandedExportRecoveryDAL(closeout.dal),
            store=store,
            host=host_module.RecoveryHost(
                manifest["process_bindings"]["authority"],
                custody=custody_module,
                child_script=manifest["child_script"],
                manifest_path=args.manifest,
            ),
            journal=journal,
            check_boundary=check_boundary,
            expected=target,
        )
        if args.action == "Inspect":
            review = service.inspect()
            journal.write("review", review)
            result = dict(
                stage="RECOVERY_REVIEW_READY",
                review_token=service.token(review),
                job_id=target["job_id"],
                destination_count=target["destination_count"],
                production_changed=False,
                provider_requests=0,
            )
        else:
            review = journal.read("review")
            if review is None or args.review_token is None:
                raise ValueError("Inspect first and supply its exact review token.")
            result = service.apply(review, args.review_token)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(
            json.dumps(
                dict(
                    stage="RECOVERY_STOPPED",
                    error_type=type(error).__name__,
                    instruction="Preserve the journal and report this stop. Do not restart, clear claims, or replay work.",
                )
            )
        )
        raise SystemExit(1) from None
