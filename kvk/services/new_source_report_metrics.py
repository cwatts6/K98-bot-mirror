"""Pure report metrics from one pinned publication's player or aggregate row.

The caller owns authorization and publication/revision selection. This adapter performs
no reads, selection, mutations or legacy-consumer activation. It does not replace the
original audit facts or reinterpret their unsupported Tanking Score field.
"""

from decimal import Decimal, localcontext
import json
from uuid import UUID

from kvk.models.new_source_observation import MetricValue
from kvk.models.new_source_report_metrics import DerivedReportMetric, SourceReportMetrics
from kvk.models.new_source_reporting import CalculatedMetric, fits_decimal
from kvk.schemas.new_source_schema import BIGINT_MAX, INT_MAX, MetricState
from kvk.services.new_source_calculation import _derived, _ratio

INPUT_KEYS = ("t4_kills", "t5_kills", "kp_t4_t5", "healed", "dead", "dkp")


def _input(row, key, states, *, aggregate):
    state = MetricState(states.get(key, "unsupported")) if not aggregate else MetricState.AVAILABLE
    value = row.get(key)
    raw = row.get(key + "_raw") if aggregate else None
    unit = row.get(key + "_unit") if aggregate else None
    precision = row.get(key + "_precision") if aggregate else "exact_published"
    if state != MetricState.AVAILABLE:
        return MetricValue(None, state, None)
    if value is None:
        return MetricValue(None, MetricState.INVALID_SOURCE_VALUE, None)
    # No float conversion, integer truncation or rounding of source values.
    valid = type(value) in (int, Decimal)
    number = Decimal(value) if valid else None
    scale = 6 if aggregate or key in ("dkp", "kp_t4_t5") else 0
    valid = valid and fits_decimal(number, scale)
    if valid:
        valid = (number >= 0 or (not aggregate and key == "dkp")) and (
            scale != 0 or number <= BIGINT_MAX
        )
    if aggregate:
        valid = (
            valid
            and isinstance(raw, str)
            and 0 < len(raw) <= 128
            and type(unit) in (int, Decimal)
            and fits_decimal(Decimal(unit), 6)
            and unit > 0
            and precision in ("reported_numeric", "reported_abbreviated")
        )
    if not valid:
        return MetricValue(None, MetricState.INVALID_SOURCE_VALUE, None)
    return MetricValue(number, state, raw, Decimal(unit) if unit is not None else None, precision)


def derive_report_metrics(
    *, publication_id, calculation_version, entity_kind, row, aggregate_revision_id=None
) -> SourceReportMetrics:
    """Derive reader values without changing the publication or its calculation version.

    Input row shape is SourcePlayerResult, SourceKingdomReportRow or SourceCampReportRow.
    Aggregate values retain their supplied resolution; derived precision never claims
    that abbreviated reports became exact measurements. A score fraction rounds half-even
    to decimal(38,12); consumers apply percentage formatting exactly once.
    """
    if entity_kind not in ("player", "kingdom", "camp"):
        raise ValueError("Unknown report entity kind.")
    aggregate = entity_kind != "player"
    for identity in (publication_id, *((aggregate_revision_id,) if aggregate else ())):
        if not isinstance(identity, str) or str(UUID(identity)) != identity:
            raise ValueError("Canonical pinned publication/revision identities are required.")
    if not aggregate and aggregate_revision_id is not None:
        raise ValueError("Player metrics do not use an aggregate revision.")
    if not isinstance(calculation_version, str) or not 1 <= len(calculation_version) <= 64:
        raise ValueError("A pinned calculation version is required.")
    identity_key, maximum = {
        "player": ("GovernorID", BIGINT_MAX),
        "kingdom": ("Kingdom", INT_MAX),
        "camp": ("CampID", 8),
    }[entity_kind]
    entity_id = row[identity_key]
    if type(entity_id) is not int or not 1 <= entity_id <= maximum:
        raise ValueError("Invalid report entity identity.")
    states = {} if aggregate else json.loads(row["FieldStatusJson"])
    if not isinstance(states, dict):
        raise ValueError("Published metric statuses must be a mapping.")
    # Players derive KP solely from T4/T5 deltas. An old stored/all-tier KP value
    # cannot silently change that basis. Aggregate supplied tier KP stays authoritative.
    keys = INPUT_KEYS if aggregate else tuple(key for key in INPUT_KEYS if key != "kp_t4_t5")
    inputs = {key: _input(row, key, states, aggregate=aggregate) for key in keys}
    values = {
        key: CalculatedMetric(item.value, item.state, None if item.value is not None else key)
        for key, item in inputs.items()
    }
    with localcontext() as context:
        context.prec = 100
        kills = _derived((values["t4_kills"], values["t5_kills"]), (Decimal(1), Decimal(1)))
        kp = (
            values["kp_t4_t5"]
            if aggregate
            else _derived((values["t4_kills"], values["t5_kills"]), (Decimal(10), Decimal(20)))
        )
        loss = _derived((values["healed"],), (Decimal(20),))
        score = next((item for item in (kp, loss, values["dead"]) if item.value is None), None)
        if score is None:
            if values["healed"].value <= 0:
                score = CalculatedMetric(None, MetricState.NOT_APPLICABLE, "no_healed_troops")
            else:
                denominator = CalculatedMetric(
                    loss.value + values["dead"].value, MetricState.AVAILABLE
                )
                score = _ratio(kp, denominator)
    precision = "derived_from_reported_values" if aggregate else "exact_derived"
    metrics = (
        (
            "kills_gain",
            DerivedReportMetric(
                kills, "T4 Kills + T5 Kills", "troops", ("t4_kills", "t5_kills"), precision
            ),
        ),
        (
            "kp_t4_t5",
            DerivedReportMetric(
                kp,
                "Supplied T4+T5 KP" if aggregate else "10*T4 Kills + 20*T5 Kills",
                "points",
                ("kp_t4_t5",) if aggregate else ("t4_kills", "t5_kills"),
                "reported" if aggregate else precision,
            ),
        ),
        (
            "kp_loss",
            DerivedReportMetric(loss, "Healed Troops * 20", "points", ("healed",), precision),
        ),
        (
            "tanking_score",
            DerivedReportMetric(
                score,
                "T4+T5 KP / (Healed Troops * 20 + Deads); healed > 0",
                "fraction",
                (
                    ("kp_t4_t5", "healed", "dead")
                    if aggregate
                    else ("t4_kills", "t5_kills", "healed", "dead")
                ),
                "half_even_decimal_38_12_from_reported" if aggregate else "half_even_decimal_38_12",
            ),
        ),
        (
            "dkp",
            DerivedReportMetric(
                values["dkp"],
                "Supplied DKP" if aggregate else "Published player DKP with frozen weights",
                "points",
                ("dkp",),
                "reported" if aggregate else "exact_published",
            ),
        ),
    )
    return SourceReportMetrics(
        publication_id,
        calculation_version,
        entity_kind,
        entity_id,
        aggregate_revision_id,
        tuple(inputs.items()),
        metrics,
    )
