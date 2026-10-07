"""Administrative startup issuer; all application work remains unelevated.

The existing SQL readiness wrapper launches this entry point. A protected seed
policy authorizes normal restart, never replay of failed/uncertain jobs. Fresh
gate identities are authenticated as descendants of issuer-created jobs.
"""

import argparse
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import time
from typing import Any
from uuid import uuid4


def administrative_inspector(launcher):
    """Administrative controls may be read, never owned/written, by the app SID."""

    def inspect(path, *, private=False):
        launcher["protected_path"](path, allow_current_identity=False)
        return launcher["protected_path"](path, private=private)

    return inspect


def load_seed(policy, inspect):
    from services.export_execution_protocol import decode

    gate = runpy.run_path(str(Path(__file__).with_name("run_export_process_gate.py")))
    reference = policy["seed_plan"]
    if set(reference) != {"path", "sha256"}:
        raise ValueError("Pinned seed plan required.")
    path = inspect(reference["path"], private=True)
    if hashlib.sha256(path.read_bytes()).hexdigest() != reference["sha256"]:
        raise ValueError("Reviewed seed plan differs.")
    plan, _, _ = gate["trusted_launch_plan"](str(path))
    if plan["source_hashes"] != policy["source_hashes"]:
        raise ValueError("Seed and startup source expectations differ.")
    templates = gate["load_templates"](plan, inspect)
    records = {}
    for kind, ref in templates["authority"]["deployment_boundary"]["review"]["records"].items():
        record_path = inspect(ref["path"], private=True)
        raw = record_path.read_bytes()
        if len(raw) > 16 * 1024 * 1024 or hashlib.sha256(raw).hexdigest() != ref["sha256"]:
            raise ValueError("Reviewed observation differs.")
        records[kind] = decode(raw)
    return plan, templates, records


def read_previous(directory, policy_hash, inspect, application_sid):
    candidates = []
    for path in Path(directory).glob("incarnation-*.json"):
        candidates.append(path)
        if len(candidates) > 1000:
            raise ValueError("Startup history bound exceeded; retain history.")
    if not candidates:
        return None
    path = sorted(candidates, key=lambda value: value.name)[-1]
    inspect(path, private=True)
    raw = path.read_bytes()
    if len(raw) > 65536:
        raise ValueError("Startup state exceeds its bound.")
    value = json.loads(raw)
    if (
        set(value) != {"version", "sequence", "policy_sha256", "bindings", "publication"}
        or value["version"] != 1
        or type(value["sequence"]) is not int
        or not 0 < value["sequence"] <= 1000
        or value["policy_sha256"] != policy_hash
    ):
        raise ValueError("Previous startup state belongs to another policy; reconcile.")
    from core.export_process_identity import validate_process_bindings

    validate_process_bindings(value["bindings"], application_sid)
    commit = value["publication"]
    if (
        not isinstance(commit, dict)
        or set(commit) != {"version", "plan_sha256", "manifests"}
        or type(commit["version"]) is not int
        or commit["version"] != 1
        or not isinstance(commit["manifests"], dict)
        or set(commit["manifests"]) != {"authority", "bot"}
        or not all(
            isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest)
            for digest in [commit["plan_sha256"], *commit["manifests"].values()]
        )
    ):
        raise ValueError("Exact prior process-pair publication required; reconcile.")
    if not path.name.startswith("incarnation-" + str(value["sequence"]).zfill(20) + "-"):
        raise ValueError("Startup sequence differs from its immutable record.")
    return value


def acknowledge_role(pipe, created, role, plan, raw):
    import ctypes
    from ctypes import wintypes

    import win32api

    from core.export_execution_host import MessagePipe
    from core.export_process_identity import process_snapshot
    from core.export_process_pair import verify_role
    from core.export_startup_windows import role_member

    channel = MessagePipe(pipe, timeout_ms=30000, process=created.process)
    channel.connect()
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    get_pid = kernel.GetNamedPipeClientProcessId
    get_pid.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.ULONG)]
    get_pid.restype = wintypes.BOOL
    pid = wintypes.ULONG()
    if not get_pid(int(pipe), ctypes.byref(pid)):
        raise ValueError("Held-role pipe identity unavailable.")
    handle = win32api.OpenProcess(0x1000 | 0x100000, False, pid.value)
    try:
        if not role_member(handle, created):
            raise ValueError("Held role is not an issuer-created descendant.")
        descriptor = process_snapshot(handle)
        verify_role(descriptor, role, plan)
        expected = dict(version=1, role=role, plan_sha256=hashlib.sha256(raw).hexdigest())
        if channel.receive() != expected:
            raise ValueError("Held-role acknowledgment differs from this incarnation.")
        channel.send(dict(version=1, accepted=True))
        return descriptor, handle
    except BaseException:
        handle.Close()
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description="Protected S11 automatic startup issuer")
    parser.add_argument("--policy", default=r"C:\ProgramData\K98\S11\AutomaticStartupPolicy.json")
    args = parser.parse_args(argv)
    launcher = runpy.run_path(str(Path(__file__).with_name("run_export_authority.py")))
    inspect = administrative_inspector(launcher)
    launcher["bootstrap"](args.policy, script=__file__, inspect_path=inspect)
    import win32api
    import win32event
    import win32process

    from core.export_automatic_pair import incarnation_files, verify_automatic_token
    from core.export_execution_host import (
        create_private_pipe,
        machine_identity,
    )
    from core.export_process_identity import process_snapshot
    from core.export_process_pair import bind_templates, publication
    from core.export_startup_windows import (
        TerminatedPair,
        create_private_directory,
        create_role,
        linked_application_token,
        release_created_role,
        signalled,
        startup_mutex,
        stop_unadmitted_role,
        write_new_protected,
    )
    from scripts.provision_export_process_pair import publish_pair
    from services.export_execution_dal import ExportExecutionDAL, installation_migrations
    from services.export_execution_protocol import encode
    from services.export_runtime_composition import verify_installation_contract
    from services.export_startup_reconciliation import StartupReconciler

    policy_path = inspect(args.policy, private=True)
    policy_raw = policy_path.read_bytes()
    policy = json.loads(policy_raw)
    if (
        set(policy) != {"version", "source_hashes", "seed_plan", "state_directory", "flags"}
        or type(policy["version"]) is not int
        or policy["version"] != 1
    ):
        raise ValueError("Exact administrator startup policy required.")
    flag_names = {
        "EXPORT_COORDINATION_ENABLED",
        "KVK_SOURCE_INTAKE_ENABLED",
        "KVK_SOURCE_RECOVERY_ENABLED",
    }
    if (
        set(policy["flags"]) != flag_names
        or any(type(v) is not bool for v in policy["flags"].values())
        or policy["flags"]["EXPORT_COORDINATION_ENABLED"] is not True
    ):
        raise ValueError("Explicit coordinated startup flags required.")
    plan, templates, records = load_seed(policy, inspect)
    authority = templates["authority"]
    sid = plan["application_sid"]
    boundary = authority["deployment_boundary"]
    host = machine_identity()
    if host != boundary["host"]:
        raise ValueError("Startup policy belongs to another Windows host.")
    token, profile = linked_application_token(sid)
    mutex = None
    try:
        for expected in plan["token_profiles"].values():
            verify_automatic_token(profile, expected, sid)
        mutex = startup_mutex(host["machine_guid"], sid)
        inspect(policy["state_directory"], private=True)
        policy_hash = hashlib.sha256(policy_raw).hexdigest()
        previous: dict[str, Any] | None = read_previous(
            policy["state_directory"], policy_hash, inspect, sid
        )
        connect = launcher["connection_factory"](authority)
        verify_installation_contract(
            ExportExecutionDAL(connect).installation_snapshot(
                migrations=installation_migrations(authority["sql_contract"])
            ),
            authority["sql_contract"],
        )
        reconciler = StartupReconciler(connect, authority["runtime_registration"], host)
        termination = TerminatedPair(previous["bindings"]) if previous else None
        sequence = previous["sequence"] if previous else 0
        recent_crashes = []
        while True:
            reconciler.prepare(
                previous_hash=(
                    previous["publication"]["manifests"]["authority"] if previous else None
                ),
                termination=termination,
            )
            sequence += 1
            if sequence > 1000:
                raise ValueError("Startup history bound reached; retain history.")
            nonce = str(uuid4())
            directory = Path(plan["commit_file"]).parent.parent / nonce
            payload, new_plan, new_templates = incarnation_files(
                plan,
                templates,
                records,
                profile=profile,
                directory=str(directory),
                nonce=nonce,
                observed_utc=datetime.now(UTC).isoformat(),
            )
            create_private_directory(directory, sid)
            for name, raw in payload.items():
                write_new_protected(directory / name, raw, sid)
            new_raw = payload["ManualProcessPairPlan-CANDIDATE.json"]
            issuer_record: dict[str, Any] = dict(
                version=1,
                issuer=process_snapshot(win32api.GetCurrentProcess()),
                pipe_id=str(uuid4()),
                plan_sha256=hashlib.sha256(new_raw).hexdigest(),
            )
            issuer_path = directory / "AutomaticIssuer.json"
            write_new_protected(issuer_path, encode(issuer_record), sid)
            environment = dict(os.environ)
            for key in ("K98_EXPORT_RUNTIME_MANIFEST", "K98_EXPORT_MANUAL_REBINDING"):
                environment.pop(key, None)
            environment.update({k: "1" if v else "0" for k, v in policy["flags"].items()})
            environment.update(
                K98_EXPORT_LAUNCH_VALIDATION="0",
                K98_EXPORT_AUTOMATIC_ISSUER=str(issuer_path),
                K98_EXPORT_LAUNCH_PLAN=str(directory / "ManualProcessPairPlan-CANDIDATE.json"),
                WATCHDOG_CHILD_LOG=str(
                    Path(__file__).parents[1] / "logs" / ("s11-automatic-" + nonce + ".log")
                ),
            )
            created = {}
            handles = {}
            bindings = {}
            try:
                for role in ("authority", "bot"):
                    pipe = create_private_pipe(
                        r"\\.\pipe\K98Export-" + issuer_record["pipe_id"],
                        authority_sid=sid,
                        client_sid=sid,
                        overlapped=True,
                    )
                    try:
                        command = (
                            [
                                authority["python"],
                                "-I",
                                "-B",
                                str(Path(__file__).with_name("run_export_process_gate.py")),
                                "--plan",
                                str(directory / "ManualProcessPairPlan-CANDIDATE.json"),
                                "--role",
                                "authority",
                                "--automatic-issuer",
                                str(issuer_path),
                            ]
                            if role == "authority"
                            else [
                                authority["python"],
                                "-B",
                                str(Path(__file__).parents[1] / "run_bot.py"),
                            ]
                        )
                        created[role] = create_role(
                            token, command, environment, str(Path(__file__).parents[1]), sid
                        )
                        bindings[role], handles[role] = acknowledge_role(
                            pipe, created[role], role, new_plan, new_raw
                        )
                    finally:
                        pipe.Close()
                expected = publication(new_raw, bind_templates(new_plan, new_templates, bindings))
                previous = dict(
                    version=1,
                    sequence=sequence,
                    policy_sha256=policy_hash,
                    bindings=bindings,
                    publication=expected,
                )
                state_path = Path(policy["state_directory"]) / (
                    "incarnation-" + str(sequence).zfill(20) + "-" + nonce + ".json"
                )
                write_new_protected(state_path, encode(previous), sid)
                commit = publish_pair(
                    new_plan,
                    new_raw,
                    new_templates,
                    bindings,
                    handles,
                    inspect,
                    write_file=lambda path, raw: write_new_protected(path, raw, sid),
                )
                if commit != expected:
                    raise ValueError("Automatic publication differs.")
                print(
                    json.dumps(
                        dict(
                            stage="AUTOMATIC_PROCESS_PAIR_PUBLISHED",
                            incarnation=nonce,
                            publication=commit,
                            authority_pid=bindings["authority"]["pid"],
                            bot_pid=bindings["bot"]["pid"],
                            application_elevated=False,
                        )
                    ),
                    flush=True,
                )
                while not signalled(created["bot"].process):
                    time.sleep(0.5)
                exit_code = win32process.GetExitCodeProcess(created["bot"].process)
                while not signalled(handles["authority"]):
                    time.sleep(0.5)
                termination = TerminatedPair(bindings, handles)
                termination.verify()
                reconciler.prepare(
                    previous_hash=commit["manifests"]["authority"], termination=termination
                )
                for role in created:
                    release_created_role(created[role])
                if exit_code == 0:
                    print(
                        json.dumps(
                            dict(
                                stage="AUTOMATIC_PAIR_STOPPED",
                                bot_exit_code=exit_code,
                                restart=False,
                            )
                        ),
                        flush=True,
                    )
                    return 0
                if exit_code != 15:
                    now = time.monotonic()
                    recent_crashes = [value for value in recent_crashes if now - value < 60]
                    recent_crashes.append(now)
                    if len(recent_crashes) >= 5:
                        raise ValueError("Crash storm; retain history and require reconciliation.")
                    # Positive native exit and SQL drain precede this delay.
                    # It never retries a job or releases ownership by age.
                    time.sleep(5)
                print(
                    json.dumps(
                        dict(
                            stage="AUTOMATIC_RESTART_READY", restart=True, requested=exit_code == 15
                        )
                    ),
                    flush=True,
                )
            except BaseException as error:
                if not (directory / "commit.json").exists():
                    for item in created.values():
                        stop_unadmitted_role(item)
                print(
                    json.dumps(
                        dict(
                            stage="STOP_RECONCILIATION_REQUIRED",
                            error_type=type(error).__name__,
                            directory=str(directory),
                            retry=False,
                        )
                    ),
                    flush=True,
                )
                # Published work is never terminated/replayed by error recovery.
                # Retain all native job handles and require operator reconciliation.
                while True:
                    time.sleep(1)
            finally:
                # This executes only after clean shutdown/restart; error mode holds.
                for handle in handles.values():
                    handle.Close()
    finally:
        if mutex is not None:
            win32event.ReleaseMutex(mutex)
            mutex.Close()
        token.Close()


if __name__ == "__main__":
    raise SystemExit(main())
