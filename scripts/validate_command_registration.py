#!/usr/bin/env python3
"""Static slash-command registration audit helper.

Usage:
  python scripts/validate_command_registration.py
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_COMMAND_INVENTORY_SPEC = importlib.util.spec_from_file_location(
    "_command_inventory", ROOT / "commands" / "command_inventory.py"
)
if _COMMAND_INVENTORY_SPEC is None or _COMMAND_INVENTORY_SPEC.loader is None:
    raise RuntimeError("Could not load commands/command_inventory.py")
_COMMAND_INVENTORY = importlib.util.module_from_spec(_COMMAND_INVENTORY_SPEC)
sys.modules[_COMMAND_INVENTORY_SPEC.name] = _COMMAND_INVENTORY
_COMMAND_INVENTORY_SPEC.loader.exec_module(_COMMAND_INVENTORY)
collect_declared_command_names = _COMMAND_INVENTORY.collect_declared_command_names
collect_static_primary_inventory = _COMMAND_INVENTORY.collect_static_primary_inventory

PRIMARY_COMMAND_LIMIT = 100
PRIMARY_COMMAND_WARNING_THRESHOLD = 90


@dataclass(frozen=True)
class CommandSource:
    label: str
    path: Path


SECONDARY_MODULES = [
    CommandSource("cogs/commands.py (disabled legacy)", ROOT / "cogs" / "commands.py"),
    CommandSource("subscribe.py (disabled legacy)", ROOT / "subscribe.py"),
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
    return collect_declared_command_names(path)


def _collect_group_helper_commands(command_paths: list[Path]) -> dict[str, set[str]]:
    helpers: dict[str, set[str]] = {}

    for path in command_paths:
        source = path.read_text(encoding="utf-8-sig")
        tree = ast.parse(source, filename=str(path))

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or not node.args.args:
                continue
            group_arg_name = node.args.args[0].arg
            command_names: set[str] = set()

            for child in ast.walk(node):
                if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                for deco in child.decorator_list:
                    if not isinstance(deco, ast.Call) or not isinstance(deco.func, ast.Attribute):
                        continue
                    if deco.func.attr != "command":
                        continue
                    if not (
                        isinstance(deco.func.value, ast.Name)
                        and deco.func.value.id == group_arg_name
                    ):
                        continue
                    for kw in deco.keywords:
                        name = _literal_string(kw.value) if kw.arg == "name" else None
                        if name:
                            command_names.add(name)
                            break

            if command_names:
                helpers[node.name] = command_names

    return helpers


def _active_command_paths(command_paths: list[Path]) -> list[Path]:
    init_path = ROOT / "commands" / "__init__.py"
    if not init_path.exists():
        return command_paths

    source = init_path.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(init_path))
    imported_registers: dict[str, str] = {}
    active_registers: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            module_name = node.module.lstrip(".")
            for alias in node.names:
                imported_registers[alias.asname or alias.name] = module_name
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            active_registers.add(node.func.id)

    active_paths = []
    for register_name in active_registers:
        module_name = imported_registers.get(register_name)
        if not module_name:
            continue
        path = ROOT / "commands" / f"{module_name}.py"
        if path.exists():
            active_paths.append(path)

    return sorted(set(active_paths)) or command_paths


def _relative_label(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _collect_primary_inventory_details() -> (
    tuple[set[str], dict[str, set[str]], dict[str, list[str]]]
):
    inventory = collect_static_primary_inventory(ROOT)
    return inventory.names, inventory.grouped, inventory.name_sources


def collect_primary_inventory() -> tuple[set[str], dict[str, set[str]]]:
    names, grouped, _name_sources = _collect_primary_inventory_details()
    return names, grouped


def collect_primary_names() -> set[str]:
    names, _grouped = collect_primary_inventory()
    return names


def main() -> int:
    primary_names, grouped, primary_name_sources = _collect_primary_inventory_details()
    grouped_subcommand_detected_count = sum(len(commands) for commands in grouped.values())
    paths = {"commands package (authoritative)": primary_names}
    paths.update({source.label: collect_names(source.path) for source in SECONDARY_MODULES})
    owners: dict[str, list[str]] = {}
    for label, names in paths.items():
        for name in names:
            owners.setdefault(name, []).append(label)
    active_duplicates = {
        name: sorted(labels) for name, labels in primary_name_sources.items() if len(labels) > 1
    }
    disabled_legacy_duplicates = {
        name: sorted(labels)
        for name, labels in owners.items()
        if len(labels) > 1 and name not in active_duplicates
    }

    primary_count = len(paths["commands package (authoritative)"])
    total_unique = len(set().union(*paths.values()))
    secondary_cogs_count = len(paths["cogs/commands.py (disabled legacy)"])
    secondary_subscribe_count = len(paths["subscribe.py (disabled legacy)"])
    disabled_legacy_count = secondary_cogs_count + secondary_subscribe_count
    print(
        f"registration summary: primary={primary_count} "
        f"grouped_subcommands_detected={grouped_subcommand_detected_count} "
        f"disabled_legacy={disabled_legacy_count} "
        f"secondary_cogs={secondary_cogs_count} "
        f"secondary_subscribe={secondary_subscribe_count} "
        f"total_unique={total_unique}"
    )
    print("active command surface: commands package (authoritative)")
    if disabled_legacy_count:
        print("disabled legacy command surfaces retained:")
        for source in SECONDARY_MODULES:
            print(f"  {source.label}: {len(paths[source.label])} command(s)")
    else:
        print("disabled legacy command surfaces: none retained")

    if grouped:
        print("grouped command summary (statically detected):")
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

    if not active_duplicates:
        print("no active duplicate risks detected")
    else:
        print("active duplicate risks detected:")
        for name in sorted(active_duplicates):
            print(f"  /{name}: {', '.join(active_duplicates[name])}")

    if disabled_legacy_duplicates:
        print("disabled legacy duplicates detected:")
        for name in sorted(disabled_legacy_duplicates):
            print(f"  /{name}: {', '.join(disabled_legacy_duplicates[name])}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
