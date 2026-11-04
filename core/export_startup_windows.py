"""Windows startup mechanics for the administrative S11 issuer.

The primary desktop token must match the issuer's linked, filtered identity.
Jobs retain the descendant relationship across the venv redirector/watchdog.
Importing this module performs no native operation.
"""

from dataclasses import dataclass
from pathlib import Path
import subprocess


@dataclass
class CreatedRole:
    process: object
    thread: object
    job: object


@dataclass(frozen=True)
class TerminatedPair:
    bindings: dict
    handles: dict | None = None

    def verify(self):
        """Retained handle exit or a native reboot; never a missing-PID heuristic."""
        import ctypes
        from ctypes import wintypes

        from core.export_process_identity import validate_process_bindings

        validate_process_bindings(self.bindings, self.bindings["bot"]["token_profile"]["user_sid"])
        if self.handles is None:
            boot = boot_filetime()
            if any(value["created_filetime"] >= boot for value in self.bindings.values()):
                raise ValueError("Same-boot unobserved termination requires manual reconciliation.")
            return
        if set(self.handles) != {"authority", "bot"}:
            raise ValueError("Both retained role handles required.")
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        get_pid = kernel.GetProcessId
        get_pid.argtypes = [wintypes.HANDLE]
        get_pid.restype = wintypes.DWORD
        get_times = kernel.GetProcessTimes
        get_times.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
        get_times.restype = wintypes.BOOL
        for role, handle in self.handles.items():
            times = [wintypes.FILETIME() for _ in range(4)]
            expected = self.bindings[role]
            if (
                not signalled(handle)
                or get_pid(int(handle)) != expected["pid"]
                or not get_times(int(handle), *(ctypes.byref(t) for t in times))
                or ((times[0].dwHighDateTime << 32) | times[0].dwLowDateTime)
                != expected["created_filetime"]
            ):
                raise ValueError("Pinned created incarnation has not demonstrably exited.")


def linked_application_token(application_sid):
    """Observe the linked identity, then obtain its usable desktop primary token.

    TokenLinkedToken can expose an identification-only token: it is observation,
    not a launch credential. The Windows-selected desktop token must match its
    identity, capabilities, native authentication ID and session before duplication.
    """
    import ctypes

    import win32api
    import win32security

    from core.export_execution_host import inspect_bot_token

    if not ctypes.windll.shell32.IsUserAnAdmin():
        raise ValueError("Administrative startup issuer required.")
    token = win32security.OpenProcessToken(win32api.GetCurrentProcess(), 0x28)
    try:
        if win32security.GetTokenInformation(token, win32security.TokenElevationType) != 2:
            raise ValueError(
                "Interactive split administrator token required; no credential fallback."
            )
        sid = win32security.ConvertSidToStringSid(
            win32security.GetTokenInformation(token, win32security.TokenUser)[0]
        )
        if sid != application_sid:
            raise ValueError("Issuer belongs to another application account.")
        privilege = win32security.LookupPrivilegeValue(None, "SeImpersonatePrivilege")
        win32security.AdjustTokenPrivileges(token, False, [(privilege, 2)])
        if win32api.GetLastError() != 0:
            raise ValueError("Existing issuer process privilege is unavailable.")
        linked = win32security.GetTokenInformation(token, win32security.TokenLinkedToken)
        try:
            profile = inspect_bot_token(linked, application_sid, observe_only=True)
            if profile["elevated"] or profile["ui_access"] or profile["elevation_type"] != 3:
                raise ValueError("Linked token is not the filtered application token.")
            return desktop_application_token(linked, profile, application_sid), profile
        finally:
            linked.Close()
    finally:
        token.Close()


def verify_desktop_token(linked, desktop, profile, sid, security=None):
    """Do not substitute another desktop account, logon or token capabilities."""
    if security is None:
        import win32security as security

    from core.export_execution_host import inspect_bot_token

    if security.GetTokenInformation(desktop, security.TokenType) != security.TokenPrimary:
        raise ValueError("Desktop primary application token required.")
    if inspect_bot_token(desktop, sid, security=security, observe_only=True) != profile:
        raise ValueError("Desktop token differs from issuer's linked identity.")
    for field in (security.TokenSessionId, security.TokenStatistics):
        observed = security.GetTokenInformation(desktop, field)
        expected = security.GetTokenInformation(linked, field)
        if field == security.TokenStatistics:
            observed, expected = observed["AuthenticationId"], expected["AuthenticationId"]
        if observed != expected:
            raise ValueError("Desktop token belongs to another native logon/session.")
    for field in (security.TokenGroups, security.TokenPrivileges):
        observed = security.GetTokenInformation(desktop, field)
        expected = security.GetTokenInformation(linked, field)
        if field == security.TokenGroups:
            observed = [(security.ConvertSidToStringSid(s), attrs) for s, attrs in observed]
            expected = [(security.ConvertSidToStringSid(s), attrs) for s, attrs in expected]
        if sorted(observed) != sorted(expected):
            raise ValueError("Desktop token capability attributes differ.")


def native_shell_window():
    import ctypes
    from ctypes import wintypes

    function = ctypes.WinDLL("user32", use_last_error=True).GetShellWindow
    function.argtypes = []
    function.restype = wintypes.HWND
    return function()


def desktop_application_token(linked, profile, sid):
    """Use Windows' own shell window, never a searched or user-supplied PID.

    https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getshellwindow
    https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-duplicatetokenex
    """
    import win32security

    process = open_desktop_application_process(linked, profile, sid)
    try:
        desktop = win32security.OpenProcessToken(process, 0x0A)
        try:
            primary = win32security.DuplicateTokenEx(
                desktop,
                win32security.SecurityImpersonation,
                0x0F,
                win32security.TokenPrimary,
                None,
            )
            try:
                verify_desktop_token(linked, primary, profile, sid)
                return primary
            except BaseException:
                primary.Close()
                raise
        finally:
            desktop.Close()
    finally:
        process.Close()


def open_desktop_application_process(linked, profile, sid):
    """Retain the verified native desktop parent; no caller-selected PID."""
    import win32api
    import win32event
    import win32process
    import win32security

    window = native_shell_window()
    if not window:
        raise ValueError("Interactive Windows desktop required; no credential fallback.")
    _, pid = win32process.GetWindowThreadProcessId(window)
    process = win32api.OpenProcess(0x1000 | 0x100000 | 0x80, False, pid)
    try:
        desktop = win32security.OpenProcessToken(process, 8)
        try:
            verify_desktop_token(linked, desktop, profile, sid)
            if (
                native_shell_window() != window
                or win32process.GetWindowThreadProcessId(window)[1] != pid
                or win32event.WaitForSingleObject(process, 0) != 258
            ):
                raise ValueError("Native desktop changed during token acquisition.")
            return process
        finally:
            desktop.Close()
    except BaseException:
        process.Close()
        raise


def _attributes(sid, *, directory=False, application_read=True):
    import pywintypes
    import win32security

    inherit = "OICI" if directory else ""
    acl = f"O:BAG:BAD:P(A;{inherit};FA;;;SY)(A;{inherit};FA;;;BA)"
    if application_read:
        acl += f"(A;{inherit};0x1200a9;;;{sid})"
    attributes = pywintypes.SECURITY_ATTRIBUTES()
    attributes.SECURITY_DESCRIPTOR = (
        win32security.ConvertStringSecurityDescriptorToSecurityDescriptor(acl, 1)
    )
    attributes.bInheritHandle = False
    return attributes


def administrative_path(path, *, private=False):
    """Separate immutable administrator controls from writable runtime evidence."""
    from core.export_execution_host import assert_protected_path

    assert_protected_path(path, allow_current_identity=False)
    return assert_protected_path(path, private=private)


def create_private_directory(path, sid):
    import win32file

    path = Path(path)
    administrative_path(path.parent, private=True)
    win32file.CreateDirectory(str(path), _attributes(sid, directory=True))
    administrative_path(path, private=True)


def write_new_protected(path, raw, sid):
    import win32file

    if not isinstance(raw, bytes) or not 0 < len(raw) <= 16 * 1024 * 1024:
        raise ValueError("Bounded immutable startup file required.")
    path = Path(path)
    administrative_path(path.parent, private=True)
    handle = win32file.CreateFile(str(path), 0x40000000, 0, _attributes(sid), 1, 0x80000000, None)
    try:
        win32file.WriteFile(handle, raw)
        win32file.FlushFileBuffers(handle)
    finally:
        handle.Close()
    administrative_path(path, private=True)
    if path.read_bytes() != raw:
        raise ValueError("Startup file readback differs; retain partial state.")


def create_role(token, command, environment, cwd, sid):
    """Create suspended; assign to an administrator-owned job before execution.

    Native contract: https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-updateprocthreadattribute
    """
    import ctypes
    from ctypes import wintypes
    from typing import Any, cast

    import pywintypes
    import win32job
    import win32process
    import win32security

    from core.export_execution_host import inspect_bot_token

    class STARTUPINFO(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("lpReserved", wintypes.LPWSTR),
            ("lpDesktop", wintypes.LPWSTR),
            ("lpTitle", wintypes.LPWSTR),
            ("dwX", wintypes.DWORD),
            ("dwY", wintypes.DWORD),
            ("dwXSize", wintypes.DWORD),
            ("dwYSize", wintypes.DWORD),
            ("dwXCountChars", wintypes.DWORD),
            ("dwYCountChars", wintypes.DWORD),
            ("dwFillAttribute", wintypes.DWORD),
            ("dwFlags", wintypes.DWORD),
            ("wShowWindow", wintypes.WORD),
            ("cbReserved2", wintypes.WORD),
            ("lpReserved2", ctypes.POINTER(ctypes.c_ubyte)),
            ("hStdInput", wintypes.HANDLE),
            ("hStdOutput", wintypes.HANDLE),
            ("hStdError", wintypes.HANDLE),
        ]

    class PROCESSINFO(ctypes.Structure):
        _fields_ = [
            ("hProcess", wintypes.HANDLE),
            ("hThread", wintypes.HANDLE),
            ("dwProcessId", wintypes.DWORD),
            ("dwThreadId", wintypes.DWORD),
        ]

    class STARTUPINFOEX(ctypes.Structure):
        _fields_ = [("StartupInfo", STARTUPINFO), ("lpAttributeList", ctypes.c_void_p)]

    if not command or not Path(command[0]).is_absolute() or not Path(cwd).is_absolute():
        raise ValueError("Fixed absolute application launch required.")
    if (
        win32security.GetTokenInformation(token, win32security.TokenType)
        != win32security.TokenPrimary
    ):
        raise ValueError("Primary filtered application token required before launch.")
    if not Path(command[0]).is_file() or not Path(cwd).is_dir():
        raise ValueError("Existing application and working directory required.")
    env = (
        "\0".join(
            k + "=" + v for k, v in sorted(environment.items(), key=lambda item: item[0].upper())
        )
        + "\0\0"
    )
    block = ctypes.create_unicode_buffer(env)
    args = ctypes.create_unicode_buffer(subprocess.list2cmdline(command))
    profile = inspect_bot_token(token, sid, observe_only=True)
    if profile["elevated"] or profile["elevation_type"] != 3 or profile["ui_access"]:
        raise ValueError("Filtered application token required before launch.")
    startup = STARTUPINFOEX()
    startup.StartupInfo.cb = ctypes.sizeof(startup)
    startup.StartupInfo.dwFlags = 1
    startup.StartupInfo.wShowWindow = 0
    created = PROCESSINFO()
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    create = kernel.CreateProcessW
    create.argtypes = [
        wintypes.LPCWSTR,
        wintypes.LPWSTR,
        ctypes.c_void_p,
        ctypes.c_void_p,
        wintypes.BOOL,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.LPCWSTR,
        ctypes.POINTER(STARTUPINFOEX),
        ctypes.POINTER(PROCESSINFO),
    ]
    create.restype = wintypes.BOOL
    initialize = kernel.InitializeProcThreadAttributeList
    initialize.argtypes = [
        ctypes.c_void_p,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.POINTER(ctypes.c_size_t),
    ]
    initialize.restype = wintypes.BOOL
    update = kernel.UpdateProcThreadAttribute
    update.argtypes = [
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.c_size_t,
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.c_void_p,
        ctypes.c_void_p,
    ]
    update.restype = wintypes.BOOL
    delete = kernel.DeleteProcThreadAttributeList
    delete.argtypes = [ctypes.c_void_p]
    delete.restype = None
    size = ctypes.c_size_t()
    initialize(None, 1, 0, ctypes.byref(size))
    if not 0 < size.value <= 65536:
        raise ValueError("Bounded native process attribute list required.")
    attributes = ctypes.create_string_buffer(size.value)
    if not initialize(attributes, 1, 0, ctypes.byref(size)):
        raise OSError(ctypes.get_last_error(), "Native process attributes unavailable.")
    parent = None
    try:
        parent = open_desktop_application_process(token, profile, sid)
        parent_value = wintypes.HANDLE(int(parent))
        if not update(
            attributes,
            0,
            0x20000,
            ctypes.byref(parent_value),
            ctypes.sizeof(parent_value),
            None,
            None,
        ):
            raise OSError(ctypes.get_last_error(), "Verified desktop parent unavailable.")
        startup.lpAttributeList = ctypes.cast(attributes, ctypes.c_void_p)
        if not create(
            command[0],
            args,
            None,
            None,
            False,
            4 | 0x400 | 0x08000000 | 0x80000,
            block,
            str(cwd),
            ctypes.byref(startup),
            ctypes.byref(created),
        ):
            raise OSError(ctypes.get_last_error(), "Filtered application launch failed.")
    finally:
        delete(attributes)
        if parent is not None:
            parent.Close()
    # pywin32 accepts a native handle value; its packaged constructor stub omits
    # that argument. Keep both returned native handles under explicit ownership.
    handle_factory = cast(Any, pywintypes.HANDLE)
    process, thread = handle_factory(created.hProcess), handle_factory(created.hThread)
    job = None
    try:
        child_token = win32security.OpenProcessToken(process, 8)
        try:
            verify_desktop_token(token, child_token, profile, sid)
        finally:
            child_token.Close()
        # pywin32 rejects None here; an empty string creates an unnamed job.
        job = win32job.CreateJobObject(_attributes(sid, application_read=False), "")
        limits = win32job.QueryInformationJobObject(job, win32job.JobObjectExtendedLimitInformation)
        limits["BasicLimitInformation"]["LimitFlags"] = 0x2000  # KILL_ON_JOB_CLOSE
        win32job.SetInformationJobObject(job, win32job.JobObjectExtendedLimitInformation, limits)
        win32job.AssignProcessToJobObject(job, process)
        win32process.ResumeThread(thread)
        return CreatedRole(process, thread, job)
    except BaseException:
        # Only the newly created, suspended/unadmitted process may be stopped.
        win32process.TerminateProcess(process, 126)
        thread.Close()
        process.Close()
        if job is not None:
            job.Close()
        raise


def role_member(process, created):
    import win32job

    return bool(win32job.IsProcessInJob(process, created.job))


def signalled(process):
    import win32event

    status = win32event.WaitForSingleObject(process, 0)
    if status not in (0, 258):
        raise ValueError("Created process liveness is unavailable.")
    return status == 0


def release_created_role(created):
    """Normal release only after every descendant has exited."""
    import win32job

    info = win32job.QueryInformationJobObject(
        created.job, win32job.JobObjectBasicAccountingInformation
    )
    if info["ActiveProcesses"] != 0:
        raise ValueError("Owned descendants still running; retain supervisor and job handles.")
    created.thread.Close()
    created.process.Close()
    created.job.Close()


def stop_unadmitted_role(created):
    """Allowed only before a commit could release the held application gates."""
    import win32job

    win32job.TerminateJobObject(created.job, 126)


def boot_filetime():
    """Read the documented local OS boot observation, never infer it from a PID.

    https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/win32-operatingsystem
    """
    import ctypes

    windows = ctypes.create_unicode_buffer(32768)
    if not ctypes.windll.kernel32.GetWindowsDirectoryW(windows, len(windows)):
        raise ValueError("Windows installation path unavailable.")
    executable = Path(windows.value) / "System32/WindowsPowerShell/v1.0/powershell.exe"
    result = subprocess.run(
        [
            str(executable),
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            "(Get-CimInstance Win32_OperatingSystem -ErrorAction Stop).LastBootUpTime.ToUniversalTime().ToFileTimeUtc()",
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
        creationflags=0x08000000,
    )
    raw = result.stdout.strip()
    if len(raw) > 20 or not raw.isdecimal() or not 0 < int(raw) < 2**64:
        raise ValueError("Bounded native boot timestamp required.")
    return int(raw)


def startup_mutex(machine_guid, sid):
    import win32event
    import win32security

    from services.export_execution_protocol import uuid_text

    uuid_text(machine_guid)
    mutex = win32event.CreateMutex(
        _attributes(sid, application_read=False), False, "Global\\K98.S11.Startup." + machine_guid
    )
    try:
        descriptor = win32security.GetSecurityInfo(mutex, 6, 1)
        if (
            win32security.ConvertSidToStringSid(descriptor.GetSecurityDescriptorOwner())
            != "S-1-5-32-544"
        ):
            raise ValueError("Startup mutex is not administrator-owned.")
        result = win32event.WaitForSingleObject(mutex, 0)
        if result not in (0, 128):
            raise ValueError("A startup supervisor already owns this host.")
        return mutex
    except BaseException:
        mutex.Close()
        raise
