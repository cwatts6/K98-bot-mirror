# tests/test_domain_registrars_no_legacy_register_commands.py

import ast
from pathlib import Path

DOMAIN_MODULES = [
    "commands/admin_cmds.py",
    "commands/events_cmds.py",
    "commands/location_cmds.py",
    "commands/registry_cmds.py",
    "commands/stats_cmds.py",
    "commands/subscriptions_cmds.py",
]


def test_domain_registrars_do_not_call_legacy_register_commands():
    for rel in DOMAIN_MODULES:
        src = Path(rel).read_text(encoding="utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id != "register_commands", (
                    f"{rel} should not call legacy register_commands(); "
                    "domain modules must only register their own command set"
                )
