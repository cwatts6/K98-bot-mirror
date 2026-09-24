"""Windows-only containment and authority-private evidence storage.

Importing this module does not create a process, pipe, directory or credential.
Runtime provisioning and live containment tests require a separate exact G4 packet.
"""

import hashlib
from pathlib import Path
import re
import socket
import subprocess

from services.export_execution_protocol import MAX_MESSAGE_BYTES, decode, encode
from services.export_snapshot_store import ExportSnapshotStore, SnapshotReceipt


class HostBoundaryError(RuntimeError):
    """No termination/authentication claim is valid after this failure."""


# Read/write data, read-control, synchronize and FILE_WRITE_ATTRIBUTES (message
# mode selection). Deliberately exclude FILE_CREATE_PIPE_INSTANCE (0x4).
PIPE_CLIENT_ACCESS = 0x120103


def machine_identity():
    """Read the provisioned Windows host identity; never infer it from a caller."""
    import winreg

    with winreg.OpenKey(
        winreg.HKEY_LOCAL_MACHINE,
        r"SOFTWARE\Microsoft\Cryptography",
        0,
        winreg.KEY_READ | winreg.KEY_WOW64_64KEY,
    ) as key:
        guid, kind = winreg.QueryValueEx(key, "MachineGuid")
    if kind != winreg.REG_SZ:
        raise HostBoundaryError("Exact Windows machine identity required.")
    from services.export_execution_protocol import uuid_text

    return {"machine_guid": uuid_text(guid.lower()), "hostname": socket.gethostname().lower()}


class DeploymentBoundary:
    """Protected G4 review record plus current local identity/byte/ACL checks.

    This does not discover or certify provider key custody. Trusted deployment
    administrators supply the reviewed source records at G4. Their exact bytes,
    target and review identity are pinned here; the authority cannot substitute
    a configuration Boolean for those records or learn new pins at startup.
    Provider observations and closed private histories remain separate per-proof
    prerequisites. Changing this packet requires a stopped/drained deployment.
    """

    RECORDS = frozenset(
        {
            "host_acl",
            "bot_identity",
            "identity_issuance",
            "key_inventory",
            "file_access",
            "writer_drain",
            "sql_installation",
        }
    )

    def __init__(self, manifest, *, inspect_path=None, observe_host=None, observe_sid=None):
        # Defaults are resolved at use, after module definition and only on the
        # explicit authority startup path. Tests inject reads, never host APIs.
        self._inspect = inspect_path or assert_protected_path
        self._host = observe_host or machine_identity
        self._sid = observe_sid or current_sid
        self._manifest = decode(encode(manifest))
        self._raw = encode(self._manifest["deployment_boundary"])
        self.recheck()

    @property
    def fingerprint(self):
        return hashlib.sha256(self._raw).hexdigest()

    def recheck(self):
        from services.export_execution_protocol import uuid_text

        m, value = self._manifest, decode(self._raw)
        fields = {
            "version",
            "deployment_id",
            "host",
            "authority_sid",
            "bot_sid",
            "identity",
            "source_hash",
            "registration_hash",
            "sql_contract_hash",
            "paths",
            "review",
        }
        if (
            not isinstance(value, dict)
            or set(value) != fields
            or type(value["version"]) is not int
            or value["version"] != 1
        ):
            raise HostBoundaryError("Exact reviewed deployment boundary required.")
        uuid_text(value["deployment_id"])
        if (
            value["host"] != self._host()
            or value["authority_sid"] != self._sid()
            or value["authority_sid"] != m["authority_sid"]
            or value["bot_sid"] != m["bot_sid"]
            or value["authority_sid"] == value["bot_sid"]
        ):
            raise HostBoundaryError("Deployment belongs to another host or identity.")
        for field, source in (
            ("source_hash", "source_hashes"),
            ("registration_hash", "runtime_registration"),
            ("sql_contract_hash", "sql_contract"),
        ):
            if value[field] != hashlib.sha256(encode(m[source])).hexdigest():
                raise HostBoundaryError("Deployment source, registration or SQL pin differs.")
        paths = {
            name: m[name]
            for name in ("python", "child_script", "credentials_file", "evidence_root")
        }
        if value["paths"] != paths:
            raise HostBoundaryError("Deployment custody paths differ.")
        for name, path in paths.items():
            self._inspect(path, private=name in {"credentials_file", "evidence_root"})
        identity = value["identity"]
        if (
            not isinstance(identity, dict)
            or set(identity)
            != {
                "service_account_email",
                "previous_service_account_email",
                "project_id",
                "client_id",
                "private_key_id",
                "credential_sha256",
            }
            or identity["service_account_email"] != m["service_account_email"]
            or identity["project_id"] != m["project_id"]
            or identity["previous_service_account_email"] == identity["service_account_email"]
            or not re.fullmatch(
                r"[A-Za-z0-9_.@-]{3,254}", identity["previous_service_account_email"]
            )
            or not re.fullmatch(r"[0-9]{1,32}", identity["client_id"])
            or not re.fullmatch(r"[0-9a-f]{40}", identity["private_key_id"])
        ):
            raise HostBoundaryError("Fresh exact service-account/key identity required.")
        raw = Path(paths["credentials_file"]).read_bytes()
        if len(raw) > 65536 or hashlib.sha256(raw).hexdigest() != identity["credential_sha256"]:
            raise HostBoundaryError("Protected credential bytes differ.")
        credential = decode(raw)
        if (
            credential.get("type") != "service_account"
            or credential.get("token_uri") != "https://oauth2.googleapis.com/token"
            or any(
                credential.get(k) != identity[k]
                for k in ("project_id", "client_id", "private_key_id")
            )
            or credential.get("client_email") != identity["service_account_email"]
        ):
            raise HostBoundaryError("Credential identity differs from reviewed issuance.")
        review = value["review"]
        if (
            not isinstance(review, dict)
            or set(review) != {"review_id", "administrators", "records"}
            or not isinstance(review["administrators"], dict)
            or set(review["administrators"]) != {"windows", "sql", "provider"}
            or any(
                not isinstance(v, str) or not v.strip() or len(v) > 256
                for v in review["administrators"].values()
            )
            or not isinstance(review["records"], dict)
            or set(review["records"]) != self.RECORDS
        ):
            raise HostBoundaryError("Complete named G4 review and source records required.")
        uuid_text(review["review_id"])
        seen = set()
        for kind, reference in review["records"].items():
            if (
                not isinstance(reference, dict)
                or set(reference) != {"path", "sha256"}
                or not isinstance(reference["sha256"], str)
                or not re.fullmatch(r"[0-9a-f]{64}", reference["sha256"])
            ):
                raise HostBoundaryError("Exact G4 source record reference required.")
            path = self._inspect(reference["path"], private=True)
            if str(path).casefold() in seen:
                raise HostBoundaryError("Distinct G4 source records required.")
            seen.add(str(path).casefold())
            with Path(path).open("rb") as source:
                raw = source.read(MAX_MESSAGE_BYTES + 1)
            if (
                len(raw) > MAX_MESSAGE_BYTES
                or hashlib.sha256(raw).hexdigest() != reference["sha256"]
            ):
                raise HostBoundaryError("Reviewed G4 source record differs.")
            record = decode(raw)
            if (
                not isinstance(record, dict)
                or set(record) != {"version", "kind", "deployment_id", "review_id", "observations"}
                or type(record["version"]) is not int
                or record["version"] != 1
                or record["kind"] != kind
                or record["deployment_id"] != value["deployment_id"]
                or record["review_id"] != review["review_id"]
                or not isinstance(record["observations"], list)
                or not record["observations"]
                or any(not isinstance(row, dict) or not row for row in record["observations"])
            ):
                raise HostBoundaryError("Reviewed source observations are missing or foreign.")
            self._validate_observations(kind, record["observations"], value)
        return self.fingerprint

    def _validate_observations(self, kind, rows, boundary):
        """Validate normalized G4 observations; the protected review supplies provenance.

        Source exports and their interpretation are reviewed by the named trusted
        administrators. These checks prevent missing/contradictory input, not a
        malicious administrator or an unobserved post-review maintenance change.
        """
        from datetime import datetime

        def instant(value):
            if not isinstance(value, str):
                raise HostBoundaryError("Exact UTC observation time required.")
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError as exc:
                raise HostBoundaryError("Exact UTC observation time required.") from exc
            if parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
                raise HostBoundaryError("UTC observation time required.")
            return parsed

        def exact(row, fields):
            if not isinstance(row, dict) or set(row) != set(fields.split()):
                raise HostBoundaryError("Complete typed G4 observations required.")

        m, identity = self._manifest, boundary["identity"]
        if kind == "host_acl":
            found = set()
            for row in rows:
                exact(row, "path owner_sid sddl observed_utc")
                instant(row["observed_utc"])
                if (
                    row["path"] not in boundary["paths"].values()
                    or row["path"] in found
                    or row["owner_sid"] not in {m["authority_sid"], "S-1-5-18", "S-1-5-32-544"}
                    or not isinstance(row["sddl"], str)
                    or not row["sddl"].startswith("O:")
                    or "D:" not in row["sddl"]
                ):
                    raise HostBoundaryError("Complete protected path ACL observations required.")
                found.add(row["path"])
            if found != set(boundary["paths"].values()):
                raise HostBoundaryError("Every custody path needs an ACL observation.")
        elif kind == "file_access":
            registration = m["runtime_registration"]
            expected = {
                target
                for configured in registration["legacy_configuration"].values()
                for target in configured["destinations"]
            }
            owners = {}
            for pool in registration["pools"]:
                for target in [pool["index_file_id"], *pool["slot_file_ids"]]:
                    expected.add(target)
                    owners[target] = pool["owner_email"]
            found = set()
            for row in rows:
                exact(row, "file_id owner_email editors audience observed_utc")
                instant(row["observed_utc"])
                if (
                    row["file_id"] not in expected
                    or row["file_id"] in found
                    or row["owner_email"]
                    != owners.get(row["file_id"], boundary["review"]["administrators"]["provider"])
                    or row["editors"] != [identity["service_account_email"]]
                    or row["audience"] not in {"private", "anyone_reader"}
                ):
                    raise HostBoundaryError(
                        "Exact owners, sole authority editor and reader audience required."
                    )
                found.add(row["file_id"])
            if found != expected:
                raise HostBoundaryError("Every admitted file needs an access observation.")
        else:
            if len(rows) != 1:
                raise HostBoundaryError("One exact deployment observation required.")
            row = rows[0]
            if kind == "bot_identity":
                exact(
                    row,
                    "host user_sid group_sids privileges elevation_type elevated ui_access observed_utc",
                )
                instant(row["observed_utc"])
                if row["host"] != boundary["host"]:
                    raise HostBoundaryError("Bot account observation belongs to another host.")
                validate_bot_token_profile(
                    {k: v for k, v in row.items() if k not in {"host", "observed_utc"}},
                    m["bot_sid"],
                    authority_sid=m["authority_sid"],
                )
            elif kind == "identity_issuance":
                exact(
                    row,
                    "service_account_email project_id client_id private_key_id created_utc issued_utc custody_path issuing_administrator",
                )
                if (
                    any(
                        row[k] != identity[k]
                        for k in (
                            "service_account_email",
                            "project_id",
                            "client_id",
                            "private_key_id",
                        )
                    )
                    or instant(row["created_utc"]) > instant(row["issued_utc"])
                    or row["custody_path"] != m["credentials_file"]
                    or row["issuing_administrator"]
                    != boundary["review"]["administrators"]["provider"]
                ):
                    raise HostBoundaryError(
                        "Fresh issuance and private custody observation differs."
                    )
            elif kind == "key_inventory":
                exact(
                    row,
                    "service_account_email user_managed_key_ids credential_holders observed_utc",
                )
                instant(row["observed_utc"])
                if (
                    row["service_account_email"] != identity["service_account_email"]
                    or row["user_managed_key_ids"] != [identity["private_key_id"]]
                    or row["credential_holders"] != [m["authority_sid"]]
                ):
                    raise HostBoundaryError("Sole reviewed key and authority custody required.")
            elif kind == "sql_installation":
                exact(row, "contract_sha256 observed_utc server database principal")
                instant(row["observed_utc"])
                if row["contract_sha256"] != boundary["sql_contract_hash"] or any(
                    row[k] != m["sql_contract"][k] for k in ("server", "database", "principal")
                ):
                    raise HostBoundaryError("Reviewed SQL installation differs.")
            elif kind == "writer_drain":
                exact(row, "host processes sql_sessions remaining_writers observed_utc")
                observed = instant(row["observed_utc"])
                if (
                    row["host"] != boundary["host"]
                    or row["remaining_writers"] != []
                    or not isinstance(row["processes"], list)
                    or not row["processes"]
                    or not isinstance(row["sql_sessions"], list)
                ):
                    raise HostBoundaryError("Exact prior writer drain records required.")
                for process in row["processes"]:
                    exact(process, "pid started_utc image_sha256 exit_code exited_utc")
                    if (
                        type(process["pid"]) is not int
                        or process["pid"] <= 0
                        or type(process["exit_code"]) is not int
                        or not isinstance(process["image_sha256"], str)
                        or not re.fullmatch(r"[0-9a-f]{64}", process["image_sha256"])
                        or not instant(process["started_utc"])
                        <= instant(process["exited_utc"])
                        <= observed
                    ):
                        raise HostBoundaryError("Exact exited old process identity required.")
                for session in row["sql_sessions"]:
                    exact(session, "session_id login_name login_utc ended_utc")
                    if (
                        type(session["session_id"]) is not int
                        or session["session_id"] <= 0
                        or not isinstance(session["login_name"], str)
                        or not session["login_name"]
                        or not instant(session["login_utc"])
                        <= instant(session["ended_utc"])
                        <= observed
                    ):
                        raise HostBoundaryError("Exact ended old SQL producer session required.")


def current_sid():
    import win32api
    import win32security

    token = win32security.OpenProcessToken(win32api.GetCurrentProcess(), 8)
    try:
        sid, _ = win32security.GetTokenInformation(token, win32security.TokenUser)
        return win32security.ConvertSidToStringSid(sid)
    finally:
        token.Close()


def assert_protected_path(path, *, private=False, allow_current_identity=True):
    """Reject reparse points and untrusted replacement/read access before use.

    Provision paths under authority/SYSTEM/Administrators ownership. Ancestors
    must not let another identity replace a child. Broad/incomprehensible ACLs
    are refused rather than interpreted as a deployment attestation.
    """
    from scripts.run_export_authority import AuthorityStartupError, protected_path

    try:
        return protected_path(
            path,
            private=private,
            allow_current_identity=allow_current_identity,
            identity=current_sid() if allow_current_identity else None,
        )
    except AuthorityStartupError as exc:
        raise HostBoundaryError(str(exc)) from exc


class PrivateEvidenceStore:
    """DPAPI protects payloads under the independent authority's Windows identity.

    Root ACL and service identity are checked during explicitly approved startup.
    The existing immutable fsync/readback store supplies byte-integrity semantics.
    No temp-root default, directory creation or evidence garbage collection.
    """

    def __init__(self, root, owner, *, protect=None, unprotect=None):
        if protect is None or unprotect is None:
            import win32crypt

            protect = lambda data: win32crypt.CryptProtectData(
                data, "K98 export evidence", None, None, None, 1
            )
            unprotect = lambda data: win32crypt.CryptUnprotectData(data, None, None, None, 1)[1]
        self._protect, self._unprotect = protect, unprotect
        self._store = ExportSnapshotStore(root, owner, max_bytes=MAX_MESSAGE_BYTES + 65536)

    def put(self, data):
        encrypted = self._protect(data)
        receipt = self._store.put(encrypted)
        if self._unprotect(self._store.read(receipt)) != data:
            raise HostBoundaryError("Evidence encryption readback differs.")
        # SQL stores plaintext hash and opaque UUID. The file remains encrypted.
        return SnapshotReceipt(
            receipt.key, len(data), hashlib.sha256(data).hexdigest(), receipt.storage_owner
        )

    def read(self, receipt):
        path = self._store._path(receipt.key)
        with path.open("rb") as source:
            encrypted = source.read(self._store.max_bytes + 1)
        if len(encrypted) > self._store.max_bytes:
            raise HostBoundaryError("Encrypted evidence exceeds bound.")
        data = self._unprotect(encrypted)
        if len(data) != receipt.byte_count or hashlib.sha256(data).hexdigest() != receipt.sha256:
            raise HostBoundaryError("Evidence hash/length differs.")
        return data

    def read_reference(self, reference, expected_hash):
        from uuid import UUID

        path = self._store._path(UUID(str(reference)).hex)
        with path.open("rb") as source:
            encrypted = source.read(self._store.max_bytes + 1)
        if len(encrypted) > self._store.max_bytes:
            raise HostBoundaryError("Encrypted evidence exceeds bound.")
        data = self._unprotect(encrypted)
        if hashlib.sha256(data).digest() != bytes(expected_hash):
            raise HostBoundaryError("Retained evidence hash differs.")
        return data


class MessagePipe:
    def __init__(self, handle, *, api=None, timeout_ms=None, event_api=None, overlapped=None):
        if api is None:
            import win32file

            api = win32file
        self.handle, self.api = handle, api
        if timeout_ms is not None:
            if type(timeout_ms) is not int or not 0 < timeout_ms <= 30000:
                raise HostBoundaryError("Bounded pipe deadline required.")
            if event_api is None:
                import win32event

                event_api = win32event
            if overlapped is None:
                import pywintypes

                overlapped = pywintypes.OVERLAPPED
        self.timeout_ms, self.events, self.overlapped = timeout_ms, event_api, overlapped

    def _bounded_io(self, start):
        """One overlapped operation; cancellation completes before buffer release.

        The caller keeps its read/write buffer alive across this entire call.
        A timeout is never proof that an action or reply did not happen.
        """
        operation = self.overlapped()
        operation.hEvent = self.events.CreateEvent(None, True, False, None)
        pending = True
        try:
            status = start(operation)
            pending = status == 997  # ERROR_IO_PENDING
            if status is None:  # Connect completed before an I/O request was issued.
                return 0
            if status not in (0, 997):
                raise HostBoundaryError("Incomplete IPC operation; do not replay.")
            if pending and self.events.WaitForSingleObject(operation.hEvent, self.timeout_ms) != 0:
                raise HostBoundaryError("IPC deadline expired; outcome is unresolved.")
            count = self.api.GetOverlappedResult(self.handle, operation, False)
            pending = False
            return count
        finally:
            try:
                if pending:
                    try:
                        # This issuing thread owns the sole pending operation
                        # on this handle. CancelIo is the pywin32 API; no helper
                        # thread or provider operation shares this Bot pipe.
                        self.api.CancelIo(self.handle)
                    finally:
                        try:
                            self.api.GetOverlappedResult(self.handle, operation, True)
                        except Exception as exc:
                            if getattr(exc, "winerror", None) not in (995, 109, 232, 234):
                                raise
            finally:
                operation.hEvent.Close()

    def connect(self):
        """Bounded accept for an overlapped Bot-facing server handle."""
        import win32pipe

        def start(operation):
            status = win32pipe.ConnectNamedPipe(self.handle, operation)
            return None if status == 535 else status

        self._bounded_io(start)

    def send(self, message):
        raw = encode(message)
        if self.timeout_ms is None:
            status, count = self.api.WriteFile(self.handle, raw)
        else:
            count = self._bounded_io(
                lambda operation: self.api.WriteFile(self.handle, raw, operation)[0]
            )
            status = 0
        if status != 0 or count != len(raw):
            raise HostBoundaryError("Incomplete IPC write; do not replay.")

    def receive(self):
        if self.timeout_ms is not None:
            # A single buffer bounds the complete frame, including slow partial
            # writes; a per-chunk deadline would allow an indefinite trickle.
            buffer = self.api.AllocateReadBuffer(MAX_MESSAGE_BYTES + 1)
            count = self._bounded_io(
                lambda operation: self.api.ReadFile(self.handle, buffer, operation)[0]
            )
            if not 0 < count <= MAX_MESSAGE_BYTES:
                raise HostBoundaryError("Invalid or oversized IPC message.")
            return decode(bytes(buffer[:count]))
        chunks, size = [], 0
        while True:
            status, chunk = self.api.ReadFile(self.handle, min(65536, MAX_MESSAGE_BYTES - size + 1))
            size += len(chunk)
            if not chunk or size > MAX_MESSAGE_BYTES or status not in (0, 234):
                raise HostBoundaryError("Invalid or oversized IPC message.")
            chunks.append(chunk)
            if status == 0:
                return decode(b"".join(chunks))


def open_message_pipe(name):
    """Open one client endpoint with only the rights needed by this protocol."""
    import win32file
    import win32pipe

    handle = win32file.CreateFile(name, PIPE_CLIENT_ACCESS, 0, None, 3, 0, None)
    try:
        win32pipe.SetNamedPipeHandleState(handle, 2, None, None)
        return handle
    except BaseException:
        handle.Close()
        raise


def create_private_pipe(name, *, authority_sid, client_sid, overlapped=False):
    import pywintypes
    import win32pipe
    import win32security

    # Explicit SID parsing prevents SDDL injection. The caller does not receive
    # FILE_CREATE_PIPE_INSTANCE (0x4), unlike generic write access.
    for sid in (authority_sid, client_sid):
        if win32security.ConvertSidToStringSid(win32security.ConvertStringSidToSid(sid)) != sid:
            raise HostBoundaryError("Canonical Windows SID required.")
    if not name.startswith("\\\\.\\pipe\\K98Export-") or any(
        c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-"
        for c in name.removeprefix("\\\\.\\pipe\\")
    ):
        raise HostBoundaryError("Local registered pipe name required.")
    descriptor = win32security.ConvertStringSecurityDescriptorToSecurityDescriptor(
        f"D:P(A;;GA;;;{authority_sid})(A;;0x{PIPE_CLIENT_ACCESS:x};;;{client_sid})", 1
    )
    attributes = pywintypes.SECURITY_ATTRIBUTES()
    attributes.SECURITY_DESCRIPTOR = descriptor
    attributes.bInheritHandle = False
    flags = 3 | 0x80000 | (0x40000000 if overlapped else 0)
    return win32pipe.CreateNamedPipe(name, flags, 4 | 2 | 8, 1, 65536, 65536, 0, attributes)


def validate_bot_token_profile(profile, expected_sid, *, authority_sid=None):
    """Reject privileged Bot identities, including disabled privileges/admin SIDs.

    Windows can enable a privilege already present in a token. A deny-only admin
    SID also indicates a filtered privileged account, unsuitable for private-key
    separation. This checks the actual IPC token, not an operator approval flag.
    Trusted Windows administrators remain outside this account boundary.
    """
    fields = {"user_sid", "group_sids", "privileges", "elevation_type", "elevated", "ui_access"}
    if not isinstance(profile, dict) or set(profile) != fields:
        raise HostBoundaryError("Complete Bot token profile required.")
    for field in ("group_sids", "privileges"):
        values = profile[field]
        if (
            not isinstance(values, list)
            or not all(isinstance(v, str) for v in values)
            or values != sorted(set(values))
        ):
            raise HostBoundaryError("Canonical Bot token groups and privileges required.")
    privileged_sids = {
        "S-1-5-18",
        "S-1-5-19",
        "S-1-5-20",
        "S-1-5-32-544",
        "S-1-5-32-548",
        "S-1-5-32-549",
        "S-1-5-32-550",
        "S-1-5-32-551",
        "S-1-5-32-552",
        "S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464",
        authority_sid,
    }
    identities = [profile["user_sid"], *profile["group_sids"]]
    if (
        profile["user_sid"] != expected_sid
        or any(
            not isinstance(sid, str) or not re.fullmatch(r"S-1-(?:[0-9]+-)*[0-9]+", sid)
            for sid in identities
        )
        or any(
            sid in privileged_sids
            or re.fullmatch(r"S-1-5-21-[0-9]+-[0-9]+-[0-9]+-(512|518|519)", sid)
            for sid in identities
        )
        or type(profile["elevation_type"]) is not int
        or profile["elevation_type"] != 1
        or profile["elevated"] is not False
        or profile["ui_access"] is not False
        or not set(profile["privileges"])
        <= {
            "SeChangeNotifyPrivilege",
            "SeIncreaseWorkingSetPrivilege",
            "SeTimeZonePrivilege",
            "SeShutdownPrivilege",
            "SeUndockPrivilege",
        }
    ):
        raise HostBoundaryError("Bot must use a nonprivileged account without authority access.")


def inspect_bot_token(token, expected_sid, *, authority_sid=None, security=None):
    if security is None:
        import win32security as security
    sid, _ = security.GetTokenInformation(token, security.TokenUser)
    profile = dict(
        user_sid=security.ConvertSidToStringSid(sid),
        group_sids=sorted(
            {
                security.ConvertSidToStringSid(s)
                for s, _ in security.GetTokenInformation(token, security.TokenGroups)
            }
        ),
        privileges=sorted(
            {
                security.LookupPrivilegeName(None, luid)
                for luid, _ in security.GetTokenInformation(token, security.TokenPrivileges)
            }
        ),
        elevation_type=security.GetTokenInformation(token, security.TokenElevationType),
        elevated=bool(security.GetTokenInformation(token, security.TokenElevation)),
        ui_access=bool(security.GetTokenInformation(token, security.TokenUIAccess)),
    )
    validate_bot_token_profile(profile, expected_sid, authority_sid=authority_sid)


def authenticated_peer(handle, expected_sid, *, expected_pid=None, bot_authority_sid=None):
    import win32api
    import win32pipe
    import win32security

    win32pipe.ImpersonateNamedPipeClient(handle)
    try:
        token = win32security.OpenThreadToken(win32api.GetCurrentThread(), 8, True)
        try:
            sid, _ = win32security.GetTokenInformation(token, win32security.TokenUser)
            actual = win32security.ConvertSidToStringSid(sid)
            if bot_authority_sid is not None:
                inspect_bot_token(token, expected_sid, authority_sid=bot_authority_sid)
        finally:
            token.Close()
        if actual != expected_sid:
            raise HostBoundaryError("Unexpected IPC principal.")
    finally:
        win32security.RevertToSelf()
    if expected_pid is not None:
        # PID is checked in addition to the parent's retained process handle,
        # never used to rediscover/adopt a process after restart.
        import ctypes
        from ctypes import wintypes

        function = ctypes.WinDLL("kernel32", use_last_error=True).GetNamedPipeClientProcessId
        function.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.ULONG)]
        function.restype = wintypes.BOOL
        pid = wintypes.ULONG()
        if not function(int(handle), ctypes.byref(pid)) or pid.value != expected_pid:
            raise HostBoundaryError("Unexpected provider child process.")


def authenticated_server(handle, expected_sid):
    """Pin the exact local pipe server's process handle and Windows identity."""
    import ctypes
    from ctypes import wintypes

    import win32api
    import win32event
    import win32security

    function = ctypes.WinDLL("kernel32", use_last_error=True).GetNamedPipeServerProcessId
    function.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.ULONG)]
    function.restype = wintypes.BOOL
    pid = wintypes.ULONG()
    if not function(int(handle), ctypes.byref(pid)) or not pid.value:
        raise HostBoundaryError("Authority pipe server identity is unavailable.")
    process = win32api.OpenProcess(0x1000 | 0x100000, False, pid.value)
    try:
        token = win32security.OpenProcessToken(process, 8)
        try:
            sid, _ = win32security.GetTokenInformation(token, win32security.TokenUser)
            if win32security.ConvertSidToStringSid(sid) != expected_sid:
                raise HostBoundaryError("Authority pipe belongs to another Windows identity.")
        finally:
            token.Close()
        if win32event.WaitForSingleObject(process, 0) != 258:
            raise HostBoundaryError("Authority pipe server process already exited.")
        return process
    except BaseException:
        process.Close()
        raise


class WindowsProviderChild:
    def __init__(self, *, identity, process, thread, job, pid, pipe, sid, api):
        self.identity, self.process, self.thread, self.job = identity, process, thread, job
        self.pid, self.pipe, self.sid, self.api = pid, pipe, sid, api
        self.resumed = False
        self.terminated = False

    def resume(self):
        if self.resumed or self.terminated:
            raise HostBoundaryError("Child cannot be resumed again.")
        self.api["process"].ResumeThread(self.thread)
        self.thread.Close()
        self.thread = None
        self.resumed = True
        try:
            self.api["pipe"].ConnectNamedPipe(self.pipe.handle, None)
        except self.api["error"] as exc:
            if exc.winerror != 535:  # Client may connect before ConnectNamedPipe.
                raise
        hello = self.pipe.receive()
        authenticated_peer(self.pipe.handle, self.sid, expected_pid=self.pid)
        if hello != {"child_id": self.identity, "version": 1}:
            raise HostBoundaryError("Child handshake differs.")

    def execute(self, message):
        if not self.resumed or self.terminated:
            raise HostBoundaryError("Provider child is not live.")
        self.pipe.send(message)
        response = self.pipe.receive()
        if (
            set(response) != {"request_id", "result"}
            or response["request_id"] != message["request_id"]
        ):
            raise HostBoundaryError("Provider response identity differs.")
        return response["result"]

    def terminate_and_observe(self):
        if self.terminated:
            raise HostBoundaryError("Closed handles are not fresh termination evidence.")
        self.api["job"].TerminateJobObject(self.job, 1)
        if self.api["event"].WaitForSingleObject(self.process, 30000) != 0:
            raise HostBoundaryError("Exact provider process termination is unproven.")
        accounting = self.api["job"].QueryInformationJobObject(self.job, 1)
        if accounting["ActiveProcesses"] != 0:
            raise HostBoundaryError("Provider descendants remain live.")
        evidence = {
            "child_id": self.identity,
            "pid": self.pid,
            "job_empty": True,
            "process_signaled": True,
        }
        self.terminated = True
        for handle in (self.thread, self.process, self.job, self.pipe.handle):
            if handle is not None:
                handle.Close()
        return evidence


class WindowsExecutionHost:
    def __init__(self, *, python, child_script, manifest, authority_sid):
        self.python, self.child_script, self.manifest = map(Path, (python, child_script, manifest))
        if any(
            not p.is_absolute() or not p.is_file()
            for p in (self.python, self.child_script, self.manifest)
        ):
            raise HostBoundaryError("Exact provisioned executable/script/manifest paths required.")
        for path in (self.python, self.child_script):
            assert_protected_path(path)
        assert_protected_path(self.manifest, private=True)
        self.sid = authority_sid

    def create_suspended(self, identity):
        import pywintypes
        import win32event
        import win32job
        import win32pipe
        import win32process

        name = "\\\\.\\pipe\\K98Export-" + identity
        pipe = create_private_pipe(name, authority_sid=self.sid, client_sid=self.sid)
        job = win32job.CreateJobObject(None, None)
        limits = win32job.QueryInformationJobObject(job, 9)
        limits["BasicLimitInformation"]["LimitFlags"] = 0x2000  # KILL_ON_JOB_CLOSE; no breakaway.
        win32job.SetInformationJobObject(job, 9, limits)
        process = thread = None
        try:
            command = subprocess.list2cmdline(
                [
                    str(self.python),
                    "-I",
                    str(self.child_script),
                    "--manifest",
                    str(self.manifest),
                    "--pipe",
                    name,
                    "--child-id",
                    identity,
                ]
            )
            process, thread, pid, _ = win32process.CreateProcess(
                None,
                command,
                None,
                None,
                False,
                0x4 | 0x8000000,
                None,
                str(self.child_script.parent),
                win32process.STARTUPINFO(),
            )
            win32job.AssignProcessToJobObject(job, process)
            return WindowsProviderChild(
                identity=identity,
                process=process,
                thread=thread,
                job=job,
                pid=pid,
                pipe=MessagePipe(pipe),
                sid=self.sid,
                api={
                    "job": win32job,
                    "process": win32process,
                    "event": win32event,
                    "pipe": win32pipe,
                    "error": pywintypes.error,
                },
            )
        except BaseException:
            if process is not None:
                # Assignment failure must terminate the still-suspended process.
                win32process.TerminateProcess(process, 1)
                win32event.WaitForSingleObject(process, 30000)
                process.Close()
            if thread is not None:
                thread.Close()
            job.Close()
            pipe.Close()
            raise
