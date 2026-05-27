#!/usr/bin/env python3
"""Validate K98 architecture boundaries for changed Python files."""

from __future__ import annotations

import argparse
from collections.abc import Iterable
from dataclasses import dataclass
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ALLOW_MARKER = "architecture-check: allow"
SQL_PATTERN = re.compile(
    r"\b(SELECT|INSERT|UPDATE|DELETE|MERGE|CREATE|ALTER|DROP|TRUNCATE)\b",
    re.IGNORECASE,
)
DAL_IMPORT_PATTERN = re.compile(
    r"^\s*(?:from|import)\s+.*(?:\bdal\b|_dal\b|\brepositor(?:y|ies)\b)",
    re.IGNORECASE,
)
DISCORD_TYPE_PATTERN = re.compile(
    r"(?:^\s*(?:import|from)\s+discord\b|\bdiscord\.(?:Interaction|ApplicationContext|Context)\b|\bdiscord\.)"
)
ROOT_LEVEL_TARGETS = {".py", ".ps1", ".md", ".toml", ".yaml", ".yml", ".json"}


@dataclass(frozen=True)
class Finding:
    severity: str
    path: str
    line: int
    message: str

    def format(self) -> str:
        location = f"{self.path}:{self.line}" if self.line else self.path
        return f"{self.severity}: {location}: {self.message}"


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


def _resolve_diff_base(root: Path) -> str:
    in_ci = os.environ.get("GITHUB_ACTIONS") == "true"
    candidates: list[str] = []
    github_base = os.environ.get("GITHUB_BASE_REF")
    if github_base:
        candidates.append(f"origin/{github_base}")
    candidates.extend(["origin/main", "main"])
    for ref in candidates:
        result = _run_git(["merge-base", "HEAD", ref], root)
        if result:
            return result[0]
    if in_ci:
        raise SystemExit(
            "ERROR: Could not resolve a diff base ref in CI. Tried: " + ", ".join(candidates)
        )
    return "HEAD"


def _changed_files(root: Path) -> list[Path]:
    diff_base = _resolve_diff_base(root)
    changed = _run_git(["diff", "--name-only", f"{diff_base}...HEAD"], root)
    changed.extend(_run_git(["diff", "--name-only"], root))
    changed.extend(_run_git(["diff", "--name-only", "--cached"], root))
    changed.extend(_run_git(["ls-files", "--others", "--exclude-standard"], root))
    paths = []
    for item in dict.fromkeys(changed):
        path = root / item
        if path.exists() and path.is_file():
            paths.append(path)
    return paths


def iter_python_files(root: Path, paths: Iterable[Path] | None, all_files: bool) -> list[Path]:
    candidates = list(root.rglob("*.py")) if all_files else list(paths or _changed_files(root))
    excluded = {".git", ".venv", "venv", "env", "__pycache__", ".pytest_cache", ".ruff_cache"}
    files: list[Path] = []
    for path in candidates:
        try:
            rel = path.resolve().relative_to(root.resolve())
        except ValueError:
            continue
        if any(part in excluded for part in rel.parts):
            continue
        if path.suffix == ".py":
            files.append(path)
    return sorted(set(files))


def _relative_path(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _has_override(lines: list[str], index: int) -> bool:
    if ALLOW_MARKER in lines[index]:
        return True
    return index > 0 and ALLOW_MARKER in lines[index - 1]


def validate_files(root: Path, files: Iterable[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for path in files:
        rel = _relative_path(root, path)
        text = path.read_text(encoding="utf-8-sig", errors="ignore")
        lines = text.splitlines()

        if rel.startswith("commands/"):
            for index, line in enumerate(lines):
                if SQL_PATTERN.search(line) and not _has_override(lines, index):
                    findings.append(
                        Finding("FAIL", rel, index + 1, "SQL keyword found in command layer")
                    )

        if rel.startswith("ui/views/"):
            for index, line in enumerate(lines):
                if DAL_IMPORT_PATTERN.search(line) and not _has_override(lines, index):
                    findings.append(
                        Finding("FAIL", rel, index + 1, "DAL/repository import found in view layer")
                    )

        if not rel.startswith(("commands/", "ui/views/")):
            service_like = (
                rel.startswith("services/")
                or rel.endswith("_service.py")
                or "/service" in rel
                or "_service" in Path(rel).stem
            )
            if service_like:
                for index, line in enumerate(lines):
                    if DISCORD_TYPE_PATTERN.search(line) and not _has_override(lines, index):
                        findings.append(
                            Finding(
                                "FAIL",
                                rel,
                                index + 1,
                                "Discord type/reference found in service layer",
                            )
                        )
    return findings


def root_level_warnings(root: Path, paths: Iterable[Path]) -> list[Finding]:
    warnings: list[Finding] = []
    tracked = set(_run_git(["ls-files"], root))
    for path in paths:
        rel = _relative_path(root, path)
        rel_path = Path(rel)
        if len(rel_path.parts) == 1 and path.suffix in ROOT_LEVEL_TARGETS and rel not in tracked:
            warnings.append(Finding("WARN", rel, 0, "new root-level file detected"))
    return warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, help="Optional paths to validate.")
    parser.add_argument("--all", action="store_true", help="Validate every Python file.")
    args = parser.parse_args(argv)

    explicit_paths = [p if p.is_absolute() else ROOT / p for p in args.paths]
    files = iter_python_files(ROOT, explicit_paths or None, args.all)
    findings = validate_files(ROOT, files)
    warnings = root_level_warnings(ROOT, explicit_paths or _changed_files(ROOT))

    for finding in [*warnings, *findings]:
        print(finding.format())

    if findings:
        print(f"architecture validation failed: {len(findings)} blocking issue(s)")
        return 1
    print(f"architecture validation passed: {len(files)} Python file(s) checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
