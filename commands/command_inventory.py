from __future__ import annotations

import ast
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class StaticCommandInventory:
    names: set[str]
    grouped: dict[str, set[str]]
    name_sources: dict[str, list[str]]

    @property
    def grouped_subcommand_count(self) -> int:
        return sum(len(commands) for commands in self.grouped.values())


def flatten_application_commands(commands: Iterable[Any]) -> Iterator[tuple[str, Any]]:
    """Yield slash commands with grouped subcommands expanded for inventory checks."""
    for command in commands:
        subcommands = getattr(command, "subcommands", None) or []
        if not subcommands:
            yield command.name, command
            continue

        for subcommand in subcommands:
            nested = getattr(subcommand, "subcommands", None) or []
            if nested:
                for nested_command in nested:
                    yield f"{command.name} {subcommand.name} {nested_command.name}", nested_command
            else:
                yield f"{command.name} {subcommand.name}", subcommand


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


def collect_declared_command_names(path: Path) -> set[str]:
    """Collect decorator-declared slash/app command names from one Python module."""
    names: set[str] = set()
    if not path.exists():
        return names
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


def _active_command_paths(root: Path, command_paths: list[Path]) -> list[Path]:
    init_path = root / "commands" / "__init__.py"
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
        path = root / "commands" / f"{module_name}.py"
        if path.exists():
            active_paths.append(path)

    return sorted(set(active_paths)) or command_paths


def _relative_label(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def collect_static_primary_inventory(root: Path) -> StaticCommandInventory:
    """Collect the authoritative static command surface from the commands package."""
    names: set[str] = set()
    grouped: dict[str, set[str]] = {}
    name_sources: dict[str, list[str]] = {}
    all_command_paths = [
        path for path in sorted((root / "commands").glob("*.py")) if path.name != "__init__.py"
    ]
    active_command_paths = _active_command_paths(root, all_command_paths)
    group_helpers = _collect_group_helper_commands(all_command_paths)

    for path in active_command_paths:
        source_label = _relative_label(path, root)
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
            name_sources.setdefault(group_name, []).append(source_label)
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
                            name_sources.setdefault(name, []).append(source_label)
                            break
            elif isinstance(node, ast.Call):
                helper_name = _call_name(node)
                helper_commands = group_helpers.get(helper_name or "") or group_helpers.get(
                    (helper_name or "").split(".")[-1]
                )
                if not helper_commands or not node.args:
                    continue
                first_arg = node.args[0]
                if not isinstance(first_arg, ast.Name):
                    continue
                group_name = group_vars.get(first_arg.id)
                if group_name:
                    # architecture-check: allow - "update" is set mutation, not SQL.
                    grouped.setdefault(group_name, set()).update(helper_commands)

    return StaticCommandInventory(names=names, grouped=grouped, name_sources=name_sources)
