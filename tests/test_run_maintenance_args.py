import sys

from file_utils import build_maintenance_cmd


def test_build_maintenance_cmd_with_kwargs(tmp_path, monkeypatch):
    """
    Verify that build_maintenance_cmd flattens kwargs into flag-style args correctly
    and omits False/None values while including True flags without values.
    """
    # simulate worker location by ensuring maintenance_worker.py exists next to file_utils during test
    # The test only inspects the generated command list, not executing it.
    kwargs = {
        "server": "MINI_AMD",
        "database": "ROK_TRACKER",
        "username": "SHEETS_USER",
        "password": "secret!",
        "verbose": True,
        "noop": False,
        "noneval": None,
        "count": 5,
    }
    cmd = build_maintenance_cmd("post_stats", args=["positional"], kwargs=kwargs)
    # Basic structure
    assert (
        cmd[0].endswith(sys.executable.split(sys.exec_prefix)[-1])
        or cmd[0] == sys.executable
        or "python" in cmd[0].lower()
    )
    # command present
    assert "post_stats" in cmd
    # positional arg preserved
    assert "positional" in cmd
    # flattened flags present
    assert "--server" in cmd and "MINI_AMD" in cmd
    assert "--database" in cmd and "ROK_TRACKER" in cmd
    assert "--username" in cmd and "SHEETS_USER" in cmd
    assert "--password" in cmd and "secret!" in cmd
    # boolean True flag present without explicit value
    assert "--verbose" in cmd
    # False/None omitted
    assert "--noop" not in cmd
    assert "--noneval" not in cmd
    # numeric values become str
    assert "--count" in cmd and "5" in cmd
