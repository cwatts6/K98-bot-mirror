"""Held ordinary S11 process; manual administrative publication releases it.

Run each role explicitly with isolated Python. No SQL/provider/Bot work begins
while held. Every restart needs a fresh plan, pair and protected publication.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import time


def trusted_launch_plan(path):
    launcher = runpy.run_path(str(Path(__file__).with_name("run_export_authority.py")))

    def inspect(candidate, *, private=False):
        # The ordinary account may read the plan but must not own or modify it.
        launcher["protected_path"](candidate, allow_current_identity=False)
        return launcher["protected_path"](candidate, private=private)

    plan = launcher["bootstrap"](path, script=__file__, inspect_path=inspect)
    from core.export_process_pair import validate_plan

    validate_plan(plan)
    return plan, Path(path).read_bytes(), inspect


def load_templates(plan, inspect):
    from services.export_execution_protocol import MAX_MESSAGE_BYTES, decode

    result = {}
    for role, reference in plan["templates"].items():
        path = inspect(reference["path"], private=True)
        with path.open("rb") as source:
            raw = source.read(MAX_MESSAGE_BYTES + 1)
        if len(raw) > MAX_MESSAGE_BYTES or hashlib.sha256(raw).hexdigest() != reference["sha256"]:
            raise ValueError("Reviewed template bytes differ.")
        result[role] = decode(raw)
    return result


def wait_for_publication(plan, plan_raw, templates, role, own, expected_own, inspect):
    from core.export_process_identity import process_snapshot, verify_process_snapshot
    from core.export_process_pair import bind_templates, publication
    from services.export_execution_protocol import MAX_MESSAGE_BYTES, decode

    commit_path = Path(plan["commit_file"])
    inspect(commit_path.parent, private=True)
    while not commit_path.exists():
        verify_process_snapshot(process_snapshot(own), expected_own)
        time.sleep(1)
    inspect(commit_path, private=True)
    with commit_path.open("rb") as stream:
        commit = decode(stream.read(MAX_MESSAGE_BYTES + 1))
    manifests = {}
    for name, path in plan["manifests"].items():
        inspect(path, private=True)
        with Path(path).open("rb") as stream:
            manifests[name] = decode(stream.read(MAX_MESSAGE_BYTES + 1))
    bindings = manifests["authority"]["process_bindings"]
    expected = bind_templates(plan, templates, bindings)
    if manifests != expected or commit != publication(plan_raw, expected):
        raise ValueError("Incomplete or differing process-pair publication.")
    verify_process_snapshot(process_snapshot(own), bindings[role])
    return bindings


def main(argv=None):
    parser = argparse.ArgumentParser(description="Held S11 process; manual rebinding required")
    parser.add_argument("--plan", required=True)
    parser.add_argument("--role", required=True, choices=("bot", "authority"))
    parser.add_argument("--automatic-issuer")
    args = parser.parse_args(argv)
    plan, raw, inspect = trusted_launch_plan(args.plan)
    templates = load_templates(plan, inspect)
    import win32api

    from core.export_process_identity import open_pinned_process, process_snapshot
    from core.export_process_pair import verify_role

    descriptor = process_snapshot(win32api.GetCurrentProcess())
    verify_role(descriptor, args.role, plan)
    handle = open_pinned_process(os.getpid(), descriptor)
    print(
        json.dumps(
            {
                "stage": "HELD_FOR_MANUAL_REBINDING",
                "role": args.role,
                "descriptor": descriptor,
                "sql_connection_attempted": False,
            }
        ),
        flush=True,
    )
    try:
        if args.automatic_issuer:
            from core.export_automatic_pair import validate_issuer_record
            from core.export_execution_host import MessagePipe, open_message_pipe
            from core.export_process_identity import authenticate_process_peer

            issuer_path = Path(args.automatic_issuer)
            if (
                issuer_path.parent != Path(args.plan).parent
                or issuer_path.name != "AutomaticIssuer.json"
            ):
                raise ValueError("Issuer record must belong to this exact incarnation.")
            inspect(issuer_path, private=True)
            with issuer_path.open("rb") as source:
                record_raw = source.read(65537)
            if len(record_raw) > 65536:
                raise ValueError("Issuer record exceeds its bound.")
            record = json.loads(record_raw)
            issuer = validate_issuer_record(record, plan, raw)
            connection = open_message_pipe(r"\\.\pipe\K98Export-" + record["pipe_id"])
            peer = None
            try:
                peer = authenticate_process_peer(connection, issuer, server=True)
                channel = MessagePipe(connection)
                channel.send(dict(version=1, role=args.role, plan_sha256=record["plan_sha256"]))
                if channel.receive() != dict(version=1, accepted=True):
                    raise ValueError("Automatic issuer did not acknowledge this held role.")
            finally:
                if peer is not None:
                    peer.Close()
                connection.Close()
        bindings = wait_for_publication(
            plan, raw, templates, args.role, handle, descriptor, inspect
        )
        peer_role = "bot" if args.role == "authority" else "authority"
        peer = open_pinned_process(bindings[peer_role]["pid"], bindings[peer_role])
        try:
            if args.role == "authority":
                launcher = runpy.run_path(str(Path(__file__).with_name("run_export_authority.py")))
                return launcher["main"](["--manifest", plan["manifests"]["authority"]])
            import win32pipe

            from core.export_process_identity import pinned_process_alive

            pipe = r"\\.\pipe\K98Export-" + templates["authority"]["pipe_id"]
            while True:
                if not pinned_process_alive(peer, bindings["authority"]):
                    raise ValueError("Pinned authority exited before Bot admission.")
                try:
                    win32pipe.WaitNamedPipe(pipe, 1000)
                    break
                except Exception as exc:
                    if getattr(exc, "winerror", None) not in (2, 121):
                        raise
                    time.sleep(0.1)
            os.environ["K98_EXPORT_RUNTIME_MANIFEST"] = plan["manifests"]["bot"]
            os.environ["K98_EXPORT_MANUAL_REBINDING"] = "1"
            runpy.run_path(
                str(Path(__file__).absolute().parents[1] / "DL_bot.py"), run_name="__main__"
            )
            return 0
        finally:
            peer.Close()
    finally:
        handle.Close()


if __name__ == "__main__":
    raise SystemExit(main())
