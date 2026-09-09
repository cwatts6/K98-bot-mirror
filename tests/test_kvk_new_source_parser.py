from dataclasses import replace
from decimal import Decimal
from io import BytesIO
import struct
from zipfile import ZIP_STORED, ZipFile

from kvk_source_fixtures import (
    MAPPING,
    aggregate_bytes,
    metadata,
    player_bytes,
    player_row,
    rewrite_zip,
)
import pytest

from kvk.models.new_source_observation import CampMapping
from kvk.schemas.new_source_schema import (
    BIGINT_MAX,
    CAMP_SHEET,
    KINGDOM_SHEET,
    PLAYER_HEADERS,
    PLAYER_SHEET,
    MetricState,
    ParseLimits,
    SourceValidationError,
)
from kvk.services.new_source_parser import parse_aggregate_workbook, parse_player_workbook


def player(content, limits=ParseLimits()):
    return parse_player_workbook(content, metadata(), limits)


def aggregate(content, limits=ParseLimits(), mapping=MAPPING):
    return parse_aggregate_workbook(content, metadata(aggregate=True), mapping, limits)


def test_preserves_typed_rows_optional_profiles_and_all_observed_identities():
    result = player(player_bytes([player_row(1001), player_row(9009, 102, VIP=0)]))
    assert [r.key for r in result.rows] == [1001, 9009]
    assert result.rows[1].cell("VIP").metric.value == 0
    assert result.rows[0].kingdom == 101
    assert len(result.rows[0].cells) == 36
    assert not hasattr(result, "scan_id")  # No allocation or B0 roster mutation in S1.


@pytest.mark.parametrize(
    "identity",
    [
        -1,
        0,
        1.5,
        True,
        "12.5",
        "1e3",
        "NaN",
        "Infinity",
        "bad",
        "=1+1",
        1_000_000_000_000_000,
        str(BIGINT_MAX + 1),
        None,
    ],
)
def test_t13_invalid_or_precision_lost_identity_rejects(identity):
    with pytest.raises(SourceValidationError):
        player(player_bytes([player_row(identity)]))


def test_t13_large_text_identity_is_lossless():
    result = player(player_bytes([player_row(str(BIGINT_MAX))]))
    assert result.rows[0].key == BIGINT_MAX
    assert result.rows[0].cell("Governor ID").cell_type == "s"


@pytest.mark.parametrize(
    "rows", [[player_row(), player_row()], [player_row(1001, 999)], [player_row(1001, "=101")]]
)
def test_t13_duplicates_unknown_kingdom_formula_kingdom(rows):
    with pytest.raises(SourceValidationError):
        player(player_bytes(rows))


def test_t14_formula_text_and_blank_are_unavailable_with_raw_evidence():
    result = player(
        player_bytes(
            [
                player_row(Alliance='=HYPERLINK("https://invalid.example","x")'),
                player_row(1002, 102, Alliance=None),
            ]
        )
    )
    formula = result.rows[0].cell("Alliance")
    assert formula.cell_type == "f"
    assert formula.metric.value is None
    assert formula.raw_value.startswith("=HYPERLINK")
    assert result.rows[1].cell("Alliance").cell_type == "null"
    assert result.rows[1].cell("VIP").metric.value == 0


@pytest.mark.parametrize(
    "value",
    ["=1+1", "NaN", "Infinity", "1e100000", "bad", 1.5, -1, str(BIGINT_MAX + 1), True, None],
)
def test_t15_invalid_optional_player_metric_never_zero_fills(value):
    result = player(player_bytes([player_row(**{"T4 Kills": value})]))
    metric = result.rows[0].cell("T4 Kills").metric
    assert metric.value is None and metric.state == MetricState.INVALID_SOURCE_VALUE
    assert result.rows[0].cell("T5 Kills").metric.value == 1
    assert result.diagnostics[0].count == 1


def test_fractional_average_raw_only_and_overlong_label_retained_unavailable():
    result = player(player_bytes([player_row(Name="x" * 257, **{"AoO Avg Kill": "1.5"})]))
    assert result.rows[0].cell("Name").raw_value == "x" * 257
    assert result.rows[0].cell("Name").metric.value is None
    assert result.rows[0].cell("AoO Avg Kill").raw_value == "1.5"
    assert result.rows[0].cell("AoO Avg Kill").metric.value is None


def test_t16_supplied_aggregate_authority_and_precision():
    result = aggregate(aggregate_bytes())
    metric = result.kingdom_rows[0].cell("DKP").metric
    assert (metric.value, metric.raw_token, metric.displayed_unit, metric.precision_kind) == (
        Decimal(25300000),
        "25.3M",
        Decimal(100000),
        "reported_abbreviated",
    )
    camp = result.camp_rows[0].cell("DKP").metric
    assert camp.value == Decimal(4779000000) and camp.displayed_unit == Decimal(1000000)
    assert camp.value != sum(r.cell("DKP").metric.value for r in result.kingdom_rows)
    assert not hasattr(result, "scan_id")


@pytest.mark.parametrize(
    "token,expected",
    [
        ("1,234.567890", "1234.567890"),
        ("0", "0"),
        ("99999999999999999999999999999999.999999", "99999999999999999999999999999999.999999"),
        ("1.234567m", "1234567"),
        ("1T", "1000000000000"),
    ],
)
def test_strict_aggregate_decimal_boundaries(token, expected):
    result = aggregate(aggregate_bytes(token=token))
    assert result.kingdom_rows[0].cell("DKP").metric.value == Decimal(expected)


@pytest.mark.parametrize(
    "token",
    [
        None,
        "=1+1",
        "NaN",
        "inf",
        True,
        "1+2",
        "1,23",
        "1.000,5",
        "1e3",
        "-1",
        "0.0000001",
        "100000000000000000000000000000000",
        "x" * 129,
    ],
)
def test_t15_required_aggregate_invalid_rejects_both_tabs(token):
    with pytest.raises(SourceValidationError):
        aggregate(aggregate_bytes(token=token))


@pytest.mark.parametrize(
    "edit",
    [
        lambda w: w.remove(w[CAMP_SHEET]),
        lambda w: setattr(w[CAMP_SHEET]["A3"], "value", "North Camp"),
        lambda w: w[KINGDOM_SHEET].delete_rows(3),
        lambda w: setattr(w[KINGDOM_SHEET]["A2"], "value", "South Camp"),
        lambda w: setattr(w[CAMP_SHEET]["A2"], "value", "=1"),
        lambda w: setattr(w[CAMP_SHEET]["I3"], "value", None),
    ],
)
def test_t17_atomic_aggregate_validation(edit):
    with pytest.raises(SourceValidationError):
        aggregate(aggregate_bytes(edit=edit))


def test_camp_lookup_normalizes_only_for_identity_not_source_digest():
    original = aggregate(aggregate_bytes())
    changed = aggregate(
        aggregate_bytes(edit=lambda w: setattr(w[KINGDOM_SHEET]["A2"], "value", "  NORTH   camp "))
    )
    assert changed.kingdom_rows[0].camp_id == original.kingdom_rows[0].camp_id
    assert changed.digest != original.digest


@pytest.mark.parametrize(
    "mapping",
    [
        CampMapping(((101, 1, "North"), (102, 2, " north "))),
        CampMapping(((101, 1, "North"), (102, 1, "South"))),
        CampMapping(((101, 1, "North Camp"),)),
        CampMapping(((101, 1, "North Camp"), (101, 2, "South Camp"))),
    ],
)
def test_ambiguous_incomplete_or_duplicate_mapping_rejects(mapping):
    with pytest.raises(SourceValidationError):
        aggregate(aggregate_bytes(), mapping=mapping)


def test_t18_only_approved_nine_numeric_tail_annotations_are_ignored():
    def add_tail(w):
        for row in range(5, 14):
            w[KINGDOM_SHEET].cell(row, 5, row * 10)

    original = aggregate(aggregate_bytes())
    result = aggregate(aggregate_bytes(edit=add_tail))
    assert result.digest == original.digest
    assert result.diagnostics[0].count == 9
    assert result.diagnostics[0].cell_range == "E5:E13"


@pytest.mark.parametrize("column,value", [(2, 101), (5, "novel text"), (5, "=1+1"), (6, 1)])
def test_t18_keyed_or_novel_tail_rejects(column, value):
    with pytest.raises(SourceValidationError):
        aggregate(aggregate_bytes(edit=lambda w: w[KINGDOM_SHEET].cell(5, column, value)))


@pytest.mark.parametrize(
    "edit",
    [
        lambda w: w.create_sheet("unknown"),
        lambda w: w[PLAYER_SHEET].cell(1, 37, "new"),
        lambda w: w[PLAYER_SHEET].cell(2, 37, "unknown data"),
        lambda w: setattr(w[PLAYER_SHEET]["A1"], "value", "governor_id"),
        lambda w: w[PLAYER_SHEET].insert_rows(3),
    ],
)
def test_t19_unknown_schema_and_malformed_keyed_table(edit):
    with pytest.raises(SourceValidationError):
        player(player_bytes(edit=edit))


@pytest.mark.parametrize("content", [b"", b"a,b,c\n1,2,3", b"\xd0\xcf\x11\xe0", "a/path.xlsx"])
def test_t19_bytes_only_and_no_xls_csv_fallback(content):
    with pytest.raises(SourceValidationError):
        player(content)


@pytest.mark.parametrize(
    "field,limit",
    [
        ("max_compressed_bytes", 100),
        ("max_uncompressed_bytes", 100),
        ("max_entry_bytes", 100),
        ("max_zip_members", 2),
        ("max_compression_ratio", 1),
        ("max_player_rows", 1),
        ("max_columns", 35),
        ("max_populated_cells", 50),
        ("max_cell_characters", 10),
    ],
)
def test_each_player_resource_budget_is_enforced(field, limit):
    with pytest.raises(SourceValidationError):
        player(player_bytes(), replace(ParseLimits(), **{field: limit}))


@pytest.mark.parametrize("field", ["max_kingdom_rows", "max_camps"])
def test_each_aggregate_scope_budget_is_enforced(field):
    with pytest.raises(SourceValidationError):
        aggregate(aggregate_bytes(), replace(ParseLimits(), **{field: 1}))


@pytest.mark.parametrize(
    "name",
    [
        "../escape.xml",
        "/absolute.xml",
        "a\\b.xml",
        "C:escape.xml",
        "a/./b.xml",
        "a//b.xml",
        "xl/vbaProject.bin",
    ],
)
def test_t19_zip_traversal_and_macro_parts_reject(name):
    with pytest.raises(SourceValidationError):
        player(rewrite_zip(player_bytes(), additions=((name, b"x"),)))


def test_duplicate_encrypted_corrupt_and_macro_content_type_reject():
    original = player_bytes()
    with pytest.warns(UserWarning, match="Duplicate name"):
        duplicate = rewrite_zip(original, additions=(("xl/workbook.xml", b"x"),))
    with pytest.raises(SourceValidationError):
        player(duplicate)
    encrypted = bytearray(original)
    index = encrypted.index(b"PK\x01\x02")
    struct.pack_into("<H", encrypted, index + 8, 1)
    with pytest.raises(SourceValidationError):
        player(bytes(encrypted))
    with pytest.raises(SourceValidationError):
        player(original[:-20])
    macro = rewrite_zip(
        original,
        lambda name, data: (
            data.replace(b"spreadsheetml.sheet.main+xml", b"ms-excel.sheet.macroEnabled.main+xml")
            if name == "[Content_Types].xml"
            else data
        ),
    )
    with pytest.raises(SourceValidationError):
        player(macro)


@pytest.mark.parametrize("encoding", ["utf-8", "utf-16"])
def test_dtd_entities_rejected_before_expansion_even_utf16(encoding):
    data = (
        '<?xml version="1.0" encoding="' + encoding + '"?>'
        '<!DOCTYPE x [<!ENTITY a "amplification">]><x>&a;</x>'
    ).encode(encoding)
    with pytest.raises(SourceValidationError) as error:
        player(rewrite_zip(player_bytes(), additions=(("extra.xml", data),)))
    assert error.value.code == "xml_declaration"


def test_external_relationships_never_followed():
    def external(name, data):
        if name == "xl/_rels/workbook.xml.rels":
            return data.replace(
                b"</Relationships>",
                b'<Relationship Id="external" '
                b'Target="https://invalid.example/data" TargetMode="External" '
                b'Type="externalLink"/></Relationships>',
            )
        return data

    with pytest.raises(SourceValidationError) as error:
        player(rewrite_zip(player_bytes(), external))
    assert error.value.code == "external_relationship"


def test_dimensions_cannot_hide_populated_cells_or_bypass_sparse_bounds():
    original = player_bytes()
    hidden = rewrite_zip(original, lambda name, data: data.replace(b"A1:AJ3", b"A1:A1"))
    assert player(hidden).digest == player(original).digest
    sparse = rewrite_zip(original, lambda name, data: data.replace(b'r="AJ3"', b'r="ZZ3"'))
    with pytest.raises(SourceValidationError):
        player(sparse)
    disorder = rewrite_zip(original, lambda name, data: data.replace(b'r="AJ3"', b'r="AJ2"'))
    with pytest.raises(SourceValidationError):
        player(disorder)


def test_actual_read_budget_is_checked_independently_of_advertised_sizes(monkeypatch):
    import kvk.services.new_source_parser as parser

    original = player_bytes()
    real_open = ZipFile.open

    def too_large(self, entry, *args, **kwargs):
        if getattr(entry, "filename", "") == "docProps/app.xml":
            return BytesIO(b"x" * 20001)
        return real_open(self, entry, *args, **kwargs)

    monkeypatch.setattr(parser.ZipFile, "open", too_large)
    with pytest.raises(SourceValidationError) as error:
        player(original, replace(ParseLimits(), max_entry_bytes=20000, max_compression_ratio=1000))
    assert error.value.code == "zip_actual_size"


def test_handles_closed_on_success_and_validation_failure(monkeypatch):
    import kvk.services.new_source_parser as parser

    real_load = parser.load_workbook
    closed = []

    def load(*args, **kwargs):
        workbook = real_load(*args, **kwargs)
        real_close = workbook.close

        def close():
            closed.append(True)
            real_close()

        workbook.close = close
        return workbook

    monkeypatch.setattr(parser, "load_workbook", load)
    player(player_bytes())
    with pytest.raises(SourceValidationError):
        player(player_bytes(headers=PLAYER_HEADERS[:-1]))
    assert len(closed) == 2


def test_numeric_xml_precision_retained_without_binary_float_round_trip():
    data = rewrite_zip(
        aggregate_bytes(token=1),
        lambda name, raw: (
            raw.replace(b"<v>1</v>", b"<v>12345678901234567890.123456</v>")
            if name == "xl/worksheets/sheet1.xml"
            else raw
        ),
        compression=ZIP_STORED,
    )
    result = aggregate(data)
    assert result.kingdom_rows[0].cell("DKP").metric.value == Decimal("12345678901234567890.123456")


def test_t63_literal_formula_like_text_is_retained_without_execution():
    def literal(w):
        cell = w[PLAYER_SHEET]["B2"]
        cell.value, cell.data_type = "=literal @everyone", "s"

    result = player(player_bytes(edit=literal))
    assert result.rows[0].cell("Name").metric.value == "=literal @everyone"
    # Export escaping/Discord rendering belong to S4; this private DTO is not public output.


def test_formula_descriptors_fail_closed_instead_of_hashing_object_addresses():
    from openpyxl.worksheet.formula import ArrayFormula

    with pytest.raises(SourceValidationError) as error:
        player(
            player_bytes(
                edit=lambda w: setattr(
                    w[PLAYER_SHEET]["K2"], "value", ArrayFormula(ref="K2:K3", text="=1+1")
                )
            )
        )
    assert error.value.code == "unsupported_formula"


@pytest.mark.parametrize("raw", [b"NaN", b"INF", b"1e100000"])
def test_invalid_numeric_xml_stays_unavailable_without_decimal_expansion(raw):
    def invalid(name, data):
        if name == "xl/worksheets/sheet1.xml":
            return data.replace(b'<c r="K2" t="n"><v>1</v>', b'<c r="K2" t="n"><v>' + raw + b"</v>")
        return data

    result = player(rewrite_zip(player_bytes(), invalid))
    cell = result.rows[0].cell("T4 Kills")
    assert cell.metric.value is None
    assert cell.raw_value == raw.decode()


def test_dates_boolean_and_error_optional_cells_have_distinct_types():
    from datetime import datetime

    row = player_row(Power=datetime(2026, 1, 1), **{"T4 Kills": "#VALUE!", "T5 Kills": True})
    result = player(player_bytes([row])).rows[0]
    assert [result.cell(h).cell_type for h in ("Power", "T4 Kills", "T5 Kills")] == ["d", "e", "b"]
    assert all(result.cell(h).metric.value is None for h in ("Power", "T4 Kills", "T5 Kills"))


def test_source_cell_over_32767_rejects_before_openpyxl_can_truncate():
    def long_text(name, data):
        return data.replace(b"Synthetic Governor", b"x" * 32768)

    with pytest.raises(SourceValidationError) as error:
        player(
            rewrite_zip(player_bytes(), long_text),
            replace(ParseLimits(), max_compression_ratio=1000),
        )
    assert error.value.code == "cell_text_limit"


def test_aggregate_11th_tail_note_is_not_silently_dropped():
    def tail(w):
        for row in range(5, 15):
            w[KINGDOM_SHEET].cell(row, 5, 1)

    with pytest.raises(SourceValidationError):
        aggregate(aggregate_bytes(edit=tail))


def test_player_parser_rejects_forged_metadata_with_unapplied_overrides():
    from datetime import UTC, datetime

    original = metadata()
    forged = replace(
        original,
        confirmation=replace(
            original.confirmation,
            values=(("scan_start_utc", datetime(2026, 1, 1, tzinfo=UTC)),),
            confirmed_fields=("scan_start_utc",),
            reason="Synthetic conflict",
        ),
    )
    with pytest.raises(SourceValidationError) as error:
        parse_player_workbook(player_bytes(), forged)
    assert error.value.code == "metadata_confirmation_mismatch"


@pytest.mark.parametrize("extension", ["dat", "XML", "part"])
@pytest.mark.parametrize("declaration", [False, True])
def test_all_consumed_parts_receive_preflight_regardless_of_extension(extension, declaration):
    original = player_bytes()
    with ZipFile(BytesIO(original)) as old, BytesIO() as output:
        with ZipFile(output, "w") as new:
            for entry in old.infolist():
                data = old.read(entry.filename).replace(
                    b"sheet1.xml", f"sheet1.{extension}".encode()
                )
                name = entry.filename
                if name == "xl/worksheets/sheet1.xml":
                    name = f"xl/worksheets/sheet1.{extension}"
                    if declaration:
                        data = (
                            b'<!DOCTYPE worksheet [<!ENTITY label "Synthetic Governor">]>'
                            + data.replace(b"Synthetic Governor", b"&label;")
                        )
                new.writestr(name, data)
        content = output.getvalue()
    if declaration:
        with pytest.raises(SourceValidationError) as error:
            player(content)
        assert error.value.code == "xml_declaration"
    else:
        assert player(content).digest == player(original).digest


@pytest.mark.parametrize("path", ["xl/worksheets/sheet1.xml", "/xl/worksheets/sheet1.xml"])
def test_sheet_numeric_evidence_resolves_package_paths_without_rounding(path):
    from types import SimpleNamespace

    from kvk.services.new_source_parser import _sheet_numeric_tokens

    tokens = {"A2": "12345678901234567890.123456"}
    assert (
        _sheet_numeric_tokens(
            SimpleNamespace(_worksheet_path=path), {"xl/worksheets/sheet1.xml": tokens}
        )
        is tokens
    )


@pytest.mark.parametrize(
    "attributes",
    [
        {},
        {"_worksheet_path": None},
        {"_worksheet_path": ""},
        {"_worksheet_path": "xl/worksheets/missing.xml"},
    ],
)
def test_missing_or_changed_loader_path_rejects_safely(attributes):
    from types import SimpleNamespace

    from kvk.services.new_source_parser import _sheet_numeric_tokens

    with pytest.raises(SourceValidationError) as error:
        _sheet_numeric_tokens(SimpleNamespace(**attributes), {"xl/worksheets/sheet1.xml": {}})
    assert error.value.code == "numeric_evidence"


@pytest.mark.parametrize("kind", ["player", "aggregate"])
def test_missing_numeric_lexemes_never_fall_back_to_loader_values(monkeypatch, kind):
    import kvk.services.new_source_parser as parser

    original = parser._xml_preflight

    def lose_tokens(data, limits, total_cells):
        original(data, limits, total_cells)
        return {}

    monkeypatch.setattr(parser, "_xml_preflight", lose_tokens)
    with pytest.raises(SourceValidationError) as error:
        if kind == "player":
            player(player_bytes())
        else:
            aggregate(aggregate_bytes(token=1))
    assert error.value.code == "numeric_evidence"


def test_text_only_aggregate_sheet_keeps_empty_numeric_evidence():
    def text_identities(workbook):
        for row in (2, 3):
            cell = workbook[KINGDOM_SHEET].cell(row, 2)
            cell.value = str(cell.value)

    result = aggregate(aggregate_bytes(edit=text_identities))
    assert result.kingdom_rows[0].cell("DKP").metric.value == Decimal("25300000")
