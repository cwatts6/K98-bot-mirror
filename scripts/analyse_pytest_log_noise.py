from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
LOG_PATHS = (
    REPO_ROOT / "logs" / "error_log.txt",
    REPO_ROOT / "logs" / "log.txt",
    REPO_ROOT / "logs" / "crash.log",
    REPO_ROOT / "logs" / "telemetry_log.jsonl",
)


def _snapshot() -> dict[Path, tuple[bool, int, int]]:
    snap: dict[Path, tuple[bool, int, int]] = {}
    for path in LOG_PATHS:
        if path.exists():
            stat = path.stat()
            snap[path] = (True, stat.st_size, stat.st_mtime_ns)
        else:
            snap[path] = (False, 0, 0)
    return snap


def _changed(before: dict[Path, tuple[bool, int, int]]) -> list[str]:
    problems: list[str] = []
    after = _snapshot()
    for path, old in before.items():
        new = after[path]
        if old != new:
            problems.append(
                f"{path.relative_to(REPO_ROOT)} changed during pytest "
                f"(before exists={old[0]} size={old[1]} mtime={old[2]}; "
                f"after exists={new[0]} size={new[1]} mtime={new[2]})"
            )
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run pytest and fail if production operational log files are touched."
    )
    parser.add_argument(
        "--pytest-args",
        nargs=argparse.REMAINDER,
        default=["-q", "tests"],
        help="Arguments passed after 'python -m pytest'. Defaults to '-q tests'.",
    )
    args = parser.parse_args(argv)

    pytest_args = args.pytest_args or ["-q", "tests"]
    env = os.environ.copy()
    env["K98_TEST_MODE"] = "1"
    env["PYTEST_RUNNING"] = "1"

    before = _snapshot()
    result = subprocess.run(
        [sys.executable, "-m", "pytest", *pytest_args],
        cwd=REPO_ROOT,
        env=env,
        text=True,
    )
    if result.returncode != 0:
        return result.returncode

    problems = _changed(before)
    if problems:
        print("pytest wrote to production operational logs:", file=sys.stderr)
        for problem in problems:
            print(f"- {problem}", file=sys.stderr)
        return 1

    print("pytest log-noise validation passed: production operational logs unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
