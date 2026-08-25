# tests/test_embed_utils_target_lookup_injection.py
import ast
from pathlib import Path


def _class_node(tree: ast.AST, class_name: str) -> ast.ClassDef:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return node
    raise AssertionError(f"class {class_name} not found")


def _function_node(cls: ast.ClassDef, fn_name: str):
    for n in cls.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == fn_name:
            return n
    raise AssertionError(f"function {fn_name} not found")


def test_target_lookup_view_uses_injected_on_lookup_and_no_commands_import():
    source = Path("embed_utils.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    # 1) no direct dependency on Commands module
    assert "from Commands import mykvktargets" not in source
    assert "import Commands" not in source

    # 2) constructor includes on_lookup
    cls = _class_node(tree, "TargetLookupView")
    init = _function_node(cls, "__init__")
    arg_names = [a.arg for a in init.args.args]
    assert "on_lookup" in arg_names

    # 3) callback delegates to self.on_lookup(...)
    callback_fn = _function_node(cls, "make_callback")
    callback_src = ast.get_source_segment(source, callback_fn) or ""
    assert "self.on_lookup(interaction, governor_id)" in callback_src
