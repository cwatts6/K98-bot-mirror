#!/usr/bin/env python3
"""Static slash-command registration audit helper.

Usage:
  python scripts/validate_command_registration.py
"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MODULES = [
    ("Commands.py (authoritative)", ROOT / "Commands.py"),
    ("cogs/commands.py (secondary)", ROOT / "cogs" / "commands.py"),
    ("subscribe.py (secondary)", ROOT / "subscribe.py"),
]


def collect_names(path: Path) -> set[str]:
    names: set[str] = set()
    source = path.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(path))

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for deco in node.decorator_list:
            if not isinstance(deco, ast.Call) or not isinstance(deco.func, ast.Attribute):
                continue
            attr = deco.func.attr
            is_slash = attr == "slash_command"
            is_app = (
                attr == "command"
                and isinstance(deco.func.value, ast.Name)
                and deco.func.value.id == "app_commands"
            )
            if not (is_slash or is_app):
                continue
            for kw in deco.keywords:
                if kw.arg == "name" and isinstance(kw.value, ast.Constant) and kw.value.value:
                    names.add(str(kw.value.value))
                    break
    return names


def main() -> int:
    paths = {label: collect_names(path) for label, path in MODULES}
    owners: dict[str, list[str]] = {}
    for label, names in paths.items():
        for name in names:
            owners.setdefault(name, []).append(label)
    duplicates = {k: sorted(v) for k, v in owners.items() if len(v) > 1}

    total_unique = len(set().union(*paths.values()))
    print(
        f"registration summary: primary={len(paths['Commands.py (authoritative)'])} "
        f"secondary_cogs={len(paths['cogs/commands.py (secondary)'])} "
        f"secondary_subscribe={len(paths['subscribe.py (secondary)'])} "
        f"total_unique={total_unique}"
    )

    if not duplicates:
        print("no duplicates detected")
        return 0

    print("duplicates detected:")
    for name in sorted(duplicates):
        print(f"  /{name}: {', '.join(duplicates[name])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
