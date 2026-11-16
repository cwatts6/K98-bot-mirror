"""Subprocess-isolated constants import validation.

These tests validate import-time env parsing/validation safely by spawning a fresh Python process
for each case so module-level constant initialization runs from a clean interpreter state.
"""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap

import pytest


def _run_constants_import_with_env(overrides: dict[str, str]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(overrides)

    code = textwrap.dedent("""
        import importlib
        import sys

        try:
            import constants  # noqa: F401
            print("IMPORT_OK")
            raise SystemExit(0)
        except Exception as e:
            print(f"IMPORT_ERR:{type(e).__name__}:{e}")
            raise SystemExit(7)
        """)
    return subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def test_constants_import_fails_for_non_positive_spike_multiplier_subprocess():
    proc = _run_constants_import_with_env({"EVENT_CALENDAR_ANOMALY_VOLUME_SPIKE_MULTIPLIER": "0"})
    assert proc.returncode == 7
    assert "IMPORT_ERR:RuntimeError:" in proc.stdout
    assert "EVENT_CALENDAR_ANOMALY_VOLUME_SPIKE_MULTIPLIER" in proc.stdout


def test_constants_import_fails_for_cancelled_ratio_out_of_range_subprocess():
    proc = _run_constants_import_with_env({"EVENT_CALENDAR_ANOMALY_CANCELLED_RATIO_WARN": "1.5"})
    assert proc.returncode == 7
    assert "IMPORT_ERR:RuntimeError:" in proc.stdout
    assert "EVENT_CALENDAR_ANOMALY_CANCELLED_RATIO_WARN" in proc.stdout


def test_constants_import_fails_for_negative_retries_subprocess():
    proc = _run_constants_import_with_env({"EVENT_CALENDAR_PIPELINE_SYNC_RETRIES": "-1"})
    assert proc.returncode == 7
    assert "IMPORT_ERR:RuntimeError:" in proc.stdout
    assert "EVENT_CALENDAR_PIPELINE_SYNC_RETRIES" in proc.stdout


def test_constants_import_fails_for_non_positive_timeout_subprocess():
    proc = _run_constants_import_with_env({"EVENT_CALENDAR_PIPELINE_GENERATE_TIMEOUT_SECONDS": "0"})
    assert proc.returncode == 7
    assert "IMPORT_ERR:RuntimeError:" in proc.stdout
    assert "EVENT_CALENDAR_PIPELINE_GENERATE_TIMEOUT_SECONDS" in proc.stdout


def test_constants_import_fails_for_backoff_cap_less_than_base_subprocess():
    proc = _run_constants_import_with_env(
        {
            "EVENT_CALENDAR_PIPELINE_BACKOFF_BASE_SECONDS": "5.0",
            "EVENT_CALENDAR_PIPELINE_BACKOFF_CAP_SECONDS": "1.0",
        }
    )
    assert proc.returncode == 7
    assert "IMPORT_ERR:RuntimeError:" in proc.stdout
    assert "EVENT_CALENDAR_PIPELINE_BACKOFF_CAP_SECONDS" in proc.stdout


@pytest.mark.parametrize(
    "name,value",
    [
        ("EVENT_CALENDAR_PIPELINE_SYNC_TIMEOUT_SECONDS", "abc"),
        ("EVENT_CALENDAR_PIPELINE_GENERATE_RETRIES", "nope"),
        ("EVENT_CALENDAR_PIPELINE_BACKOFF_BASE_SECONDS", "not-a-float"),
    ],
)
def test_constants_import_fails_for_bad_numeric_types_subprocess(name: str, value: str):
    proc = _run_constants_import_with_env({name: value})
    assert proc.returncode == 7
    assert "IMPORT_ERR:RuntimeError:" in proc.stdout
    assert name in proc.stdout


def test_constants_import_success_with_valid_overrides_subprocess():
    proc = _run_constants_import_with_env(
        {
            "EVENT_CALENDAR_ANOMALY_VOLUME_SPIKE_MULTIPLIER": "2.5",
            "EVENT_CALENDAR_ANOMALY_CANCELLED_RATIO_WARN": "0.75",
            "EVENT_CALENDAR_PIPELINE_SYNC_TIMEOUT_SECONDS": "30",
            "EVENT_CALENDAR_PIPELINE_GENERATE_TIMEOUT_SECONDS": "40",
            "EVENT_CALENDAR_PIPELINE_PUBLISH_TIMEOUT_SECONDS": "50",
            "EVENT_CALENDAR_PIPELINE_SYNC_RETRIES": "1",
            "EVENT_CALENDAR_PIPELINE_GENERATE_RETRIES": "2",
            "EVENT_CALENDAR_PIPELINE_PUBLISH_RETRIES": "3",
            "EVENT_CALENDAR_PIPELINE_BACKOFF_BASE_SECONDS": "1.0",
            "EVENT_CALENDAR_PIPELINE_BACKOFF_CAP_SECONDS": "4.0",
            "EVENT_CALENDAR_STALE_WARN_MINUTES": "60",
            "EVENT_CALENDAR_STALE_DEGRADED_MINUTES": "240",
        }
    )
    assert proc.returncode == 0
    assert "IMPORT_OK" in proc.stdout
