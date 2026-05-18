#!/usr/bin/env python3
"""Static slash-command registration audit helper.

Usage:
  python scripts/validate_command_registration.py
"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PRIMARY_COMMAND_LIMIT = 100

SECONDARY_MODULES = [
    ("cogs/commands.py (secondary)", ROOT / "cogs" / "commands.py"),
    ("subscribe.py (secondary)", ROOT / "subscribe.py"),
]


def _literal_string(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value:
        return str(node.value)
    return None


def _call_name(call: ast.Call) -> str | None:
    func = call.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


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
                name = _literal_string(kw.value) if kw.arg == "name" else None
                if name:
                    names.add(name)
                    break
    return names


def collect_primary_names() -> set[str]:
    names: set[str] = set()
    for path in sorted((ROOT / "commands").glob("*.py")):
        if path.name == "__init__.py":
            continue
        source = path.read_text(encoding="utf-8-sig")
        tree = ast.parse(source, filename=str(path))

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for deco in node.decorator_list:
                    if not isinstance(deco, ast.Call) or not isinstance(deco.func, ast.Attribute):
                        continue
                    attr = deco.func.attr
                    owner = deco.func.value
                    is_bot_slash = (
                        attr == "slash_command"
                        and isinstance(owner, ast.Name)
                        and owner.id in {"bot", "bot_instance"}
                    )
                    is_app_command = (
                        attr == "command"
                        and isinstance(owner, ast.Name)
                        and owner.id == "app_commands"
                    )
                    if not (is_bot_slash or is_app_command):
                        continue
                    for kw in deco.keywords:
                        name = _literal_string(kw.value) if kw.arg == "name" else None
                        if name:
                            names.add(name)
                            break

            if isinstance(node, ast.Call) and _call_name(node) == "SlashCommandGroup":
                if node.args:
                    name = _literal_string(node.args[0])
                    if name:
                        names.add(name)
                        continue
                for kw in node.keywords:
                    name = _literal_string(kw.value) if kw.arg == "name" else None
                    if name:
                        names.add(name)
                        break

    return names


def main() -> int:
    paths = {"commands package (authoritative)": collect_primary_names()}
    paths.update({label: collect_names(path) for label, path in SECONDARY_MODULES})
    owners: dict[str, list[str]] = {}
    for label, names in paths.items():
        for name in names:
            owners.setdefault(name, []).append(label)
    duplicates = {k: sorted(v) for k, v in owners.items() if len(v) > 1}

    primary_count = len(paths["commands package (authoritative)"])
    total_unique = len(set().union(*paths.values()))
    print(
        f"registration summary: primary={primary_count} "
        f"secondary_cogs={len(paths['cogs/commands.py (secondary)'])} "
        f"secondary_subscribe={len(paths['subscribe.py (secondary)'])} "
        f"total_unique={total_unique}"
    )

    failed = False
    if primary_count > PRIMARY_COMMAND_LIMIT:
        print(
            f"primary command limit exceeded: {primary_count}/{PRIMARY_COMMAND_LIMIT} "
            "top-level application commands"
        )
        failed = True

    if not duplicates:
        print("no duplicates detected")
    else:
        print("duplicates detected:")
        for name in sorted(duplicates):
            print(f"  /{name}: {', '.join(duplicates[name])}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
