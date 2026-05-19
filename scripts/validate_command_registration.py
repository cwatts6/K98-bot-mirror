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
PRIMARY_COMMAND_WARNING_THRESHOLD = 90

SECONDARY_MODULES = [
    ("cogs/commands.py (secondary)", ROOT / "cogs" / "commands.py"),
    ("subscribe.py (secondary)", ROOT / "subscribe.py"),
]


def _literal_string(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value:
        return str(node.value)
    return None


def _node_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _node_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return None


def _call_name(call: ast.Call) -> str | None:
    return _node_name(call.func)


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


def collect_primary_inventory() -> tuple[set[str], dict[str, set[str]]]:
    names: set[str] = set()
    grouped: dict[str, set[str]] = {}
    for path in sorted((ROOT / "commands").glob("*.py")):
        if path.name == "__init__.py":
            continue
        source = path.read_text(encoding="utf-8-sig")
        tree = ast.parse(source, filename=str(path))
        group_vars: dict[str, str] = {}

        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Call):
                continue
            if not (_call_name(node.value) or "").endswith("SlashCommandGroup"):
                continue

            group_name = None
            if node.value.args:
                group_name = _literal_string(node.value.args[0])
            for kw in node.value.keywords:
                if kw.arg == "name":
                    group_name = _literal_string(kw.value) or group_name

            if not group_name:
                continue
            for target in node.targets:
                if isinstance(target, ast.Name):
                    group_vars[target.id] = group_name
            names.add(group_name)
            grouped.setdefault(group_name, set())

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
                        if attr == "command" and isinstance(owner, ast.Name):
                            group_name = group_vars.get(owner.id)
                            if group_name:
                                for kw in deco.keywords:
                                    name = _literal_string(kw.value) if kw.arg == "name" else None
                                    if name:
                                        grouped.setdefault(group_name, set()).add(name)
                                        break
                        continue
                    for kw in deco.keywords:
                        name = _literal_string(kw.value) if kw.arg == "name" else None
                        if name:
                            names.add(name)
                            break

    return names, grouped


def collect_primary_names() -> set[str]:
    names, _grouped = collect_primary_inventory()
    return names


def main() -> int:
    primary_names, grouped = collect_primary_inventory()
    grouped_subcommand_count = sum(len(commands) for commands in grouped.values())
    paths = {"commands package (authoritative)": primary_names}
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
        f"grouped_subcommands={grouped_subcommand_count} "
        f"secondary_cogs={len(paths['cogs/commands.py (secondary)'])} "
        f"secondary_subscribe={len(paths['subscribe.py (secondary)'])} "
        f"total_unique={total_unique}"
    )

    if grouped:
        print("grouped command summary:")
        for group_name in sorted(grouped):
            subcommands = grouped[group_name]
            print(f"  /{group_name}: {len(subcommands)} subcommand(s)")

    failed = False
    if primary_count > PRIMARY_COMMAND_LIMIT:
        print(
            f"primary command limit exceeded: {primary_count}/{PRIMARY_COMMAND_LIMIT} "
            "top-level application commands"
        )
        failed = True
    elif primary_count >= PRIMARY_COMMAND_WARNING_THRESHOLD:
        print(
            f"primary command limit warning: {primary_count}/{PRIMARY_COMMAND_LIMIT} "
            "top-level application commands"
        )

    if not duplicates:
        print("no duplicates detected")
    else:
        print("duplicates detected:")
        for name in sorted(duplicates):
            print(f"  /{name}: {', '.join(duplicates[name])}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
