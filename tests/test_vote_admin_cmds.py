from __future__ import annotations

import ast
from pathlib import Path


def _vote_create_option_required_flags() -> list[tuple[str, bool]]:
    tree = ast.parse(Path("commands/vote_admin_cmds.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "vote_create":
            defaults_by_arg = dict(
                zip(node.args.args[-len(node.args.defaults) :], node.args.defaults, strict=True)
            )
            flags: list[tuple[str, bool]] = []
            for arg in node.args.args:
                if arg.arg == "ctx":
                    continue
                default = defaults_by_arg[arg]
                required = True
                if isinstance(default, ast.Call):
                    for keyword in default.keywords:
                        if (
                            keyword.arg == "required"
                            and isinstance(keyword.value, ast.Constant)
                            and keyword.value.value is False
                        ):
                            required = False
                flags.append((arg.arg, required))
            return flags
    raise AssertionError("vote_create command was not found")


def test_vote_create_places_required_options_before_optional_options() -> None:
    seen_optional = False
    for name, required in _vote_create_option_required_flags():
        if required:
            assert not seen_optional, f"{name} is required after an optional slash option"
        else:
            seen_optional = True


def test_vote_create_description_remains_optional() -> None:
    flags = dict(_vote_create_option_required_flags())

    assert flags["description"] is False
