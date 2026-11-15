"""Conservative procedure-header comparison for offline SQL validation tools.

This is not a SQL parser or a replacement for catalog identity/options checks.
Only the leading DDL keywords and their whitespace are canonicalized. The name,
signature and complete remaining definition are compared exactly.
"""
import re

_HEADER = re.compile(
    r"\A[ \t\r\n]*(?:CREATE(?:[ \t\r\n]+OR[ \t\r\n]+ALTER)?|ALTER)"
    r"[ \t\r\n]+PROCEDURE[ \t\r\n]+",
    re.IGNORECASE,
)


def canonical_procedure_definition(definition: str) -> str:
    if not isinstance(definition, str) or not definition:
        raise ValueError("A complete visible procedure definition is required")
    match = _HEADER.match(definition)
    if match is None or not definition[match.end():]:
        raise ValueError("Unsupported procedure header; retain actual catalog evidence")
    return "PROCEDURE " + definition[match.end():]


def same_procedure_definition(expected: str, actual: str) -> bool:
    return canonical_procedure_definition(expected) == canonical_procedure_definition(actual)
