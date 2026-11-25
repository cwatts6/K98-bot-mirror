"""Version 1 canonical typed-cell comparison, separate from source event identity."""

from decimal import Decimal
import hashlib

from kvk.models.new_source_observation import SemanticDigest, SourceRow
from kvk.schemas.new_source_schema import (
    AGGREGATE_SCHEMA_VERSION,
    CAMP_HEADERS,
    CAMP_SHEET,
    KINGDOM_HEADERS,
    KINGDOM_SHEET,
    PLAYER_HEADERS,
    PLAYER_SCHEMA_VERSION,
    PLAYER_SHEET,
    SourceValidationError,
)


def canonical_decimal(value: Decimal) -> str:
    """Exact context-independent normalisation; Decimal.normalize can round at precision 28."""
    if not value.is_finite():
        return str(value)
    if value == 0:
        return "0"
    text = format(value, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def semantic_digest_v1(rows: tuple[SourceRow, ...], schema_version: str) -> SemanticDigest:
    """SHA256 over 8-byte big-endian byte lengths then UTF-8 fields.

    Fields: magic, schema, sheet count; for each sorted sheet: name, header count,
    canonical headers, row count; each numerically sorted row: key; then each cell:
    type, typed value. Aggregate metrics additionally include raw token, unit and
    precision kind. Null uses its own type, not a magic text sentinel. Formats and
    metadata do not participate. Any format change to this encoding needs v2.
    """
    schemas = {
        PLAYER_SCHEMA_VERSION: {PLAYER_SHEET: PLAYER_HEADERS},
        AGGREGATE_SCHEMA_VERSION: {KINGDOM_SHEET: KINGDOM_HEADERS, CAMP_SHEET: CAMP_HEADERS},
    }
    if schema_version not in schemas or not rows:
        raise SourceValidationError("digest_schema", "Digest requires validated versioned rows.")
    schema = schemas[schema_version]
    if set(r.sheet for r in rows) != set(schema):
        raise SourceValidationError("digest_sheets", "Digest sheet set is incomplete.")
    digest = hashlib.sha256()

    def field(value: str) -> None:
        encoded = value.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)

    field("semantic_digest_v1")
    field(schema_version)
    field(str(len(schema)))
    for sheet, headers in sorted(schema.items()):
        selected = sorted((r for r in rows if r.sheet == sheet), key=lambda r: r.key)
        if len({r.key for r in selected}) != len(selected):
            raise SourceValidationError("duplicate_identity", "Duplicate digest row identity.")
        field(sheet)
        field(str(len(headers)))
        for header in headers:
            field(header)
        field(str(len(selected)))
        for row in selected:
            if tuple(c.header for c in row.cells) != headers:
                raise SourceValidationError("digest_headers", "Digest requires canonical headers.")
            field(str(row.key))
            for cell in row.cells:
                field(cell.cell_type)
                field(
                    canonical_decimal(cell.numeric_value)
                    if cell.numeric_value is not None
                    else cell.raw_value or ""
                )
                if cell.metric.displayed_unit is not None:
                    # Numeric 1/1.0 normalizes; literal report tokens preserve their precision.
                    field(
                        canonical_decimal(cell.numeric_value)
                        if cell.numeric_value is not None
                        else cell.metric.raw_token or ""
                    )
                    field(canonical_decimal(cell.metric.displayed_unit))
                    field(cell.metric.precision_kind or "")
    return SemanticDigest(digest.hexdigest())
