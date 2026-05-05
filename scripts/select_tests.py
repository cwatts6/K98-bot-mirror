#!/usr/bin/env python3
"""Recommend focused tests for changed K98 files."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ALWAYS_RUN = [
    "python scripts/smoke_imports.py",
    "python scripts/validate_command_registration.py",
]
RULES = [
    (
        "commands/stats",
        ["python -m pytest -q tests/test_stats_service.py tests/test_mykvkstats.py"],
    ),
    ("stats", ["python -m pytest -q tests/test_stats_service.py tests/test_mykvkstats.py"]),
    ("ark/", ["python -m pytest -q tests/test_ark_*.py"]),
    ("mge/", ["python -m pytest -q tests/test_mge_*.py"]),
    ("event_calendar/", ["python -m pytest -q tests/test_calendar_*.py"]),
    ("ui/views/", ["python -m pytest -q tests/test_ui_imports.py"]),
    ("registry/", ["python -m pytest -q tests/test_registry_*.py"]),
    ("inventory/", ["python -m pytest -q tests/test_inventory_*.py"]),
]


def _run_git(args: list[str], root: Path) -> list[str]:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return []
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def changed_files(root: Path) -> list[str]:
    base_ref = _run_git(["merge-base", "HEAD", "origin/main"], root)
    diff_base = base_ref[0] if base_ref else "HEAD"
    changed = _run_git(["diff", "--name-only", f"{diff_base}...HEAD"], root)
    changed.extend(_run_git(["diff", "--name-only"], root))
    changed.extend(_run_git(["diff", "--name-only", "--cached"], root))
    changed.extend(_run_git(["ls-files", "--others", "--exclude-standard"], root))
    return list(dict.fromkeys(changed))


def select_tests(paths: list[str]) -> list[str]:
    commands: list[str] = []
    normalized = [path.replace("\\", "/") for path in paths]
    for prefix, tests in RULES:
        if any(path.startswith(prefix) for path in normalized):
            commands.extend(tests)
    if any(path.startswith("tests/") for path in normalized):
        commands.append("python -m pytest -q tests")
    commands.extend(ALWAYS_RUN)
    return list(dict.fromkeys(commands))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="Optional changed file paths.")
    args = parser.parse_args(argv)

    paths = args.paths or changed_files(ROOT)
    print("Changed files:")
    if paths:
        for path in paths:
            print(f"- {path}")
    else:
        print("- none detected")

    print("\nRecommended validation:")
    for command in select_tests(paths):
        print(f"- {command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
