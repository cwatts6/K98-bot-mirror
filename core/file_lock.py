"""Owned local-file locks. No age/PID recovery and no path-only deletion.

Windows deletes the created object through its exclusive native handle. POSIX
keeps a stable rendezvous inode: cooperating writers must never unlink it. Only
our exact released marker is reusable; a crash-held/foreign file stays blocked.
Local filesystems and trusted parent directories are required, not network locks.
"""

from contextlib import contextmanager
import logging
import math
import os
from pathlib import Path
import stat
import threading
import time

logger = logging.getLogger(__name__)
_FREE = b"K98:file-lock:v1:released\n"
_HELD = b"K98:file-lock:v1:held\n"
_uncertain = {}
_active = set()
_custody = threading.Lock()


class LockCleanupError(RuntimeError):
    """The body may have committed; cleanup failure never authorizes replay."""


class LockOwnershipError(RuntimeError):
    """The original rendezvous identity is unavailable or changed."""


class _Busy(Exception):
    def __init__(self, error=None):
        self.error = error


def _key(path):
    return os.path.normcase(os.path.realpath(path))


def _retain(key, owner, error):
    # Never retry an uncertain close: the numeric handle may already be reused.
    with _custody:
        _uncertain.setdefault(key, []).append((owner, error))


def _claim(key):
    with _custody:
        if key in _uncertain:
            raise LockCleanupError("File lock cleanup remains unconfirmed")
        if key in _active:
            return False
        _active.add(key)
        return True


def _release_claim(key):
    with _custody:
        _active.remove(key)


def _secondary(primary, cleanup):
    primary.add_note(f"File lock cleanup also failed: {type(cleanup).__name__}")
    try:
        logger.error("File lock cleanup unconfirmed; original failure preserved", exc_info=cleanup)
    except Exception:
        primary.add_note("File lock cleanup diagnostic also failed")


class _PosixOwner:
    def __init__(self, path):
        import fcntl

        self.path, self.fcntl = path, fcntl
        flags = os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC
        try:
            self.fd = os.open(path, flags | os.O_CREAT | os.O_EXCL, 0o600)
            self.created = True
        except FileExistsError:
            self.fd = os.open(path, flags)
            self.created = False
        self.locked = False

    def _identity(self):
        opened = os.fstat(self.fd)
        named = os.stat(self.path, follow_symlinks=False)
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_nlink != 1
            or (opened.st_dev, opened.st_ino) != (named.st_dev, named.st_ino)
        ):
            raise LockOwnershipError("File lock identity changed or is aliased")

    def attempt(self):
        try:
            self.fcntl.flock(self.fd, self.fcntl.LOCK_EX | self.fcntl.LOCK_NB)
        except BlockingIOError:
            return False
        self.locked = True
        self._identity()
        os.lseek(self.fd, 0, os.SEEK_SET)
        raw = os.read(self.fd, len(_FREE) + 1)
        if not self.created and raw != _FREE:
            self.fcntl.flock(self.fd, self.fcntl.LOCK_UN)
            self.locked = False
            return False
        return True

    def _write(self, data):
        os.lseek(self.fd, 0, os.SEEK_SET)
        if os.write(self.fd, data) != len(data):
            raise OSError("Incomplete file lock metadata write")
        os.ftruncate(self.fd, len(data))
        os.fsync(self.fd)

    def initialize(self):
        self._write(_HELD)

    def release(self):
        self._identity()
        self._write(_FREE)
        # flock remains owned until close physically completes. No unlink, no
        # second open and no check-then-unlink window on POSIX.
        self.close()

    def close(self):
        os.close(self.fd)
        self.fd = None


if os.name == "nt":
    import ctypes
    from ctypes import wintypes

    _kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    _create = _kernel.CreateFileW
    _create.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    _create.restype = wintypes.HANDLE
    _write = _kernel.WriteFile
    _write.argtypes = [
        wintypes.HANDLE,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        ctypes.c_void_p,
    ]
    _write.restype = wintypes.BOOL
    _dispose = _kernel.SetFileInformationByHandle
    _dispose.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    _dispose.restype = wintypes.BOOL
    _close = _kernel.CloseHandle
    _close.argtypes = [wintypes.HANDLE]
    _close.restype = wintypes.BOOL

    class _Disposition(ctypes.Structure):
        _fields_ = [("DeleteFile", wintypes.BOOL)]


class _WindowsOwner:
    def __init__(self, path):
        # CREATE_NEW, GENERIC_WRITE | DELETE; no share flags and no inheritance.
        # Do not set DELETE_ON_CLOSE at acquisition: a crashed writer's sentinel
        # must remain, rather than silently permitting recovery/replay.
        self.handle = _create(str(path), 0x40010000, 0, None, 1, 0x80, None)
        if self.handle == ctypes.c_void_p(-1).value:
            code = ctypes.get_last_error()
            if code in (32, 80, 183):
                raise _Busy
            if code == 5:
                # A delete-pending object returns ACCESS_DENIED until the last
                # kernel reference closes. Retry within the same admission
                # budget; a persistent ACL refusal retains its original error.
                raise _Busy(ctypes.WinError(code))
            raise ctypes.WinError(code)

    def attempt(self):
        return True

    def initialize(self):
        raw = f"{os.getpid()}\n".encode("ascii")
        written = wintypes.DWORD()
        if not _write(self.handle, raw, len(raw), ctypes.byref(written), None):
            raise ctypes.WinError(ctypes.get_last_error())
        if written.value != len(raw):
            raise OSError("Incomplete file lock metadata write")

    def release(self):
        disposition = _Disposition(True)
        if not _dispose(self.handle, 4, ctypes.byref(disposition), ctypes.sizeof(disposition)):
            raise ctypes.WinError(ctypes.get_last_error())
        self.close()

    def close(self):
        if not _close(self.handle):
            raise ctypes.WinError(ctypes.get_last_error())
        self.handle = None


def _cleanup(key, owner, *, release, primary=None):
    try:
        if release:
            owner.release()
        else:
            owner.close()
    except BaseException as error:
        _retain(key, owner, error)
        if primary is not None:
            _secondary(primary, error)
        else:
            if not isinstance(error, Exception):
                raise
            raise LockCleanupError(
                "File lock cleanup unconfirmed; protected work must not be replayed"
            ) from error
    else:
        # A physically closed handle can precede a failed acknowledgement.
        # Keep local admission owned until cleanup is positively confirmed;
        # never release this claim when retaining an uncertain owner.
        _release_claim(key)


@contextmanager
def acquire_lock(path, timeout=5.0, poll=0.1):
    """Execute the body once, releasing only the physical object we own."""
    path = Path(path).absolute()
    timeout, poll = float(timeout), float(poll)
    if not math.isfinite(timeout) or not math.isfinite(poll) or timeout < 0 or poll <= 0:
        raise ValueError("File lock timeout must be finite/nonnegative and poll positive")
    key = _key(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + timeout
    owner = None
    acquired = False
    claimed = False
    try:
        while True:
            admission_error = None
            try:
                if not claimed:
                    claimed = _claim(key)
                if claimed:
                    if owner is None:
                        owner = _WindowsOwner(path) if os.name == "nt" else _PosixOwner(path)
                    acquired = owner.attempt()
            except _Busy as busy:
                acquired = False
                admission_error = busy.error
            if acquired:
                break
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                if admission_error is not None:
                    raise admission_error
                raise TimeoutError(f"Timed out acquiring lock {path!s}")
            time.sleep(min(poll, remaining))
        owner.initialize()
    except BaseException as primary:
        if owner is not None:
            _cleanup(key, owner, release=acquired, primary=primary)
        elif claimed:
            _release_claim(key)
        raise

    try:
        yield Path(path)
    except BaseException as primary:
        _cleanup(key, owner, release=True, primary=primary)
        raise
    else:
        _cleanup(key, owner, release=True)
