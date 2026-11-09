"""Stage 1B: tier-only reader arithmetic over immutable publication facts."""

from copy import deepcopy
from dataclasses import FrozenInstanceError
from decimal import ROUND_UP, Decimal, localcontext
import json

import pytest

from kvk.combat_metrics import calculate_combat_metrics
from kvk.models.new_source_report_metrics import REPORT_METRIC_VERSION
from kvk.schemas.new_source_schema import MetricState
from kvk.services.new_source_report_metrics import derive_report_metrics

PUBLICATION = "00000000-0000-0000-0000-000000000001"
REVISION = "00000000-0000-0000-0000-000000000002"


def published_row(kind="player", **changes):
    row = dict(
        GovernorID=1001,
        Kingdom=101,
        CampID=1,
        t4_kills=Decimal("1000000"),
        t5_kills=Decimal("2000000"),
        kp_t4_t5=Decimal("50000000"),
        healed=Decimal("250000"),
        dead=Decimal("100000"),
        dkp=Decimal("123456789.125000"),
        total_kill_points=Decimal("999999999"),
        t1_kills=Decimal("999999"),
        t2_kills=Decimal("999999"),
        t3_kills=Decimal("999999"),
        t4_t5_dead=Decimal("1"),
        healed_points=Decimal("999"),
        tanking_score=None,
    )
    row.update(changes)
    row["FieldStatusJson"] = json.dumps(
        {
            key: "available" if value is not None else "missing_end"
            for key, value in row.items()
            if isinstance(value, Decimal) or value is None
        }
        | {"tanking_score": "unsupported"}
    )
    if kind != "player":
        for key in ("t4_kills", "t5_kills", "kp_t4_t5", "healed", "dead", "dkp"):
            row[key + "_raw"] = str(row[key])
            row[key + "_unit"] = Decimal("0.000001")
            row[key + "_precision"] = "reported_numeric"
    return row


def derive(kind="player", row=None, **changes):
    return derive_report_metrics(
        publication_id=PUBLICATION,
        calculation_version="snapshot_report_calculation_v3",
        entity_kind=kind,
        row=published_row(kind, **changes) if row is None else row,
        aggregate_revision_id=REVISION if kind != "player" else None,
    )


@pytest.mark.parametrize("kind", ["player", "kingdom", "camp"])
def test_same_tier_formula_and_percentage_fraction_for_every_entity(kind):
    result = derive(kind)
    assert result.version == REPORT_METRIC_VERSION
    assert result.metric("kills_gain").value == 3_000_000
    assert result.metric("kp_t4_t5").value == 50_000_000
    assert result.metric("kp_loss").value == 5_000_000
    score = result.metric("tanking_score")
    assert score.value == Decimal("9.803921568627")
    assert format(score.value, ".2%") == "980.39%"
    assert result.metric("dkp").value == Decimal("123456789.125000")
    payload = result.to_dict()
    assert payload["metrics"]["tanking_score"]["unit"] == "fraction"
    assert payload["metrics"]["tanking_score"]["value"] == "9.803921568627"
    assert Decimal(json.loads(json.dumps(payload))["metrics"]["kp_loss"]["value"]) == 5_000_000
    assert "Deads" in payload["metrics"]["tanking_score"]["definition"]


@pytest.mark.parametrize("kind", ["player", "kingdom", "camp"])
def test_lower_tiers_all_tier_kp_and_tier_deads_never_affect_metrics(kind):
    old = derive(kind)
    new = derive(
        kind,
        total_kill_points=Decimal("0"),
        t1_kills=Decimal("0"),
        t2_kills=Decimal("0"),
        t3_kills=Decimal("0"),
        t4_t5_dead=Decimal("9999999"),
        healed_points=Decimal("123"),
    )
    assert new == old


def test_player_kp_comes_from_tier_deltas_not_a_stored_legacy_field():
    assert derive(kp_t4_t5=Decimal("999999")).metric("kp_t4_t5").value == 50_000_000


@pytest.mark.parametrize("kind", ["kingdom", "camp"])
def test_aggregate_kp_dkp_and_fractional_report_values_are_not_recomputed_or_truncated(kind):
    result = derive(
        kind,
        kp_t4_t5=Decimal("100.5"),
        t4_kills=Decimal("1.25"),
        t5_kills=Decimal("2.5"),
        healed=Decimal("0.125"),
        dead=Decimal("0.5"),
    )
    assert result.metric("kills_gain").value == Decimal("3.75")
    assert result.metric("kp_t4_t5").value == Decimal("100.5")
    assert result.metric("kp_loss").value == Decimal("2.5")
    assert result.metric("tanking_score").value == Decimal("33.500000000000")
    assert result.metric("dkp").value == Decimal("123456789.125000")


@pytest.mark.parametrize("kind", ["kingdom", "camp"])
def test_abbreviated_source_resolution_and_revision_are_retained(kind):
    row = published_row(kind)
    row.update(
        healed_raw="250K", healed_unit=Decimal("1000"), healed_precision="reported_abbreviated"
    )
    result = derive(kind, row)
    payload = result.to_dict()
    assert payload["aggregate_revision_id"] == REVISION
    assert payload["inputs"]["healed"] == {
        "value": "250000",
        "state": "available",
        "raw": "250K",
        "unit": "1000",
        "precision": "reported_abbreviated",
    }
    assert payload["metrics"]["kp_loss"]["precision"] == "derived_from_reported_values"
    assert "from_reported" in payload["metrics"]["tanking_score"]["precision"]


@pytest.mark.parametrize("kind", ["player", "kingdom", "camp"])
def test_no_healed_is_not_an_ingestion_error_and_zero_kp_is_valid(kind):
    no_healed = derive(kind, healed=Decimal(0))
    assert no_healed.metric("kp_loss").value == 0
    assert no_healed.metric("tanking_score").state == MetricState.NOT_APPLICABLE
    assert no_healed.metric("tanking_score").reason == "no_healed_troops"
    zero_kp = derive(kind, t4_kills=Decimal(0), t5_kills=Decimal(0), kp_t4_t5=Decimal(0))
    assert zero_kp.metric("tanking_score").value == 0
    assert zero_kp.metric("tanking_score").state == MetricState.AVAILABLE
    zero_denominator = derive(kind, healed=Decimal(0), dead=Decimal(0))
    assert zero_denominator.metric("tanking_score").value is None


@pytest.mark.parametrize("kind", ["player", "kingdom", "camp"])
@pytest.mark.parametrize("key", ["healed", "dead", "t4_kills", "dkp"])
def test_missing_input_only_disables_dependent_metrics(kind, key):
    result = derive(kind, **{key: None})
    if key == "healed":
        assert result.metric("kp_loss").value is None
        assert result.metric("tanking_score").value is None
        assert result.metric("kills_gain").value == 3_000_000
    elif key == "dead":
        assert result.metric("tanking_score").value is None
        assert result.metric("kp_loss").value == 5_000_000
    elif key == "dkp":
        assert result.metric("dkp").value is None
        assert result.metric("tanking_score").value is not None
    else:
        assert result.metric("kills_gain").value is None
        # Provider KP remains usable even if its separately supplied kills are unavailable.
        assert (result.metric("tanking_score").value is None) == (kind == "player")


@pytest.mark.parametrize(
    "state", ["missing_start", "missing_end", "counter_regression", "unsupported"]
)
def test_original_player_unavailable_state_propagates(state):
    row = published_row(healed=None)
    states = json.loads(row["FieldStatusJson"])
    states["healed"] = state
    row["FieldStatusJson"] = json.dumps(states)
    result = derive(row=row)
    assert result.metric("kp_loss").state.value == state
    assert result.metric("tanking_score").state.value == state


@pytest.mark.parametrize("kind", ["player", "kingdom", "camp"])
@pytest.mark.parametrize(
    "value", [-1, True, 1.5, "250000", Decimal("NaN"), Decimal("Infinity"), Decimal("0.0000001")]
)
def test_invalid_source_healed_values_are_unavailable_not_coerced(kind, value):
    row = published_row(kind, healed=value)
    if kind == "player":
        states = json.loads(row["FieldStatusJson"])
        states["healed"] = "available"
        row["FieldStatusJson"] = json.dumps(states)
    result = derive(kind, row)
    assert result.metric("kp_loss").state == MetricState.INVALID_SOURCE_VALUE
    assert result.metric("tanking_score").value is None


@pytest.mark.parametrize(
    "key,value",
    [
        ("healed_unit", 0),
        ("healed_unit", Decimal("NaN")),
        ("healed_precision", "exact"),
        ("healed_raw", None),
    ],
)
def test_invalid_aggregate_provenance_cannot_be_labelled_exact(key, value):
    row = published_row("camp")
    row[key] = value
    assert derive("camp", row).metric("kp_loss").state == MetricState.INVALID_SOURCE_VALUE


@pytest.mark.parametrize(
    "kp,expected",
    [
        ("0.000001", "0.000000000000"),
        ("0.000003", "0.000000000002"),
        ("0.000005", "0.000000000002"),
    ],
)
def test_score_half_even_ties_and_ambient_context_independence(kp, expected):
    row = published_row("camp", kp_t4_t5=Decimal(kp), healed=Decimal("100000"), dead=Decimal(0))
    expected_result = derive("camp", row)
    with localcontext() as context:
        context.prec = 3
        context.rounding = ROUND_UP
        result = derive("camp", row)
    assert result == expected_result
    assert result.metric("tanking_score").value == Decimal(expected)


def test_large_input_derived_overflow_and_ratio_overflow_are_explicit():
    loss_overflow = derive("camp", healed=Decimal("1e31"))
    assert loss_overflow.metric("kp_loss").reason == "decimal_precision_or_overflow"
    assert loss_overflow.metric("tanking_score").value is None
    score_overflow = derive(
        "camp", kp_t4_t5=Decimal("1e31"), healed=Decimal("0.000001"), dead=Decimal(0)
    )
    assert score_overflow.metric("kp_loss").value == Decimal("0.000020")
    assert score_overflow.metric("tanking_score").reason == "ratio_decimal_overflow"
    assert (
        derive("camp", healed=Decimal("1e32")).metric("kp_loss").state
        == MetricState.INVALID_SOURCE_VALUE
    )
    assert derive(healed=Decimal(2**63)).metric("kp_loss").state == MetricState.INVALID_SOURCE_VALUE


@pytest.mark.parametrize("kind", ["player", "kingdom", "camp"])
def test_negative_deads_cannot_create_a_zero_or_negative_score_denominator(kind):
    result = derive(kind, dead=Decimal("-5000000"))
    assert result.metric("tanking_score").state == MetricState.INVALID_SOURCE_VALUE
    assert result.metric("kp_loss").value == 5_000_000


@pytest.mark.parametrize("kind", ["kingdom", "camp"])
def test_missing_reported_kp_never_falls_back_to_player_formula(kind):
    result = derive(kind, kp_t4_t5=None)
    assert result.metric("kp_t4_t5").value is None
    assert result.metric("tanking_score").value is None
    assert result.metric("kills_gain").value == 3_000_000
    assert result.metric("dkp").value == Decimal("123456789.125000")


def test_new_model_does_not_rewrite_old_audit_facts_or_legacy_helper():
    row = published_row()
    before = deepcopy(row)
    result = derive(row=row)
    assert row == before and row["tanking_score"] is None
    assert json.loads(row["FieldStatusJson"])["tanking_score"] == "unsupported"
    assert result.metric("tanking_score").state == MetricState.AVAILABLE
    assert result.to_dict()["version"] != result.to_dict()["calculation_version"]
    row["healed"] = Decimal(0)
    assert result.metric("kp_loss").value == 5_000_000
    with pytest.raises(FrozenInstanceError):
        result.version = "changed"
    legacy = calculate_combat_metrics(
        kill_points=100_000_000, healed=250_000, deads=100_000, t4_t5_kills=3_000_000
    )
    assert format(legacy.tanking_score, ".2f") == "1960.78"
    assert format(result.metric("tanking_score").value, ".2%") == "980.39%"


@pytest.mark.parametrize(
    "changes",
    [
        dict(publication_id="latest"),
        dict(calculation_version=""),
        dict(entity_kind="all"),
        dict(aggregate_revision_id=REVISION),
    ],
)
def test_invalid_or_ambiguous_context_is_rejected(changes):
    params = dict(
        publication_id=PUBLICATION,
        calculation_version="v3",
        entity_kind="player",
        row=published_row(),
    )
    with pytest.raises(ValueError):
        derive_report_metrics(**(params | changes))


def test_real_published_result_and_report_rows_feed_the_model():
    from kvk.dal.new_source_publication_dal import result_values
    from tests.test_kvk_source_reporting_models import snapshot

    original = snapshot()
    before = original.to_dict()
    player = result_values(original.calculation.players[0])
    result = derive(row=player)
    assert (
        result.metric("kp_t4_t5").value == original.calculation.players[0].metric("kp_t4_t5").value
    )
    assert result.metric("dkp").value == original.calculation.players[0].metric("dkp").value
    # Read retained provider numeric/raw/unit/precision exactly as the DAL stores them.
    source = original.aggregate.report.camp_rows[0]
    row = {"CampID": source.camp_id}
    for key, header in (
        ("t4_kills", "T4 Kills"),
        ("t5_kills", "T5 Kills"),
        ("kp_t4_t5", "KP (T4+T5)"),
        ("healed", "Healed"),
        ("dead", "Dead"),
        ("dkp", "DKP"),
    ):
        metric = source.cell(header).metric
        row.update(
            {
                key: metric.value,
                key + "_raw": metric.raw_token,
                key + "_unit": metric.displayed_unit,
                key + "_precision": metric.precision_kind,
            }
        )
    aggregate = derive("camp", row)
    assert aggregate.metric("kp_t4_t5").value == Decimal("4779000000")
    assert aggregate.metric("kp_loss").value == Decimal("95580000000")
    assert aggregate.metric("tanking_score").value == Decimal("0.047619047619")
    assert original.to_dict() == before
