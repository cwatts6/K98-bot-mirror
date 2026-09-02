#!/usr/bin/env python3
"""
scripts/find_similar_helpers.py

Scan python source in the repo for functions with potentially duplicated or very similar bodies.
Reports pairs with a fuzzy similarity score.

Usage:
    python3 scripts/find_similar_helpers.py [--min-score 0.85] [--exclude path1,path2]
"""

from __future__ import annotations

import argparse
import ast
import difflib
from pathlib import Path

# Files/dirs to ignore by default
DEFAULT_EXCLUDE = {".venv", "venv", "env", "__pycache__", ".git", "node_modules", "build", "dist"}


def iter_py_files(root: Path, exclude: set[str]):
    for p in root.rglob("*.py"):
        if any(part in exclude for part in p.parts):
            continue
        yield p


def extract_functions(source: str, path: Path) -> list[tuple[str, str, int]]:
    """
    Returns list of (qualified_name, normalized_body, lineno)
    """
    out = []
    try:
        tree = ast.parse(source)
    except Exception:
        return out

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            name = node.name
            # Qualified name: file::funcname:lineno
            qname = f"{path}:{name}:{getattr(node, 'lineno', 0)}"
            # try to extract source segment for the node (best-effort)
            try:
                body_src = ast.get_source_segment(source, node) or ""
            except Exception:
                # fallback: reconstruct simple signature + body tokens
                body_src = name + ":" + str(node.lineno)

            # Normalize: remove leading/trailing whitespace, collapse spaces, remove docstrings
            # Remove the first Expr if it's a Str (module docstring inside function)
            try:
                # crude normalization: remove all whitespace for similarity-by-structure
                lines = [ln.strip() for ln in body_src.splitlines() if ln.strip()]
                # drop first line if it starts with def/async def (we want body)
                if lines and (lines[0].startswith("def ") or lines[0].startswith("async def ")):
                    lines = lines[1:]
                # drop docstring lines heuristically
                if lines and (lines[0].startswith('"""') or lines[0].startswith("'''")):
                    # remove until closing triple quotes
                    i = 0
                    while i < len(lines):
                        if lines[i].endswith('"""') or lines[i].endswith("'''"):
                            i += 1
                            break
                        i += 1
                    lines = lines[i:]
                normalized = " ".join(lines)
            except Exception:
                normalized = body_src.strip()
            out.append((qname, normalized, getattr(node, "lineno", 0)))
    return out


def score(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()


def main():
    p = Path(".").resolve()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--min-score", type=float, default=0.85, help="Minimum similarity to report (0-1)"
    )
    parser.add_argument("--exclude", type=str, default="", help="Comma separated paths to exclude")
    args = parser.parse_args()

    exclude = set(DEFAULT_EXCLUDE)
    if args.exclude:
        exclude.update(x.strip() for x in args.exclude.split(",") if x.strip())

    funcs: list[tuple[str, str, int]] = []
    for py in iter_py_files(p, exclude):
        try:
            src = py.read_text(encoding="utf-8")
        except Exception:
            continue
        funcs.extend(extract_functions(src, py))

    # Simple pairwise compare (O(n^2), but repo-sized should be fine). For bigger repos, sample or index.
    n = len(funcs)
    results: list[tuple[float, str, str]] = []
    for i in range(n):
        qi, body_i, li = funcs[i]
        if not body_i:
            continue
        for j in range(i + 1, n):
            qj, body_j, lj = funcs[j]
            if not body_j:
                continue
            s = score(body_i, body_j)
            if s >= args.min_score:
                results.append((s, qi, qj))

    # Sort descending by score
    results.sort(reverse=True, key=lambda t: t[0])
    if not results:
        print("No similar function pairs found above threshold.")
        return

    print(f"Found {len(results)} similar function pairs (threshold={args.min_score}):")
    for s, a, b in results:
        print(f"  score={s:.3f}  {a}  <->  {b}")


if __name__ == "__main__":
    main()
