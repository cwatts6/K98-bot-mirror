"""A consumed shutdown must not mask the next issuer-supervised outcome."""

import ast
import logging
import os
from pathlib import Path
import sys
from unittest.mock import Mock

import pytest


def outcome_branch():
    # Execute the production branch without importing the executable watchdog,
    # which would acquire locks and launch a real Bot during test collection.
    source = ast.parse((Path(__file__).parents[1] / "run_bot.py").read_text(encoding="utf-8"))
    remove = next(
        node
        for node in source.body
        if isinstance(node, ast.FunctionDef) and node.name == "safe_remove"
    )
    branch = next(
        node
        for loop in ast.walk(source)
        if isinstance(loop, ast.While)
        for node in loop.body
        if isinstance(node, ast.If)
        and isinstance(node.test, ast.Name)
        and node.test.id == "manual_rebinding"
    )
    # Preserve valid syntax for the non-automatic branch's break statement.
    return compile(
        ast.fix_missing_locations(
            ast.Module(
                body=[remove, ast.While(test=ast.Constant(True), body=[branch], orelse=[])],
                type_ignores=[],
            )
        ),
        "run_bot.py",
        "exec",
    )


@pytest.mark.parametrize(
    "next_code,flag_present,expected", [(1, False, 1), (15, True, 15), (15, False, 1)]
)
def test_shutdown_marker_does_not_mask_next_crash_or_restart(
    tmp_path, monkeypatch, next_code, flag_present, expected
):
    marker = tmp_path / ".shutdown_marker"
    restart = tmp_path / ".restart_flag"
    marker.write_text("parent signal", encoding="utf-8")
    monkeypatch.setenv("K98_EXPORT_AUTOMATIC_ISSUER", "protected-issuer.json")
    log_restart = Mock()
    record_restart = Mock()
    namespace = dict(
        os=os,
        sys=sys,
        log=logging.getLogger("watchdog-test"),
        manual_rebinding=True,
        SHUTDOWN_MARKER_FILE=str(marker),
        RESTART_FLAG_PATH=str(restart),
        RESTART_EXIT_CODE=15,
        exit_code=1,
        log_restart=log_restart,
        wait_for_restart_flag=lambda: restart.exists(),
        read_restart_flag_metadata=lambda: ("timestamp", "operator", "requested"),
        write_last_restart_info=record_restart,
    )
    code = outcome_branch()
    with pytest.raises(SystemExit) as stopped:
        exec(code, namespace)
    assert stopped.value.code == 0
    assert not marker.exists()
    log_restart.assert_called_once_with("scheduled", "graceful")

    log_restart.reset_mock()
    namespace["exit_code"] = next_code
    if flag_present:
        restart.write_text("requested", encoding="utf-8")
    with pytest.raises(SystemExit) as restarted:
        exec(code, namespace)
    assert restarted.value.code == expected
    assert not marker.exists()
    assert ("scheduled", "graceful") not in [call.args for call in log_restart.call_args_list]
    if flag_present:
        assert not restart.exists()
        record_restart.assert_called_once_with("timestamp", "operator", "requested")
        log_restart.assert_called_once_with("manual", "success")
    else:
        record_restart.assert_not_called()
