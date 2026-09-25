"""Independent, operator-provisioned S11 export supervisor.

No service is installed and importing this file starts nothing. G4 supplies a
protected manifest, Windows service identity and SQL permissions. The bot's
normal process does not launch this entry point.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import sys
from uuid import uuid4


class AuthorityStartupError(RuntimeError):
    """No runtime readiness or provider request may follow this failure."""


def windows_sid():
    import win32api
    import win32security

    token = win32security.OpenProcessToken(win32api.GetCurrentProcess(), 8)
    try:
        sid, _ = win32security.GetTokenInformation(token, win32security.TokenUser)
        return win32security.ConvertSidToStringSid(sid)
    finally:
        token.Close()


def protected_path(path, *, private=False, allow_current_identity=True, identity=None):
    """Native-only bootstrap check, usable before the application is importable."""
    import win32file
    import win32security

    candidate = Path(path)
    if not candidate.is_absolute() or not candidate.exists():
        raise AuthorityStartupError("Provisioned absolute protected path required.")
    trusted = {"S-1-5-18", "S-1-5-32-544"}
    if allow_current_identity:
        trusted.add(identity if identity is not None else windows_sid())
    installer, _, _ = win32security.LookupAccountName(None, "NT SERVICE\\TrustedInstaller")
    trusted.add(win32security.ConvertSidToStringSid(installer))
    for index, item in enumerate((candidate, *candidate.parents)):
        if win32file.GetFileAttributes(str(item)) & 0x400:
            raise AuthorityStartupError("Reparse points are forbidden in authority paths.")
        security = win32security.GetNamedSecurityInfo(str(item), 1, 1 | 4)
        owner = win32security.ConvertSidToStringSid(security.GetSecurityDescriptorOwner())
        if owner not in trusted:
            raise AuthorityStartupError("Authority path has an untrusted owner.")
        dacl = security.GetSecurityDescriptorDacl()
        if dacl is None:
            raise AuthorityStartupError("Authority path has no protective DACL.")
        for ace_index in range(dacl.GetAceCount()):
            ace = dacl.GetAce(ace_index)
            kind, flags = ace[0]
            if flags & 8 or kind == 1:
                continue
            if kind != 0:
                raise AuthorityStartupError("Unsupported authority path ACL entry.")
            mask, sid = ace[1:]
            if win32security.ConvertSidToStringSid(sid) in trusted:
                continue
            dangerous = 0x10000000 | 0x40000000 | 0x40000 | 0x80000 | 0x10000 | 0x40
            if index == 0:
                dangerous |= 0x2 | 0x4 | 0x10 | 0x100
                if private:
                    dangerous |= 0x80000000 | 0x1
            if mask & dangerous:
                raise AuthorityStartupError("Untrusted authority path access.")
    return candidate


def bootstrap(manifest_path, *, script, inspect_path=None):
    """Check protected import directories and exact source before app imports.

    The three launcher .py files and isolated Python/pywin32 installation are
    administrator-verified G4 trust roots. Child/enrollment load this exact .py
    with runpy, never through a package search. No application module is used
    until this check returns. Deploy a source-only tree: cached bytecode and
    native application modules are not part of the reviewed source inventory.
    """
    if not sys.flags.isolated:
        raise AuthorityStartupError("Authority entry points require isolated Python (-I).")
    inspect_path = inspect_path or protected_path
    root = Path(script).absolute().parents[1]
    inspect_path(root)
    path = inspect_path(Path(manifest_path), private=True)
    with path.open("rb") as stream:
        raw = stream.read(16 * 1024 * 1024 + 1)
    if not 0 < len(raw) <= 16 * 1024 * 1024:
        raise AuthorityStartupError("Bounded protected manifest required.")
    manifest = json.loads(raw)
    hashes = manifest.get("source_hashes") if isinstance(manifest, dict) else None
    if not isinstance(hashes, dict) or not hashes or len(hashes) > 4096:
        raise AuthorityStartupError("Reviewed authority source inventory required.")
    sources = code_files(root, inspect_directory=inspect_path)
    if set(hashes) != sources:
        raise AuthorityStartupError("Reviewed authority source inventory differs.")
    for relative, digest in hashes.items():
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise AuthorityStartupError("Exact source digest required.")
        source = inspect_path(root / relative)
        if hashlib.sha256(source.read_bytes()).hexdigest() != digest:
            raise AuthorityStartupError("Provisioned source digest differs.")
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(root))
    return manifest


def code_files(root, *, inspect_directory=None):
    """Enumerate executable application source without walking data or local tooling."""
    ignored = {
        ".venv",
        ".git",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        "tests",
        "data",
        "downloads",
        "artifacts",
        "docs",
        "logs",
        "smoke_artifacts",
        "sql",
        "telemetry",
        "assets",
    }
    result = set()

    def unreadable(_error):
        raise AuthorityStartupError("Complete source inventory cannot be enumerated.")

    for directory, subdirectories, filenames in os.walk(
        root, followlinks=False, onerror=unreadable
    ):
        if inspect_directory is not None:
            inspect_directory(Path(directory))
            # os.walk lists directory links but does not yield them with
            # followlinks=False. Inspect before pruning, so an importable alias
            # cannot silently escape the protected source inventory.
            for name in subdirectories:
                if name not in ignored and not name.startswith("."):
                    inspect_directory(Path(directory) / name)
            cache = Path(directory) / "__pycache__"
            if cache.exists():
                inspect_directory(cache)
                if any(cache.iterdir()):
                    raise AuthorityStartupError(
                        "Application bytecode cache is not reviewed source."
                    )
            if any(
                Path(name).suffix.lower() in {".pyd", ".so", ".pyc", ".pyo", ".pyw"}
                for name in filenames
            ):
                raise AuthorityStartupError("Unreviewed executable import artifact.")
        subdirectories[:] = [
            name for name in subdirectories if name not in ignored and not name.startswith(".")
        ]
        for name in filenames:
            if name.lower().endswith(".py"):
                result.add((Path(directory) / name).relative_to(root).as_posix())
                if len(result) > 4096:
                    raise AuthorityStartupError("Authority source inventory exceeds bound.")
    return result


def manifest_contract(manifest, *, script, current_sid, inspect_path, enrollment=False):
    """Validate provisioned identities and protected source before any SQL open."""
    from services.export_execution_protocol import uuid_text

    expected = {
        "version",
        "authority_sid",
        "bot_sid",
        "pipe_id",
        "python",
        "child_script",
        "credentials_file",
        "evidence_root",
        "storage_owner",
        "sql_server",
        "sql_database",
        "sql_contract",
        "service_account_email",
        "project_id",
        "source_hashes",
        "runtime_registration",
        "deployment_boundary",
    }
    if enrollment:
        expected = expected - {"runtime_registration", "deployment_boundary"} | {
            "enrollment_profile"
        }
    if (
        not isinstance(manifest, dict)
        or set(manifest) != expected
        or type(manifest["version"]) is not int
        or manifest["version"] != (1 if enrollment else 2)
    ):
        raise AuthorityStartupError("Exact S11 authority manifest required.")
    if manifest["authority_sid"] != current_sid or manifest["bot_sid"] == current_sid:
        raise AuthorityStartupError("Separate provisioned authority and Bot identities required.")
    if not all(
        re.fullmatch(r"S-\d+(?:-\d+)+", manifest[key]) for key in ("authority_sid", "bot_sid")
    ):
        raise AuthorityStartupError("Canonical Windows identities required.")
    uuid_text(manifest["pipe_id"])
    if not re.fullmatch(r"[A-Za-z0-9_.\\,-]{1,128}", manifest["sql_server"]) or not re.fullmatch(
        r"[A-Za-z0-9_]{1,128}", manifest["sql_database"]
    ):
        raise AuthorityStartupError("Exact configured SQL target required.")
    if not re.fullmatch(
        r"[A-Za-z0-9_.@-]{3,254}", manifest["service_account_email"]
    ) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", manifest["project_id"]):
        raise AuthorityStartupError("Registered provider identity required.")
    if not re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", manifest["storage_owner"]):
        raise AuthorityStartupError("Explicit private evidence owner required.")
    from kvk.dal.new_source_import_dal import SourceConflict
    from services.export_runtime_composition import (
        RuntimeRegistration,
        validate_installation_contract,
    )

    try:
        validate_installation_contract(manifest["sql_contract"])
    except SourceConflict as exc:
        raise AuthorityStartupError(
            "Protected complete SQL installation contract required."
        ) from exc
    if (
        manifest["sql_contract"]["profile"] != "authority"
        or manifest["sql_contract"]["database"] != manifest["sql_database"]
    ):
        raise AuthorityStartupError("Authority SQL profile/database differs from its contract.")
    if enrollment:
        from services.export_runtime_composition import enrollment_profile

        enrollment_profile(manifest["enrollment_profile"])
    else:
        if not isinstance(manifest["deployment_boundary"], dict):
            raise AuthorityStartupError("Protected deployment boundary required.")
        try:
            registration = RuntimeRegistration(manifest["runtime_registration"])
        except (ValueError, SourceConflict) as exc:
            raise AuthorityStartupError(
                "Complete protected runtime registration required."
            ) from exc
        if registration.value()["service_account_email"] != manifest["service_account_email"]:
            raise AuthorityStartupError("Runtime registration differs from the provider identity.")
    root = Path(script).resolve().parents[1]
    required = {
        "scripts/run_export_authority.py",
        "scripts/run_export_provider_child.py",
        "core/export_execution_host.py",
        "services/export_execution_authority.py",
        "services/export_execution_dal.py",
        "services/export_execution_protocol.py",
        "services/export_request_budget.py",
        "services/export_coordination_dal.py",
    }
    hashes = manifest["source_hashes"]
    source_files = code_files(root)
    if (
        not isinstance(hashes, dict)
        or not required <= set(hashes)
        or set(hashes) != source_files
        or len(hashes) > 4096
    ):
        raise AuthorityStartupError("Reviewed authority source inventory required.")
    for relative, expected_hash in sorted(hashes.items()):
        if (
            not isinstance(relative, str)
            or not re.fullmatch(r"[A-Za-z0-9_./-]{1,256}", relative)
            or ".." in Path(relative).parts
            or not isinstance(expected_hash, str)
            or not re.fullmatch(r"[0-9a-f]{64}", expected_hash)
        ):
            raise AuthorityStartupError("Canonical immutable source identity required.")
        path = root / relative
        inspect_path(path)
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected_hash:
            raise AuthorityStartupError("Provisioned source digest differs.")
    for name in ("python", "child_script", "credentials_file"):
        inspect_path(manifest[name], private=name == "credentials_file")
    inspect_path(manifest["evidence_root"], private=True)
    if Path(manifest["child_script"]).resolve() != (root / "scripts/run_export_provider_child.py"):
        raise AuthorityStartupError("Child entry differs from the reviewed source tree.")
    return manifest


def connection_factory(manifest):
    """Windows integrated SQL identity; no caller-controlled connection options."""
    import pyodbc

    target = (
        "DRIVER={ODBC Driver 18 for SQL Server};SERVER="
        + manifest["sql_server"]
        + ";DATABASE="
        + manifest["sql_database"]
        + ";Trusted_Connection=yes;Encrypt=yes;TrustServerCertificate=no;"
    )

    def connect():
        return pyodbc.connect(target, autocommit=True, timeout=5)

    return connect


class AuthorityBroker:
    """Typed provider actions and fixed proof selectors; never caller-authored evidence."""

    def __init__(self, authority, registration, *, boundary=None):
        from services.export_runtime_composition import RuntimeRegistration

        if not isinstance(registration, RuntimeRegistration):
            raise ValueError("Immutable protected authority registration required.")
        self.authority = authority
        self.registration = registration
        self.boundary = boundary
        self.issuer = None

    def dispatch(self, message):
        from services.export_execution_protocol import ProviderRequest, uuid_text

        if self.boundary is not None:
            if (
                not isinstance(message, dict)
                or message.get("deployment_hash") != self.boundary.fingerprint
            ):
                raise ValueError("Action belongs to another deployment boundary.")
            message = {k: v for k, v in message.items() if k != "deployment_hash"}
        if (
            not isinstance(message, dict)
            or type(message.get("version")) is not int
            or message["version"] != 1
        ):
            raise ValueError("Versioned authority action required.")
        action = message.get("action")
        if action == "ready":
            if (
                set(message) != {"version", "action"}
                or self.boundary is None
                or self.issuer is None
            ):
                raise ValueError("Complete provisioned authority required.")
            return dict(
                deployment_hash=self.boundary.recheck(),
                registration_hash=self.registration.fingerprint,
            )
        if action == "prove":
            if (
                set(message)
                != {
                    "version",
                    "action",
                    "kind",
                    "object_id",
                    "snapshot_hash",
                    "current_attempt_id",
                    "old_attempt_id",
                }
                or self.issuer is None
                or not isinstance(message["snapshot_hash"], str)
                or not re.fullmatch(r"[0-9a-f]{64}", message["snapshot_hash"])
            ):
                raise ValueError("Exact fixed proof selector and trusted issuer required.")
            return self.issuer.issue(
                **{
                    key: message[key]
                    for key in (
                        "kind",
                        "object_id",
                        "snapshot_hash",
                        "current_attempt_id",
                        "old_attempt_id",
                    )
                }
            )
        if action == "open":
            if set(message) != {"version", "action", "stream_id", "scope"}:
                raise ValueError("Exact stream admission message required.")
            uuid_text(message["stream_id"])
            scope = message["scope"]
            if not isinstance(scope, dict):
                raise ValueError("Exact owner scope required.")
            exact_scope = {
                "AccountKey",
                "OwnerKind",
                "ObjectID",
                "OwnerID",
                "Fence",
                "ClaimVersion",
                "NestedToken",
                "RegistrationHash",
                "Epoch",
                "SnapshotHash",
                "ScopeJson",
                "Purpose",
            }
            if (
                set(scope) != exact_scope
                or scope["OwnerKind"] not in {"job", "preparation", "operation"}
                or scope["Purpose"] not in {"mutation", "probe"}
            ):
                raise ValueError("Complete typed owner scope required.")
            uuid_text(scope["ObjectID"])
            closing_probe = scope["OwnerID"] is None
            if closing_probe:
                if (
                    scope["OwnerKind"] != "operation"
                    or scope["Purpose"] != "probe"
                    or scope["NestedToken"] is not None
                    or type(scope["Fence"]) is not int
                    or scope["Fence"] != 0
                ):
                    raise ValueError("Only a closing operation probe may have no owner.")
            else:
                uuid_text(scope["OwnerID"])
            if scope["NestedToken"] is not None:
                uuid_text(scope["NestedToken"])
            if (
                type(scope["ClaimVersion"]) is not int
                or scope["ClaimVersion"] <= 0
                or (not closing_probe and (type(scope["Fence"]) is not int or scope["Fence"] <= 0))
            ):
                raise ValueError("Positive exact fence and claim version required.")
            if scope["Epoch"] is not None and (
                type(scope["Epoch"]) is not int or scope["Epoch"] <= 0
            ):
                raise ValueError("Positive registered epoch required.")
            if not isinstance(scope["AccountKey"], str) or not re.fullmatch(
                r"[A-Za-z0-9_.@:-]{1,128}", scope["AccountKey"]
            ):
                raise ValueError("Registered account identity required.")
            # No free-form SQL values or binary blobs arrive over IPC.
            for key in ("RegistrationHash", "SnapshotHash"):
                if not isinstance(scope.get(key), str) or not re.fullmatch(
                    r"[0-9a-f]{64}", scope[key]
                ):
                    raise ValueError("Canonical registered hash required.")
            scope = dict(scope)
            if not isinstance(scope.get("ScopeJson"), dict) or set(scope["ScopeJson"]) != {
                "resources"
            }:
                raise ValueError("Structured resource membership required.")
            resources = scope["ScopeJson"]["resources"]
            if (
                not isinstance(resources, list)
                or not resources
                or any(
                    not isinstance(item, dict)
                    or set(item) != {"key", "version"}
                    or not isinstance(item["key"], str)
                    or not re.fullmatch(r"[A-Za-z0-9_.@:-]{1,256}", item["key"])
                    or type(item["version"]) is not int
                    or item["version"] <= 0
                    for item in resources
                )
                or [item["key"] for item in resources]
                != sorted({item["key"] for item in resources})
                or "account:" + scope["AccountKey"] not in {item["key"] for item in resources}
            ):
                raise ValueError("Exact sorted resource membership required.")
            from services.export_execution_protocol import encode

            self.registration.authorize_scope(scope)
            for key in ("RegistrationHash", "SnapshotHash"):
                scope[key] = bytes.fromhex(scope[key])
            scope["ScopeJson"] = encode(scope["ScopeJson"]).decode()
            if self.boundary is not None:
                self.boundary.recheck()
            stream = self.authority.open_stream(stream_id=message["stream_id"], scope=scope)
            return {"stream_id": stream, "state": "open"}
        if action == "execute":
            if set(message) != {"version", "action", "request"}:
                raise ValueError("Exact provider request message required.")
            request = ProviderRequest.parse(message["request"])
            return {
                "request_id": request.request_id,
                "result": self.authority.execute(request.message()),
            }
        if action == "close":
            if set(message) != {"version", "action", "stream_id"}:
                raise ValueError("Exact stream closure message required.")
            return self.authority.close_stream(uuid_text(message["stream_id"]))
        raise ValueError("Unsupported authority action.")


def serve(*, manifest, authority, make_pipe, authenticate, broker):
    from core.export_execution_host import MessagePipe

    name = "\\\\.\\pipe\\K98Export-" + manifest["pipe_id"]
    while True:
        handle = make_pipe(
            name,
            authority_sid=manifest["authority_sid"],
            client_sid=manifest["bot_sid"],
            overlapped=True,
        )
        try:
            pipe = MessagePipe(handle, timeout_ms=30000)
            pipe.connect()
            message = pipe.receive()
            authenticate(handle, manifest["bot_sid"], bot_authority_sid=manifest["authority_sid"])
            try:
                result = broker.dispatch(message)
            except Exception:
                # A lost reply is uncertainty to the caller. Never include SQL,
                # provider, credential or private evidence prose in IPC errors.
                reply = {"version": 1, "error": "unresolved_action"}
            else:
                reply = {"version": 1, "result": result}
            pipe.send(reply)
        except Exception:
            # A malformed, stalled, unauthenticated or disconnected peer owns
            # only this connection. Retain all claims and never replay dispatch.
            pass
        finally:
            handle.Close()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Explicit S11 authority; G4 provisioning only")
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args(argv)
    bootstrap(args.manifest, script=__file__)
    from core.export_execution_host import (
        DeploymentBoundary,
        PrivateEvidenceStore,
        WindowsExecutionHost,
        assert_protected_path,
        authenticated_peer,
        create_private_pipe,
        current_sid,
    )
    from services.export_coordination_dal import ExportCoordinationDAL
    from services.export_execution_authority import ExportExecutionAuthority
    from services.export_execution_dal import ExportExecutionDAL
    from services.export_execution_protocol import decode
    from services.export_request_budget import RequestBudget
    from services.export_runtime_composition import verify_installation_contract

    manifest_file = assert_protected_path(args.manifest, private=True)
    raw = manifest_file.read_bytes()
    manifest = manifest_contract(
        decode(raw), script=__file__, current_sid=current_sid(), inspect_path=assert_protected_path
    )
    boundary = DeploymentBoundary(manifest)
    connect = connection_factory(manifest)
    dal = ExportExecutionDAL(connect)
    # This explicit startup performs read-only metadata inspection before an
    # authority session, evidence store, provider child or request can be created.
    # Expected hashes are protected deployment inputs; never learn them here.
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
    budget_dal = ExportCoordinationDAL(
        connect, preparations=True, output_operations=True, execution_evidence=True
    )
    authority = ExportExecutionAuthority(
        dal=dal,
        store=store,
        host=host,
        session_id=session_id,
        budget_factory=lambda account: RequestBudget(budget_dal, account),
    )
    from kvk.dal.source_output_pool_dal import SourceOutputPoolDAL
    from services.export_reconciliation_service import TrustedProofIssuer
    from services.export_runtime_composition import LocalAuthorityClient, RuntimeRegistration

    registration = RuntimeRegistration(manifest["runtime_registration"])
    broker = AuthorityBroker(authority, registration, boundary=boundary)
    broker.issuer = TrustedProofIssuer(
        authority=authority,
        boundary=boundary,
        registration=registration,
        coordinator=budget_dal,
        pools=SourceOutputPoolDAL(connect, execution_evidence=True),
        client=LocalAuthorityClient(broker),
    )
    try:
        serve(
            manifest=manifest,
            authority=authority,
            make_pipe=create_private_pipe,
            authenticate=authenticated_peer,
            broker=broker,
        )
    except KeyboardInterrupt:
        pass
    finally:
        drained = authority.drain()
        if drained:
            dal.transition(
                "session", SessionID=session_id, Action="close", ExpectedVersion=session["Version"]
            )
    # Retained claims require reconciliation; do not report a clean service stop.
    return 0 if drained else 1


if __name__ == "__main__":
    raise SystemExit(main())
