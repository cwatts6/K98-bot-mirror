"""
Run this script to validate CSV log migration logic for a variety of legacy inputs.

Usage:
    python -m stats_alerts.tests.test_guard_migration

It will:
- Create a temporary dir
- Write several test CSV files with legacy and current formats
- For each file, set the environment variable STATS_ALERT_LOG to point to it,
  import the guard module (reloadable), run ensure_log_exists and show results.
"""

import importlib
import os
from pathlib import Path
import sys
import tempfile
import textwrap

TEST_FILES = {
    "legacy_2col_no_header.csv": textwrap.dedent("""\
        2025-10-25,00:00:00
        2025-10-26,12:34:56
        """),
    "legacy_2col_with_blank_and_corrupt.csv": textwrap.dedent("""\
        2025-10-25,00:00:00

        badrow
        2025-10-27,03:03:03
        """),
    "headered_3col.csv": textwrap.dedent("""\
        date,time_utc,kind
        2025-10-26,01:01:01,offseason_daily
        2025-10-27,02:02:02,kvk
        """),
    "headerless_3col.csv": textwrap.dedent("""\
        2025-10-26,01:01:01,offseason_daily
        2025-10-27,02:02:02,kvk
        """),
}


def write_file(path: Path, content: str):
    path.write_text(content, encoding="utf-8")
    print(f"Wrote {path}:\n{content}\n---")


def show_file(path: Path):
    print(f"--- CONTENTS {path} ---")
    print(path.read_text(encoding="utf-8"))
    print("------")


def reload_guard_module():
    # ensure we import the package from repo root
    # in case stats_alerts package already loaded with previous STATS_ALERT_LOG
    if "stats_alerts.guard" in sys.modules:
        importlib.reload(sys.modules["stats_alerts.guard"])
    else:
        pass  # type: ignore
    return sys.modules["stats_alerts.guard"]


def run_test_on_file(file_path: Path):
    print(f"\n=== Testing file: {file_path.name} ===")
    # Set environment var so resolve_path picks it up like constants.STATS_ALERT_LOG would
    os.environ["STATS_ALERT_LOG"] = str(file_path)
    # Reload module to pick up new LOG_PATH constant if it was imported earlier
    guard = reload_guard_module()
    # Call ensure_log_exists and then show file
    try:
        guard.ensure_log_exists()
    except Exception as e:
        print("ensure_log_exists raised:", e)
    show_file(file_path)
    # Print iterator output
    print("iter_log_rows() ->")
    for r in guard.iter_log_rows():
        print(r)
    print(
        "read_counts_for('offseason_daily', '2025-10-26') ->",
        guard.read_counts_for("offseason_daily", "2025-10-26"),
    )


def main():
    tmpdir = Path(tempfile.mkdtemp(prefix="guard_test_"))
    print("Using tmpdir:", tmpdir)
    for fname, content in TEST_FILES.items():
        p = tmpdir / fname
        write_file(p, content)
    # run tests
    for fname in TEST_FILES.keys():
        p = tmpdir / fname
        run_test_on_file(p)


if __name__ == "__main__":
    main()
