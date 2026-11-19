"""Bounded, read-only startup history for the separately sealed verifier.

Logs are evidence, never authority to restart or repeat work. The private profile
pins the original generation by content, not by its mutable rotation suffix.
"""

import argparse
import base64
from contextlib import ExitStack
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import stat
import sys

READ_LIMIT = 8 * 1024 * 1024
NAMES = ("log.txt", *(f"log.txt.{i}" for i in range(1, 6)))


def validate_anchor(anchor):
    if (
        not isinstance(anchor, dict)
        or set(anchor) != {"sha256", "bytes", "offset"}
        or not isinstance(anchor["sha256"], str)
        or not re.fullmatch(r"[a-f0-9]{64}", anchor["sha256"])
        or type(anchor["bytes"]) is not int
        or not 0 < anchor["bytes"] <= READ_LIMIT
        or type(anchor["offset"]) is not int
        or not 0 <= anchor["offset"] < anchor["bytes"]
    ):
        raise ValueError("Exact reviewed startup-log anchor required")


def file_identity(info):
    if (
        not stat.S_ISREG(info.st_mode)
        or info.st_nlink != 1
        or not info.st_ino
        or getattr(info, "st_file_attributes", 0) & 0x400
    ):
        raise ValueError("Startup log type, link or identity differs")
    return info.st_dev, info.st_ino


def open_log(path):
    """Allow the logger to write and rotate; reject reparse objects themselves."""
    if os.name != "nt":
        return os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), "rb", buffering=0)
    import ctypes
    from ctypes import wintypes
    import msvcrt

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    create = kernel.CreateFileW
    create.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    create.restype = wintypes.HANDLE
    close = kernel.CloseHandle
    close.argtypes = [wintypes.HANDLE]
    close.restype = wintypes.BOOL
    # GENERIC_READ, SHARE_READ|WRITE|DELETE, OPEN_EXISTING, OPEN_REPARSE_POINT.
    handle = create(str(path), 0x80000000, 7, None, 3, 0x00200000, None)
    if handle == wintypes.HANDLE(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        fd = msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY)
    except BaseException:
        close(handle)
        raise
    try:
        return os.fdopen(fd, "rb", buffering=0)
    except BaseException:
        os.close(fd)
        raise


def capture(log_root, anchor):
    """Capture the pinned generation and every newer one, with no retry.

    An active-file append may follow the captured boundary. Its captured prefix
    is read again to reject rewriting. Archived files must remain unchanged.
    Path identity checks reject rotation during capture; all handles share DELETE.
    Every byte read, including the prefix comparison, consumes the same budget.
    """
    validate_anchor(anchor)
    root = Path(log_root)
    root_before = root.stat(follow_symlinks=False)
    if (
        not stat.S_ISDIR(root_before.st_mode)
        or getattr(root_before, "st_file_attributes", 0) & 0x400
    ):
        raise ValueError("Startup log directory differs")
    budget = READ_LIMIT
    generations = []

    def read_exact(stream, length):
        nonlocal budget
        if length < 0 or length > budget:
            raise ValueError("Startup history exceeds capture read budget")
        budget -= length
        value = stream.read(length)
        if len(value) != length:
            raise ValueError("Startup history truncated during capture")
        return value

    with ExitStack() as stack:
        for index, name in enumerate(NAMES):
            path = root / name
            before = path.stat(follow_symlinks=False)
            identity = file_identity(before)
            stream = stack.enter_context(open_log(path))
            opened = os.fstat(stream.fileno())
            if file_identity(opened) != identity or opened.st_size != before.st_size:
                raise ValueError("Startup log identity changed before capture")
            raw = read_exact(stream, opened.st_size)
            if raw and not raw.endswith(b"\n"):
                raise ValueError("Startup history contains an incomplete record")
            digest = hashlib.sha256(raw).hexdigest()
            generations.append((name, path, stream, opened, raw, digest))
            if digest == anchor["sha256"]:
                if len(raw) != anchor["bytes"]:
                    raise ValueError("Startup anchor length differs")
                break
        else:
            raise ValueError("Reviewed startup generation is unavailable")

        # Keep a stable current prefix while permitting ordinary appends.
        current = generations[0]
        current[2].seek(0)
        if read_exact(current[2], len(current[4])) != current[4]:
            raise ValueError("Active startup log prefix changed")
        for index, (name, path, stream, opened, raw, digest) in enumerate(generations):
            after = os.fstat(stream.fileno())
            named = path.stat(follow_symlinks=False)
            if file_identity(after) != file_identity(opened) or file_identity(
                named
            ) != file_identity(opened):
                raise ValueError("Startup log rotated during capture")
            if index == 0:
                if after.st_size < len(raw) or named.st_size < len(raw):
                    raise ValueError("Active startup log was truncated")
            elif (after.st_size, after.st_mtime_ns) != (opened.st_size, opened.st_mtime_ns) or (
                named.st_size,
                named.st_mtime_ns,
            ) != (opened.st_size, opened.st_mtime_ns):
                raise ValueError("Archived startup generation changed")
        root_after = root.stat(follow_symlinks=False)
        if (root_before.st_dev, root_before.st_ino) != (root_after.st_dev, root_after.st_ino):
            raise ValueError("Startup log directory changed")
        ordered = list(reversed(generations))
        raw = ordered[0][4][anchor["offset"] :] + b"".join(item[4] for item in ordered[1:])
        raw.decode("utf-8")
        evidence = dict(
            version=1,
            observed_utc=datetime.now(UTC).isoformat(),
            anchor=dict(anchor),
            bytes_read=READ_LIMIT - budget,
            interval_bytes=len(raw),
            interval_sha256=hashlib.sha256(raw).hexdigest(),
            generations=[
                dict(
                    name=item[0],
                    bytes=len(item[4]),
                    sha256=item[5],
                    identity=[str(n) for n in file_identity(item[3])],
                )
                for item in ordered
            ],
        )
        return dict(raw=raw, evidence=evidence)


def require_startup_ready(raw):
    text = raw.decode("utf-8")
    if (
        "[BOOT] full_startup_sequence completed successfully" not in text
        or "Logged in as" not in text
        or "S11 export admission remains closed" in text
        or "Export admission disabled:" in text
        or any(
            "Export coordinator unavailable" in line
            and not re.search(r"error_type=ObservationBusy(?:\s|$)", line)
            for line in text.splitlines()
        )
    ):
        raise ValueError("Startup history does not establish readiness")


def observe(config, start, profile):
    anchor = profile["startup_log_anchor"]
    validate_anchor(anchor)
    if start["release_id"] != profile["release_id"] or start["log_offset"] != anchor["offset"]:
        raise ValueError("Startup log anchor differs from original request")
    result = capture(Path(config["root"]) / "logs", anchor)
    require_startup_ready(result["raw"])
    return result


def pinned_bytes(path, digest, limit):
    with Path(path).open("rb") as stream:
        raw = stream.read(limit + 1)
    if not 0 < len(raw) <= limit or hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError("Pinned startup evidence input differs")
    return raw


def capture_profile(profile, directory):
    """Use the same exact admission parser at the PowerShell final boundary."""
    stage = Path(profile["stage"])
    config = json.loads(
        pinned_bytes(stage / "ReleaseBindings.json", profile["bindings_sha256"], 1024 * 1024)
    )
    if (
        config["root"] != r"C:\discord_file_downloader"
        or config["release_id"] != profile["release_id"]
    ):
        raise ValueError("Exact installed release required for startup evidence")
    start = json.loads(pinned_bytes(stage / "start-requested.json", profile["start_sha256"], 65536))
    journal = json.loads(
        pinned_bytes(
            Path(config["new_state_directory"]) / profile["journal_name"],
            profile["journal_sha256"],
            65536,
        )
    )
    pair_path = Path(directory) / "Verify-NewPair.py"
    pinned_bytes(pair_path, profile["pair_sha256"], 1024 * 1024)
    pair = runpy.run_path(str(pair_path))
    result = observe(config, start, profile)
    result["evidence"]["admission"] = pair["startup_admission_result"](
        config, journal, start, raw=result["raw"]
    )
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args()
    if not sys.flags.isolated or os.name != "nt":
        raise ValueError("Isolated Windows interpreter required")
    with Path(args.profile).open("rb") as stream:
        raw = stream.read(65537)
    if not 0 < len(raw) <= 65536 or hashlib.sha256(raw).hexdigest() != args.sha256:
        raise ValueError("Startup observation profile differs")
    profile = json.loads(raw)
    if profile["version"] != 2 or profile["host"] != "MINI_AMD":
        raise ValueError("Reviewed rotation-aware profile required")
    # Full custody/native/source checks remain the caller's responsibility.
    result = capture_profile(profile, Path(args.profile).parent)
    print(
        json.dumps(
            dict(
                stage="STARTUP_HISTORY_CAPTURED",
                evidence=result["evidence"],
                raw_base64=base64.b64encode(result["raw"]).decode(),
            )
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(
            json.dumps(
                dict(
                    stage="STARTUP_HISTORY_REFUSED", failure_type=type(error).__name__, retry=False
                )
            )
        )
        raise SystemExit(1) from None
