#!/usr/bin/env python3
"""Validate structured Deferred Optimisation sections in changed Markdown files."""

from __future__ import annotations

import argparse
from collections.abc import Iterable
from dataclasses import dataclass
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
HEADER = "### Deferred Optimisation"
REQUIRED_FIELDS = [
    "Area",
    "Type",
    "Description",
    "Suggested Fix",
    "Impact",
    "Risk",
    "Dependencies",
]
VAGUE_PATTERNS = [
    re.compile(r"\bimprove later\b", re.IGNORECASE),
    re.compile(r"\bfuture work\b", re.IGNORECASE),
    re.compile(r"\btodo\b", re.IGNORECASE),
]


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    message: str

    def format(self) -> str:
        return f"FAIL: {self.path}:{self.line}: {self.message}"


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


def iter_markdown_files(
    root: Path, paths: Iterable[Path] | None, all_files: bool
) -> list[Path]:
    # When neither --all nor explicit paths are given, auto-detect changed files
    # and exclude the source-of-truth doc that defines the schema itself.
    auto_detect = not all_files and paths is None
    candidates = list(root.rglob("*.md")) if all_files else list(paths or _changed_files(root))
    excluded = {".git", ".venv", "venv", "env", "__pycache__"}
    files: list[Path] = []
    for path in candidates:
        try:
            rel = path.resolve().relative_to(root.resolve())
        except ValueError:
            continue
        if any(part in excluded for part in rel.parts):
            continue
        if path.suffix.lower() != ".md":
            continue
        if auto_detect and path.name == "Quality Automation + Review System.md":
            continue
        files.append(path)
    return sorted(set(files))


def _relative_path(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _line_is_deferred_field(line: str) -> bool:
    return any(line.startswith(f"- {field}:") for field in REQUIRED_FIELDS)


def validate_file(root: Path, path: Path) -> list[Finding]:
    rel = _relative_path(root, path)
    lines = path.read_text(encoding="utf-8-sig", errors="ignore").splitlines()
    findings: list[Finding] = []

    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("-") and _line_is_deferred_field(stripped):
            # Check only the value portion after the first ":" so that vague
            # phrases in field values are still caught.
            colon_pos = stripped.find(":")
            check_text = stripped[colon_pos + 1 :] if colon_pos != -1 else line
        else:
            check_text = line
        for pattern in VAGUE_PATTERNS:
            if pattern.search(check_text):
                findings.append(Finding(rel, index + 1, "vague deferred-work phrase found"))
                break

    for index, line in enumerate(lines):
        if line.strip() != HEADER:
            continue
        block = lines[index + 1 : index + 1 + len(REQUIRED_FIELDS)]
        for offset, field in enumerate(REQUIRED_FIELDS):
            expected = f"- {field}:"
            actual_line = block[offset].strip() if offset < len(block) else ""
            if not actual_line.startswith(expected):
                findings.append(
                    Finding(
                        rel,
                        index + 1 + offset + 1,
                        f"Deferred Optimisation missing field '{expected}'",
                    )
                )
    return findings


def validate_files(root: Path, files: Iterable[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for path in files:
        findings.extend(validate_file(root, path))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, help="Optional Markdown files to validate.")
    parser.add_argument("--all", action="store_true", help="Validate every Markdown file.")
    args = parser.parse_args(argv)

    explicit_paths = [p if p.is_absolute() else ROOT / p for p in args.paths]
    files = iter_markdown_files(ROOT, explicit_paths or None, args.all)
    findings = validate_files(ROOT, files)
    for finding in findings:
        print(finding.format())
    if findings:
        print(f"deferred optimisation validation failed: {len(findings)} issue(s)")
        return 1
    print(f"deferred optimisation validation passed: {len(files)} Markdown file(s) checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
