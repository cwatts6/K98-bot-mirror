"""Exact process pins for the shared-account export application.

These distinguish approved process incarnations, not hostile code running as the
same Windows account. Importing this module performs no native observations.
"""

import hashlib
from pathlib import Path, PureWindowsPath
import re

TRUST_MODEL = "single_account_application_v1"
TOKEN_FIELDS = {"user_sid", "group_sids", "privileges", "elevation_type", "elevated", "ui_access"}


def validate_token_profile(value, sid):
    if not isinstance(value, dict) or set(value) != TOKEN_FIELDS or value["user_sid"] != sid:
        raise ValueError("Exact reviewed application token required.")
    for field in ("group_sids", "privileges"):
        items = value[field]
        if (
            not isinstance(items, list)
            or not all(isinstance(item, str) and item for item in items)
            or items != sorted(set(items))
        ):
            raise ValueError("Canonical application token capabilities required.")
    if (
        not all(re.fullmatch(r"S-1-(?:[0-9]+-)*[0-9]+", s) for s in [sid, *value["group_sids"]])
        or type(value["elevation_type"]) is not int
        or value["elevation_type"] not in (1, 2, 3)
        or type(value["elevated"]) is not bool
        or type(value["ui_access"]) is not bool
    ):
        raise ValueError("Complete reviewed application token required.")


def validate_process_descriptor(value, sid):
    if (
        not isinstance(value, dict)
        or set(value) != {"pid", "created_filetime", "executable", "sha256", "token_profile"}
        or type(value["pid"]) is not int
        or not 0 < value["pid"] < 2**32
        or type(value["created_filetime"]) is not int
        or not 0 < value["created_filetime"] < 2**64
        or not isinstance(value["executable"], str)
        or not PureWindowsPath(value["executable"]).is_absolute()
        or not isinstance(value["sha256"], str)
        or not re.fullmatch(r"[0-9a-f]{64}", value["sha256"])
    ):
        raise ValueError("Exact reviewed process incarnation required.")
    validate_token_profile(value["token_profile"], sid)


def validate_process_bindings(value, sid):
    if not isinstance(value, dict) or set(value) != {"authority", "bot"}:
        raise ValueError("Both application process bindings required.")
    for descriptor in value.values():
        validate_process_descriptor(descriptor, sid)
    if value["authority"]["pid"] == value["bot"]["pid"]:
        raise ValueError("Distinct supervised process incarnations required.")


def process_snapshot(process):
    """Observe a retained process handle, without opening another process by PID."""
    import ctypes
    from ctypes import wintypes

    import win32event
    import win32security

    from core.export_execution_host import inspect_bot_token

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    times = kernel.GetProcessTimes
    times.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
    times.restype = wintypes.BOOL
    values = [wintypes.FILETIME() for _ in range(4)]
    image = kernel.QueryFullProcessImageNameW
    image.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.LPWSTR,
        ctypes.POINTER(wintypes.DWORD),
    ]
    image.restype = wintypes.BOOL
    get_pid = kernel.GetProcessId
    get_pid.argtypes = [wintypes.HANDLE]
    get_pid.restype = wintypes.DWORD
    size, buffer = wintypes.DWORD(32768), ctypes.create_unicode_buffer(32768)
    if not times(int(process), *(ctypes.byref(v) for v in values)) or not image(
        int(process), 0, buffer, ctypes.byref(size)
    ):
        raise ValueError("Process incarnation observation unavailable.")
    token = win32security.OpenProcessToken(process, 8)
    try:
        sid = win32security.ConvertSidToStringSid(
            win32security.GetTokenInformation(token, win32security.TokenUser)[0]
        )
        profile = inspect_bot_token(token, sid, observe_only=True)
    finally:
        token.Close()
    result = dict(
        pid=get_pid(int(process)),
        created_filetime=(values[0].dwHighDateTime << 32) | values[0].dwLowDateTime,
        executable=buffer.value,
        sha256=hashlib.sha256(Path(buffer.value).read_bytes()).hexdigest(),
        token_profile=profile,
    )
    if win32event.WaitForSingleObject(process, 0) != 258:
        raise ValueError("Pinned application process exited.")
    return result


def verify_process_snapshot(observed, expected):
    # Case-insensitive Windows path identity; every other field is exact.
    if not isinstance(observed, dict) or set(observed) != set(expected):
        raise ValueError("Incomplete application process observation.")
    if PureWindowsPath(observed["executable"]) != PureWindowsPath(expected["executable"]) or {
        k: v for k, v in observed.items() if k != "executable"
    } != {k: v for k, v in expected.items() if k != "executable"}:
        raise ValueError("Application process incarnation differs from approved binding.")


def open_pinned_process(pid, expected):
    import win32api

    validate_process_descriptor(expected, expected["token_profile"]["user_sid"])
    if pid != expected["pid"]:
        raise ValueError("Unexpected application peer PID.")
    process = win32api.OpenProcess(0x1000 | 0x100000, False, pid)
    try:
        verify_process_snapshot(process_snapshot(process), expected)
        return process
    except BaseException:
        process.Close()
        raise


def authenticate_process_peer(pipe, expected, *, server):
    import ctypes
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    get_pid = getattr(
        kernel, "GetNamedPipeServerProcessId" if server else "GetNamedPipeClientProcessId"
    )
    get_pid.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.ULONG)]
    get_pid.restype = wintypes.BOOL
    pid = wintypes.ULONG()
    if not get_pid(int(pipe), ctypes.byref(pid)):
        raise ValueError("Application pipe peer identity unavailable.")
    return open_pinned_process(pid.value, expected)
