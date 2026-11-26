"""Repository-wide offline regression for the ROWCOUNT/BACKUP alias family.

Discovers tracked AND untracked source via Git, not a list of known queries.
This lexical guard is deliberately separate from the packet's ScriptDom grammar
gate. It does not claim to validate schema, permissions, or all SQL syntax.
"""

import ast
from itertools import pairwise
from pathlib import Path
import re
import subprocess


def sql_tokens(text):
    """Yield tokens outside comments, preserving quoted identifiers and strings."""
    position = 0
    while position < len(text):
        if text[position].isspace():
            position += 1
            continue
        if text.startswith("--", position):
            end = text.find("\n", position)
            position = len(text) if end < 0 else end + 1
            continue
        if text.startswith("/*", position):
            depth = 1
            position += 2
            while position < len(text) and depth:
                if text.startswith("/*", position):
                    depth += 1
                    position += 2
                elif text.startswith("*/", position):
                    depth -= 1
                    position += 2
                else:
                    # Quotes have no string-literal meaning inside a comment.
                    position += 1
            continue
        start = position
        if text[position] in "['\"":
            closing = "]" if text[position] == "[" else text[position]
            position += 1
            while position < len(text):
                if text[position] == closing:
                    position += 1
                    if position < len(text) and text[position] == closing:
                        position += 1
                        continue
                    break
                position += 1
        else:
            word = re.match(r"[A-Za-z_][A-Za-z_0-9]*", text[position:])
            position += len(word.group()) if word else 1
        yield text[start:position]


def alias_errors(sql):
    tokens = list(sql_tokens(sql))
    errors = [
        f"reserved alias {right!r} requires identifier delimiters"
        for left, right in pairwise(tokens)
        if left.upper() == "AS" and right.upper() in {"ROWCOUNT", "BACKUP"}
    ]
    # ROWCOUNT is also invalid as a bare column (the MGE UPDATE regression).
    # Preserve its valid SET ROWCOUNT and @@ROWCOUNT language constructs.
    if any(t.upper() in {"SELECT", "INSERT", "UPDATE", "DELETE", "SET"} for t in tokens):
        for index, token in enumerate(tokens):
            previous = tokens[index - 1].upper() if index else ""
            following = tokens[index + 1] if index + 1 < len(tokens) else ""
            if (
                token.upper() == "ROWCOUNT"
                and previous not in {"@", "AS"}
                and not (previous == "SET" and following != "=")
            ):
                errors.append("bare ROWCOUNT column requires identifier delimiters")
    return errors


def python_strings(text):
    """Include f-string literal parts and folded adjacent/concatenated literals."""
    tree = ast.parse(text)
    parents = {child: parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if isinstance(parents.get(node), ast.Expr):
                continue  # Python documentation is not emitted SQL.
            yield node.lineno, node.value
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):

            def fold(part):
                if isinstance(part, ast.Constant) and isinstance(part.value, str):
                    return part.value
                if isinstance(part, ast.BinOp) and isinstance(part.op, ast.Add):
                    return fold(part.left) + fold(part.right)
                raise ValueError

            try:
                yield node.lineno, fold(node)
            except ValueError:
                pass


def powershell_literals(text):
    """Keep here-string bodies whole, including embedded quote characters."""
    masked = list(text)
    for match in re.finditer(r"(?ms)@(?P<quote>['\"])\r?\n(?P<body>.*?)^(?P=quote)@", text):
        yield match.start(), match.group("body")
        for index in range(match.start(), match.end()):
            if masked[index] not in "\r\n":
                masked[index] = " "
    for match in re.finditer(r"'(?:''|[^'])*'|\"(?:`.|[^\"])*\"", "".join(masked), re.DOTALL):
        yield match.start(), match.group()[1:-1].replace("''", "'")


def source_errors(name, text):
    if name.endswith(".py"):
        pieces = python_strings(text)
    elif name.endswith(".ps1"):
        # PowerShell uses doubled quotes/backticks; inspect literal bodies as
        # well as here-strings. No PowerShell execution or expression expansion.
        pieces = (
            (text.count("\n", 0, start) + 1, body) for start, body in powershell_literals(text)
        )
    else:
        pieces = [(1, text)]
    return sorted(
        {f"{name}:{line}: {error}" for line, piece in pieces for error in alias_errors(piece)}
    )


def source_paths(root):
    names = (
        subprocess.check_output(
            [
                "git",
                "-C",
                str(root),
                "ls-files",
                "-z",
                "--cached",
                "--others",
                "--exclude-standard",
            ],
            timeout=30,
        )
        .decode()
        .split("\0")
    )
    return sorted(
        {
            name
            for name in names
            if name.endswith((".py", ".ps1", ".sql"))
            and not name.startswith(("tests/", ".", "docs/"))
            and (Path(root) / name).is_file()
        }
    )


def validate(root):
    return [
        error
        for name in source_paths(root)
        for error in source_errors(name, (Path(root) / name).read_text(encoding="utf-8-sig"))
    ]


if __name__ == "__main__":
    errors = validate(Path(__file__).resolve().parents[1])
    print("\n".join(errors) if errors else "SQL reserved-alias inventory passed")
    raise SystemExit(bool(errors))
