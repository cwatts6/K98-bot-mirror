#!/usr/bin/env python3
"""Validate K98 Codex Security routing in active repository guidance.

The validator prevents routine task/PR instructions from silently selecting a
standard or deep codebase scan. Historical task packs under archive directories
are intentionally excluded.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
import re
import sys

EXCLUDED_PARTS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "archive",
    "archives",
    "generated",
}

TEXT_SUFFIXES = {".md", ".txt", ".yaml", ".yml", ".toml"}
STANDARD_PATTERN = re.compile(r"(?<![\w-])\$?codex-security:security-scan(?![\w-])", re.IGNORECASE)
DEEP_PATTERN = re.compile(r"(?<![\w-])\$?codex-security:deep-security-scan(?![\w-])", re.IGNORECASE)
GENERIC_PATTERN = re.compile(r"\bcodex\s+security\s+(?:review|scan)\b", re.IGNORECASE)
ALLOW_STANDARD = "codex-security-routing: allow-standard"
ALLOW_DEEP = "codex-security-routing: allow-deep"
ALLOW_GENERIC = "codex-security-routing: allow-generic"
LEGACY_BINARY_GATE = re.compile(r"codex\s+security\s*:\s*<\s*run\s*\|\s*skipped", re.IGNORECASE)


@dataclass(frozen=True)
class Finding:
    level: str
    path: Path
    line: int
    message: str


def is_excluded(path: Path) -> bool:
    return any(part.lower() in EXCLUDED_PARTS for part in path.parts)


def candidate_files(root: Path) -> Iterable[Path]:
    direct = [root / "AGENTS.md", root / "README-DEV.md", root / "SECURITY.md"]
    for path in direct:
        if path.is_file():
            yield path

    for rel in ("docs/reference", "docs/templates", "docs/task_packs"):
        base = root / rel
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if (
                path.is_file()
                and path.suffix.lower() in TEXT_SUFFIXES
                and not is_excluded(path.relative_to(root))
            ):
                yield path


def nearby_marker(lines: list[str], index: int, marker: str) -> bool:
    start = max(0, index - 3)
    return any(marker in lines[i].lower() for i in range(start, index + 1))


def scan_file(root: Path, path: Path) -> list[Finding]:
    findings: list[Finding] = []
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return findings

    lines = text.splitlines()
    rel = path.relative_to(root)

    for index, line in enumerate(lines):
        if STANDARD_PATTERN.search(line) and not nearby_marker(lines, index, ALLOW_STANDARD):
            findings.append(
                Finding(
                    "ERROR",
                    rel,
                    index + 1,
                    "standard codebase scan invocation lacks an explicit allow-standard marker and reason",
                )
            )
        if DEEP_PATTERN.search(line) and not nearby_marker(lines, index, ALLOW_DEEP):
            findings.append(
                Finding(
                    "ERROR",
                    rel,
                    index + 1,
                    "deep scan invocation lacks an explicit allow-deep marker and reason",
                )
            )

    rel_lower = rel.as_posix().lower()
    if LEGACY_BINARY_GATE.search(text):
        match = LEGACY_BINARY_GATE.search(text)
        line_no = text[: match.start()].count("\n") + 1 if match else 1
        findings.append(
            Finding(
                "ERROR",
                rel,
                line_no,
                "legacy run/skipped Codex Security gate is ambiguous; record decision, target, expected setup, and evidence",
            )
        )

    if rel_lower.startswith("docs/task_packs/") or rel_lower.startswith("docs/templates/"):
        if GENERIC_PATTERN.search(text):
            has_route = "security-diff-scan" in text or "k98-security-review-routing" in text
            has_skip = "documented skip" in text or "justify skipping" in text
            has_allow = ALLOW_GENERIC in text.lower()
            if not ((has_route and has_skip) or has_allow):
                match = GENERIC_PATTERN.search(text)
                line_no = text[: match.start()].count("\n") + 1 if match else 1
                findings.append(
                    Finding(
                        "ERROR",
                        rel,
                        line_no,
                        "ambiguous Codex Security wording must select security-diff-scan, define a precise skip, or carry an allow-generic marker",
                    )
                )

        if rel_lower.startswith("docs/templates/") and "pack template" in rel.name.lower():
            required_tokens = {
                "k98-security-review-routing": "name the routing skill",
                "security-diff-scan": "name the routine Changes workflow",
                "documented skip": "define the precise skip outcome",
                "changes review": "define the routine review outcome",
                "standard codebase audit": "define the explicit standard-audit outcome",
                "deep codebase audit": "define the explicit deep-audit outcome",
                "findings triage": "define captured-findings triage",
                "finding remediation": "define focused remediation",
                "target": "record the repository/Git or findings target",
                "evidence": "record retained evidence",
            }
            lower_text = text.lower()
            for token, purpose in required_tokens.items():
                if token not in lower_text:
                    findings.append(
                        Finding(
                            "ERROR",
                            rel,
                            1,
                            f"canonical pack template must {purpose}; missing `{token}`",
                        )
                    )
            if "deep off" not in lower_text and "deep: off" not in lower_text:
                findings.append(
                    Finding(
                        "ERROR",
                        rel,
                        1,
                        "canonical pack template must require Deep off for routine Changes reviews",
                    )
                )

    return findings


def check_core_contract(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    agents = root / "AGENTS.md"
    if not agents.is_file():
        findings.append(Finding("ERROR", Path("AGENTS.md"), 1, "repository AGENTS.md is missing"))
    else:
        text = agents.read_text(encoding="utf-8")
        required = {
            "k98-security-review-routing": "route decisions through the K98 routing skill",
            "security-diff-scan": "name the routine diff workflow",
            "deep-security-scan": "state the explicit-only deep workflow boundary",
            "SECURITY.md": "distinguish policy context from scan routing",
        }
        for token, purpose in required.items():
            if token not in text:
                findings.append(
                    Finding(
                        "ERROR",
                        Path("AGENTS.md"),
                        1,
                        f"missing `{token}`; AGENTS.md must {purpose}",
                    )
                )

    security = root / "SECURITY.md"
    if not security.is_file():
        findings.append(
            Finding(
                "WARNING",
                Path("SECURITY.md"),
                1,
                "SECURITY.md is not present; complete the supplied template before enabling policy-context checks",
            )
        )
    else:
        text = security.read_text(encoding="utf-8")
        if "<OWNER:" in text or "Template status:" in text:
            findings.append(
                Finding(
                    "ERROR",
                    Path("SECURITY.md"),
                    1,
                    "SECURITY.md still contains template placeholders",
                )
            )
        if (
            "does not select a scan type" not in text.lower()
            and "does not select or launch" not in text.lower()
        ):
            findings.append(
                Finding(
                    "WARNING",
                    Path("SECURITY.md"),
                    1,
                    "state explicitly that SECURITY.md is policy context and does not select a scan type",
                )
            )

    for rel in (
        Path("README-DEV.md"),
        Path("docs/reference/K98 Bot - Skills & Refactor Triggers.md"),
    ):
        path = root / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if "Codex Security" in text and "k98-security-review-routing" not in text:
            findings.append(
                Finding(
                    "ERROR",
                    rel,
                    1,
                    "core guidance mentions Codex Security without the K98 routing skill",
                )
            )
        if "Codex Security" in text and "security-diff-scan" not in text:
            findings.append(
                Finding(
                    "ERROR",
                    rel,
                    1,
                    "core guidance mentions Codex Security without naming the routine diff workflow",
                )
            )

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo", type=Path, default=Path.cwd(), help="repository root (default: current directory)"
    )
    args = parser.parse_args()

    root = args.repo.resolve()
    if not root.is_dir():
        print(f"ERROR: repository root does not exist: {root}", file=sys.stderr)
        return 2

    findings = check_core_contract(root)
    seen: set[Path] = set()
    for path in candidate_files(root):
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        findings.extend(scan_file(root, path))

    findings.sort(
        key=lambda item: (
            item.level != "ERROR",
            item.path.as_posix().lower(),
            item.line,
            item.message,
        )
    )
    for item in findings:
        print(f"{item.level}: {item.path}:{item.line}: {item.message}")

    errors = sum(item.level == "ERROR" for item in findings)
    warnings = sum(item.level == "WARNING" for item in findings)
    if errors:
        print(f"FAILED: {errors} error(s), {warnings} warning(s)")
        return 1

    print(f"PASSED: 0 errors, {warnings} warning(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
