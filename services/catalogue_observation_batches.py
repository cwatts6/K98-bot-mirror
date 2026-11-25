"""Finite catalogue batches for the explicitly selected optimistic observer.

Each object stays in one batch, so window functions and per-object row ordering
keep their SQL semantics. Every original query/category remains present. The
caller must checkpoint after consuming each batch and validate the full result.
"""

import re

from kvk.dal.new_source_import_dal import SourceConflict

# Derived from the representative timing receipt, not an adaptive success cache.
# Striding the sorted scope spreads wide legacy tables across the fixed batches.
_WIDTHS = {
    "metadata.objects": 192,
    "metadata.columns": 64,
    "metadata.indexes": 96,
    "metadata.checks": 128,
    "metadata.foreign_keys": 256,
    "metadata.dependencies": 256,
    "identity.columns": 48,
    "identity.checks": 128,
    "identity.indexes": 256,
    "object_permissions": 32,
    "column_permissions": 64,
}
COLUMN_BASE_WIDTH = 16
# The combined native read exposed these two categories above the batch target.
# Keep the already-qualified separate-dispatch path's widths unchanged.
_COMBINED_WIDTHS = {
    "metadata.indexes": 64,
    "identity.default_constraints": 128,
    "metadata.triggers": 256,
    "metadata.foreign_keys": 128,
}


def statement_count(scope, *, combined_boundaries=False):
    # 22 catalogue reads, one lifecycle read and a boundary after each, plus
    # opening/final boundaries. Splitting adds a read and boundary per part.
    widths = _WIDTHS | _COMBINED_WIDTHS if combined_boundaries else _WIDTHS
    extra = sum(max(0, (len(scope) + width - 1) // width - 1) for width in widths.values())
    # Each column group has three decoration reads and smaller base lookups.
    column_groups = scopes(scope, "metadata.columns")
    extra += 2 * len(column_groups) + sum(
        (len(group) + COLUMN_BASE_WIDTH - 1) // COLUMN_BASE_WIDTH for group in column_groups
    )
    # Combining preserves every token; two standalone checkpoints remain. The
    # verifier counts execute dispatches and still enforces the shared ceiling.
    return 25 + extra if combined_boundaries else 48 + 2 * extra


def validate_scope(scope, checkpoint, *, combined_boundaries=False):
    if (
        type(combined_boundaries) is not bool
        or not isinstance(scope, list)
        or not 1 <= len(scope) <= 2048
        or not callable(checkpoint)
        or any(
            not isinstance(name, str)
            or not re.fullmatch(r"(?:dbo|KVK)\.[A-Za-z_][A-Za-z_0-9&]{0,127}", name)
            for name in scope
        )
        or len({name.casefold() for name in scope}) != len(scope)
    ):
        raise SourceConflict("Bounded unaliased source scope and observation checkpoint required.")
    if statement_count(scope, combined_boundaries=combined_boundaries) > 256:
        raise SourceConflict("Complete observer exceeds the 256-statement ceiling.")


def scopes(scope, category, *, combined_boundaries=False):
    widths = _WIDTHS | _COMBINED_WIDTHS if combined_boundaries else _WIDTHS
    width = widths.get(category)
    if width is None or len(scope) <= width:
        return (scope,)
    count = (len(scope) + width - 1) // width
    ordered = sorted(scope)
    return tuple(ordered[index::count] for index in range(count))


def combine(rows, scope, category):
    """Keep every row, restoring object groups after strided batches.

    Permissions use the same BIN2 object order as the existing SQL, retaining
    each object's native permission/column order. Identity row order need not
    equal the database's linguistic ordering: the portable fingerprint already
    canonicalizes those rows. No row or duplicate is removed here.
    """
    field = "object_name" if category.startswith("identity.") else "ObjectName"
    allowed = {name.casefold() for name in scope}
    if any(
        not isinstance(row, dict)
        or not isinstance(row.get(field), str)
        or row[field].casefold() not in allowed
        for row in rows
    ):
        raise SourceConflict("Catalogue batch returned a row outside its declared source scope.")
    return sorted(rows, key=lambda row: row[field].encode("utf-16-be"))
