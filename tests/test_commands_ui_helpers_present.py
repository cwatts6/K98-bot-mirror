# tests/test_commands_ui_helpers_present.py
import ast
from pathlib import Path


def test_commands_has_log_source_helper_and_account_order_constant():
    src = Path("Commands.py").read_text(encoding="utf-8")
    tree = ast.parse(src)

    has_pick_log = any(
        isinstance(n, ast.FunctionDef) and n.name == "_pick_log_source" for n in tree.body
    )
    has_account_order = any(
        isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "ACCOUNT_ORDER" for t in n.targets)
        for n in tree.body
    )

    assert has_pick_log, "Commands.py must define _pick_log_source used by /logs"
    assert (
        has_account_order
    ), "Commands.py must define ACCOUNT_ORDER used by registry/location views"
