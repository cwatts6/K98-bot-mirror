from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import Any


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
