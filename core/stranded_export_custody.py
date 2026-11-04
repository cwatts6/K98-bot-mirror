"""Exact live custody for legacy writers without saved historical births.

Inspection uses query-only handles. Separately reviewed recovery can request a
retained termination handle; it never creates birth evidence, changes a source
handle, assigns a process, or changes a job's limits. Unsupported
native layouts, races and ambiguous matches fail closed. Returned observations
are private; the operator-facing report contains only counts and booleans.
"""

from contextlib import ExitStack, contextmanager
import ctypes
from ctypes import wintypes
import hashlib
import os
from pathlib import PureWindowsPath
import re
from uuid import uuid4

from core.export_process_identity import (
    process_snapshot,
    validate_process_descriptor,
    verify_process_snapshot,
)


class CustodyUnavailable(ValueError):
    """Current custody cannot be positively established without mutation."""


def _handles():
    """Bounded x64 SystemExtendedHandleInformation; no kernel addresses escape."""
    if os.name != "nt" or ctypes.sizeof(ctypes.c_void_p) != 8:
        raise CustodyUnavailable("Native x64 Windows inspection required.")

    class Entry(ctypes.Structure):
        _fields_ = [
            ("object", ctypes.c_void_p),
            ("pid", ctypes.c_size_t),
            ("handle", ctypes.c_size_t),
            ("access", wintypes.ULONG),
            ("trace", wintypes.USHORT),
            ("type", wintypes.USHORT),
            ("attributes", wintypes.ULONG),
            ("reserved", wintypes.ULONG),
        ]

    query = ctypes.WinDLL("ntdll").NtQuerySystemInformation
    query.argtypes = [
        wintypes.ULONG,
        ctypes.c_void_p,
        wintypes.ULONG,
        ctypes.POINTER(wintypes.ULONG),
    ]
    query.restype = wintypes.LONG
    size = 1024 * 1024
    for _ in range(7):
        if size > 64 * 1024 * 1024:
            break
        buffer, required = ctypes.create_string_buffer(size), wintypes.ULONG()
        status = query(64, buffer, size, ctypes.byref(required))
        if status == 0:
            count = ctypes.c_size_t.from_buffer(buffer).value
            if (
                required.value > size
                or not 16 <= required.value
                or count > (required.value - 16) // ctypes.sizeof(Entry)
            ):
                raise CustodyUnavailable("Native handle layout is invalid.")
            entries = (Entry * count).from_buffer(buffer, 16)
            return [(e.pid, e.handle, e.type) for e in entries]
        if status & 0xFFFFFFFF != 0xC0000004:
            raise CustodyUnavailable("Native handle enumeration unavailable.")
        size = max(size * 2, required.value)
    raise CustodyUnavailable("Native handle enumeration exceeded its bound.")


def _job_name(handle):
    """Query a handle already proven to be a Job; never query pipe/file names."""

    class UnicodeString(ctypes.Structure):
        _fields_ = [
            ("length", wintypes.USHORT),
            ("maximum", wintypes.USHORT),
            ("buffer", ctypes.c_void_p),
        ]

    query = ctypes.WinDLL("ntdll").NtQueryObject
    query.argtypes = [
        wintypes.HANDLE,
        wintypes.ULONG,
        ctypes.c_void_p,
        wintypes.ULONG,
        ctypes.POINTER(wintypes.ULONG),
    ]
    query.restype = wintypes.LONG
    buffer, required = ctypes.create_string_buffer(65536), wintypes.ULONG()
    if query(int(handle), 1, buffer, len(buffer), ctypes.byref(required)) != 0:
        raise CustodyUnavailable("Job name observation unavailable.")
    value = UnicodeString.from_buffer(buffer)
    if value.length == 0:
        return None
    start, end = ctypes.addressof(buffer), ctypes.addressof(buffer) + len(buffer)
    if (
        not value.buffer
        or value.length % 2
        or not start <= value.buffer <= value.buffer + value.length <= end
    ):
        raise CustodyUnavailable("Job name layout is invalid.")
    name = ctypes.wstring_at(value.buffer, value.length // 2)
    match = re.fullmatch(r"\\BaseNamedObjects\\(K98ExportChild-[0-9a-f]{64})", name)
    return "Global\\" + match[1] if match else None


def _parent(process):
    class Basic(ctypes.Structure):
        _fields_ = [
            ("exit", ctypes.c_ssize_t),
            ("peb", ctypes.c_void_p),
            ("affinity", ctypes.c_size_t),
            ("priority", ctypes.c_ssize_t),
            ("pid", ctypes.c_size_t),
            ("parent", ctypes.c_size_t),
        ]

    query = ctypes.WinDLL("ntdll").NtQueryInformationProcess
    query.argtypes = [
        wintypes.HANDLE,
        wintypes.ULONG,
        ctypes.c_void_p,
        wintypes.ULONG,
        ctypes.POINTER(wintypes.ULONG),
    ]
    query.restype = wintypes.LONG
    basic, required = Basic(), wintypes.ULONG()
    if query(
        int(process), 0, ctypes.byref(basic), ctypes.sizeof(basic), ctypes.byref(required)
    ) != 0 or required.value != ctypes.sizeof(basic):
        raise CustodyUnavailable("Original writer parent observation unavailable.")
    return basic.parent


def _command_matches(argv, binding, child_script, manifest_path, child_id):
    expected = [
        binding["executable"],
        "-I",
        str(child_script),
        "--manifest",
        str(manifest_path),
        "--pipe",
        "\\\\.\\pipe\\K98Export-" + child_id,
        "--child-id",
        child_id,
    ]
    return len(argv) == len(expected) and all(
        PureWindowsPath(a) == PureWindowsPath(b) if i in {0, 2, 4} else a == b
        for i, (a, b) in enumerate(zip(argv, expected, strict=True))
    )


@contextmanager
def retain_writer(
    *, binding, child_script, manifest_path, child_id, expected=None, allow_termination=False
):
    """Require one live writer and one matching Job held by the original authority.

    Inspection copies have QUERY access only. Apply additionally requests
    TERMINATE. Copies are non-inheritable and never use
    DUPLICATE_CLOSE_SOURCE. Handles are released before returning. No provider
    channel is opened. A positive result remains diagnostic, not an Apply token.
    """
    import psutil
    import win32api
    import win32job

    from core.export_execution_host import machine_identity
    from services.export_execution_protocol import uuid_text

    uuid_text(child_id)
    if type(allow_termination) is not bool:
        raise CustodyUnavailable("Explicit recovery handle mode required.")
    if allow_termination and expected is None:
        raise CustodyUnavailable("Reviewed live custody required for termination handles.")
    with ExitStack() as stack:
        authority = win32api.OpenProcess(0x100000 | 0x1000 | 0x0040, False, binding["pid"])
        stack.callback(authority.Close)
        verify_process_snapshot(process_snapshot(authority), binding)
        children = psutil.Process(binding["pid"]).children(recursive=False)
        if len(children) > 256:
            raise CustodyUnavailable("Authority child count exceeds its bound.")
        matches = []
        for candidate in children:
            try:
                argv = candidate.cmdline()
            except psutil.NoSuchProcess:
                raise CustodyUnavailable("Authority child membership changed.") from None
            if not _command_matches(argv, binding, child_script, manifest_path, child_id):
                continue
            child = win32api.OpenProcess(0x100000 | 0x1000, False, candidate.pid)
            stack.callback(child.Close)
            observed = process_snapshot(child)
            if (
                _parent(child) != binding["pid"]
                or observed["created_filetime"] < binding["created_filetime"]
                or observed["token_profile"] != binding["token_profile"]
                or PureWindowsPath(observed["executable"]) != PureWindowsPath(binding["executable"])
                or observed["sha256"] != binding["sha256"]
                or not _command_matches(
                    psutil.Process(observed["pid"]).cmdline(),
                    binding,
                    child_script,
                    manifest_path,
                    child_id,
                )
            ):
                raise CustodyUnavailable("Writer incarnation differs from original authority.")
            matches.append((child, observed))
        if len(matches) != 1:
            raise CustodyUnavailable("Exactly one original live writer required.")
        child, observed = matches[0]
        # Learn this boot's Job type index using an empty, randomly named local
        # sentinel. It never owns a process and has no kill-on-close limits.
        sentinel = win32job.CreateJobObject(None, "K98CustodyDiagnostic-" + uuid4().hex)
        stack.callback(sentinel.Close)
        inventory = _handles()
        types = [
            kind
            for pid, handle, kind in inventory
            if pid == os.getpid() and handle == int(sentinel)
        ]
        if len(types) != 1:
            raise CustodyUnavailable("Native Job type could not be established.")
        candidates = [
            handle for pid, handle, kind in inventory if pid == binding["pid"] and kind == types[0]
        ]
        if len(candidates) > 256:
            raise CustodyUnavailable("Authority Job count exceeds its bound.")
        jobs = []
        for handle in candidates:
            # No SAME_ACCESS or CLOSE_SOURCE. A raced handle must still pass
            # native Job type, name, membership and containment checks below.
            job = win32api.DuplicateHandle(
                authority,
                handle,
                win32api.GetCurrentProcess(),
                0x0004 | (0x0008 if allow_termination else 0),
                False,
                0,
            )
            stack.callback(job.Close)
            limits = win32job.QueryInformationJobObject(job, 9)["BasicLimitInformation"][
                "LimitFlags"
            ]
            name = _job_name(job)
            if name is not None and win32job.IsProcessInJob(child, job):
                if (
                    limits != 0x2000
                    or win32job.QueryInformationJobObject(job, 1)["ActiveProcesses"] < 1
                ):
                    raise CustodyUnavailable("Original writer containment changed.")
                jobs.append((job, name))
        if len(jobs) != 1:
            raise CustodyUnavailable("Exactly one authority-owned private writer Job required.")
        verify_process_snapshot(process_snapshot(authority), binding)
        verify_process_snapshot(process_snapshot(child), observed)
        evidence = dict(
            kind="live_writer_custody/1",
            child_id=child_id,
            authority=binding,
            process=observed,
            job_name=jobs[0][1],
            machine=machine_identity(),
            child_script=str(child_script),
            manifest_path=str(manifest_path),
        )
        validate_custody(evidence, binding)
        if expected is not None and evidence != expected:
            raise CustodyUnavailable("Live custody differs from the exact reviewed writer.")
        retained = CustodyWriter(authority, child, jobs[0][0], evidence, allow_termination)
        retained.inspect()
        yield retained


def inspect_custody(**kwargs):
    """Diagnostic observations never carry termination or recovery authority."""
    with retain_writer(**kwargs) as writer:
        writer.inspect()
        return dict(
            original_authority_alive=True,
            exact_live_writer=True,
            original_parent=True,
            executable_and_token_match=True,
            authority_holds_writer_job=True,
            writer_is_job_member=True,
            no_breakaway_limits=True,
            birth_evidence_created=False,
            termination_authorized=False,
        )


def custody_hash(evidence):
    from services.export_execution_protocol import encode

    return hashlib.sha256(encode(evidence)).hexdigest()


def validate_custody(evidence, binding):
    from core.export_execution_host import machine_identity
    from services.export_execution_protocol import uuid_text

    if (
        not isinstance(evidence, dict)
        or set(evidence)
        != {
            "kind",
            "child_id",
            "authority",
            "process",
            "job_name",
            "machine",
            "child_script",
            "manifest_path",
        }
        or evidence["kind"] != "live_writer_custody/1"
    ):
        raise CustodyUnavailable("Complete reviewed live custody required.")
    uuid_text(evidence["child_id"])
    validate_process_descriptor(binding, binding["token_profile"]["user_sid"])
    process = evidence["process"]
    validate_process_descriptor(process, binding["token_profile"]["user_sid"])
    if (
        evidence["authority"] != binding
        or evidence["machine"] != machine_identity()
        or not isinstance(evidence["job_name"], str)
        or re.fullmatch(r"Global\\K98ExportChild-[0-9a-f]{64}", evidence["job_name"]) is None
        or process["pid"] == binding["pid"]
        or process["created_filetime"] < binding["created_filetime"]
        or process["token_profile"] != binding["token_profile"]
        or process["sha256"] != binding["sha256"]
        or PureWindowsPath(process["executable"]) != PureWindowsPath(binding["executable"])
        or any(
            not isinstance(evidence[k], str) or not PureWindowsPath(evidence[k]).is_absolute()
            for k in ("child_script", "manifest_path")
        )
    ):
        raise CustodyUnavailable("Reviewed live custody identity differs.")


class CustodyWriter:
    def __init__(self, authority, process, job, evidence, allow_termination):
        self.authority, self.process, self.job = authority, process, job
        self.evidence, self.allow_termination = evidence, allow_termination

    def inspect(self):
        import win32job

        verify_process_snapshot(process_snapshot(self.authority), self.evidence["authority"])
        verify_process_snapshot(process_snapshot(self.process), self.evidence["process"])
        if (
            not win32job.IsProcessInJob(self.process, self.job)
            or win32job.QueryInformationJobObject(self.job, 1)["ActiveProcesses"] < 1
            or win32job.QueryInformationJobObject(self.job, 9)["BasicLimitInformation"][
                "LimitFlags"
            ]
            != 0x2000
            or _job_name(self.job) != self.evidence["job_name"]
        ):
            raise CustodyUnavailable("Retained writer containment differs.")

    def terminate_and_observe(self):
        import win32event
        import win32job

        if not self.allow_termination:
            raise CustodyUnavailable("Query-only inspection cannot terminate a writer.")
        self.inspect()
        win32job.TerminateJobObject(self.job, 1)
        if (
            win32event.WaitForSingleObject(self.process, 30000) != 0
            or win32job.QueryInformationJobObject(self.job, 1)["ActiveProcesses"] != 0
        ):
            raise CustodyUnavailable("Exact live writer termination is unconfirmed.")
        return dict(
            child_id=self.evidence["child_id"],
            pid=self.evidence["process"]["pid"],
            process_signaled=True,
            job_empty=True,
            job_name_sha256=hashlib.sha256(self.evidence["job_name"].encode()).hexdigest(),
            observed_process=self.evidence["process"],
            custody_sha256=custody_hash(self.evidence),
        )


def verify_terminated(evidence, receipt, binding):
    """Only recheck a saved positive observation; never infer exit from PID absence."""
    import pywintypes
    import win32job

    validate_custody(evidence, binding)
    expected = dict(
        child_id=evidence["child_id"],
        pid=evidence["process"]["pid"],
        process_signaled=True,
        job_empty=True,
        job_name_sha256=hashlib.sha256(evidence["job_name"].encode()).hexdigest(),
        observed_process=evidence["process"],
        custody_sha256=custody_hash(evidence),
    )
    if receipt != expected:
        raise CustodyUnavailable("Saved live writer termination receipt differs.")
    try:
        job = win32job.OpenJobObject(0x0004, False, evidence["job_name"])
    except pywintypes.error as error:
        if error.winerror != 2:
            raise CustodyUnavailable("Retained live writer Job is inaccessible.") from error
        return
    try:
        if (
            win32job.QueryInformationJobObject(job, 9)["BasicLimitInformation"]["LimitFlags"]
            != 0x2000
            or win32job.QueryInformationJobObject(job, 1)["ActiveProcesses"] != 0
        ):
            raise CustodyUnavailable("Retained live writer Job is not empty and contained.")
    finally:
        job.Close()
