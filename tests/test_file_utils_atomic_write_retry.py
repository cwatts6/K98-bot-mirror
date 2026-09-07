from __future__ import annotations

import os
from pathlib import Path

import pytest

import file_utils as fu


def test_atomic_write_json_retries_winerror32(monkeypatch, tmp_path: Path):
    target = tmp_path / "dm_scheduled_tracker.json"

    real_replace = os.replace
    calls = {"n": 0}

    class _FakePerm(PermissionError):
        def __init__(self):
            super().__init__(
                13, "The process cannot access the file because it is being used by another process"
            )
            self.winerror = 32

    def flaky_replace(src, dst):
        calls["n"] += 1
        if calls["n"] < 3:
            raise _FakePerm()
        return real_replace(src, dst)

    monkeypatch.setattr(fu.os, "replace", flaky_replace)
    monkeypatch.setattr(fu.time, "sleep", lambda _s: None)  # speed up test

    fu.atomic_write_json(target, {"ok": True}, replace_retries=5)

    assert target.exists()
    assert calls["n"] == 3


def test_atomic_write_json_raises_after_retry_exhaustion(monkeypatch, tmp_path: Path):
    target = tmp_path / "dm_sent_tracker.json"

    class _FakePerm(PermissionError):
        def __init__(self):
            super().__init__(
                13, "The process cannot access the file because it is being used by another process"
            )
            self.winerror = 32

    monkeypatch.setattr(
        fu.os, "replace", lambda *_args, **_kwargs: (_ for _ in ()).throw(_FakePerm())
    )
    monkeypatch.setattr(fu.time, "sleep", lambda _s: None)

    with pytest.raises(PermissionError):
        fu.atomic_write_json(target, {"ok": False}, replace_retries=3)
