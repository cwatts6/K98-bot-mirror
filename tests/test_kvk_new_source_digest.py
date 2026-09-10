from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal, localcontext

from kvk_source_fixtures import (
    MAPPING,
    aggregate_bytes,
    metadata,
    player_bytes,
    player_row,
    rewrite_zip,
)
import pytest

from kvk.schemas.new_source_schema import (
    PLAYER_HEADERS,
    PLAYER_SCHEMA_VERSION,
    SourceValidationError,
)
from kvk.services.new_source_digest import canonical_decimal, semantic_digest_v1
from kvk.services.new_source_parser import parse_aggregate_workbook, parse_player_workbook


def parsed(content):
    return parse_player_workbook(content, metadata())


def test_t01_t02_artifact_retry_and_zip_metadata_reexport():
    content = player_bytes()
    first = parsed(content)
    assert parsed(content) == first
    reexport = parsed(rewrite_zip(content))
    assert reexport.artifact_sha256 != first.artifact_sha256
    assert reexport.digest == first.digest


def test_t03_row_header_and_sheet_order_do_not_change_digest():
    first = parsed(player_bytes())
    reordered = parsed(
        player_bytes([player_row(1002, 102), player_row()], headers=tuple(reversed(PLAYER_HEADERS)))
    )
    assert reordered.digest == first.digest
    aggregate = parse_aggregate_workbook(aggregate_bytes(), metadata(aggregate=True), MAPPING)
    reordered_aggregate = parse_aggregate_workbook(
        aggregate_bytes(reverse_sheets=True), metadata(aggregate=True), MAPPING
    )
    assert reordered_aggregate.digest == aggregate.digest


@pytest.mark.parametrize(
    "change",
    [
        {"T4 Kills": 2},
        {"Name": "different"},
        {"Alliance": "=Synthetic"},
        {"Alliance": None},
        {"VIP": "0"},
        {"AoO Avg Kill": "bad"},
    ],
)
def test_t04_t05_changed_recognized_cells_never_disappear(change):
    assert (
        parsed(player_bytes([player_row(**change)])).digest
        != parsed(player_bytes([player_row()])).digest
    )


def test_formula_type_is_distinct_from_literal_with_same_token():
    formula = parsed(player_bytes([player_row(Alliance="=1+1")]))
    literal = parsed(
        player_bytes(
            [player_row(Alliance="=1+1")], edit=lambda w: setattr(w["Scan"]["C2"], "data_type", "s")
        )
    )
    assert formula.digest != literal.digest


def test_only_approved_null_number_and_line_endings_normalize():
    first = parsed(player_bytes([player_row(Name="Line\nTwo", Alliance=None, Power=1)]))
    # Encode CR as an XML character reference: Windows' XLSX writer otherwise
    # translates an existing CRLF to CRCRLF before XML newline normalization.
    content = player_bytes([player_row(Name="Line\nTwo", Alliance="", Power=1.0)])
    content = rewrite_zip(
        content,
        lambda name, data: data.replace(b"Line\r\nTwo", b"Line&#13;\nTwo").replace(
            b"Line\nTwo", b"Line&#13;\nTwo"
        ),
    )
    second = parsed(content)
    assert first.digest == second.digest
    assert (
        parsed(player_bytes([player_row(Name="line\nTwo", Alliance=None)])).digest != first.digest
    )
    assert parsed(player_bytes([player_row(Name="Line\nTwo", Alliance=0)])).digest != first.digest


def test_t16_aggregate_tokens_and_precision_are_identity():
    one = parse_aggregate_workbook(aggregate_bytes(token="1.0M"), metadata(aggregate=True), MAPPING)
    two = parse_aggregate_workbook(
        aggregate_bytes(token="1.00M"), metadata(aggregate=True), MAPPING
    )
    assert (
        one.kingdom_rows[0].cell("DKP").metric.value == two.kingdom_rows[0].cell("DKP").metric.value
    )
    assert one.digest != two.digest


def test_t07_metadata_is_retained_not_sorted_by_upload_or_scan_id():
    first = parsed(player_bytes())
    older_metadata = replace(
        first.metadata,
        candidate=replace(
            first.metadata.candidate, scan_start_utc=datetime(2026, 9, 4, tzinfo=UTC)
        ),
    )
    older = parse_player_workbook(player_bytes(), older_metadata)
    assert older.metadata.candidate.scan_start_utc < first.metadata.candidate.scan_start_utc
    assert older.digest == first.digest
    assert older.metadata.event_identity != first.metadata.event_identity
    # No selection or admission is performed by a pure parser.


def test_t20_digest_v1_has_golden_synthetic_vector_and_no_silent_upgrade():
    result = parsed(player_bytes([player_row()]))
    assert result.schema_version == PLAYER_SCHEMA_VERSION
    assert result.digest.canonical_version == "semantic_digest_v1"
    assert (
        result.digest.sha256 == "bda549cea82699c69fae53e5ae25455572c6e0d1ceddb46627d490aa18b59395"
    )
    with pytest.raises(SourceValidationError):
        semantic_digest_v1(result.rows, "snapshot_report_players_v2")
    assert result.digest.canonical_version == "semantic_digest_v1"


def test_decimal_normalization_does_not_round_at_ambient_context_precision():
    with localcontext() as context:
        context.prec = 6
        assert (
            canonical_decimal(Decimal("12345678901234567890.123456"))
            == "12345678901234567890.123456"
        )
        assert canonical_decimal(Decimal("1.000")) == "1"
        assert canonical_decimal(Decimal("-0.000")) == "0"
