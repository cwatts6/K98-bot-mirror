"""Exact player endpoint arithmetic and B0-cohort ranking, with no side effects."""

from dataclasses import replace
from decimal import Decimal, localcontext

from kvk.combat_metrics import calculate_combat_metrics
from kvk.models.new_source_observation import SourceRow
from kvk.models.new_source_reporting import (
    CalculatedMetric,
    MetricRank,
    ObservationInput,
    PeriodCalculation,
    PeriodKind,
    PlayerPeriodResult,
    WindowInputSelection,
    fits_decimal,
)
from kvk.schemas.new_source_schema import BIGINT_MAX, PLAYER_SCHEMA_VERSION, MetricState, SourceKind

COUNTER_FIELDS = (
    ("power", "Power"),
    ("troops_power", "Troops Power"),
    ("t1_kills", "T1 Kills"),
    ("t2_kills", "T2 Kills"),
    ("t3_kills", "T3 Kills"),
    ("t4_kills", "T4 Kills"),
    ("t5_kills", "T5 Kills"),
    ("total_kill_points", "Total Kill Points"),
    ("dead", "Dead"),
    ("healed", "Healed"),
    ("acclaim", "Acclaim"),
    ("highest_acclaim", "Highest Acclaim"),
)


def _unavailable(state: MetricState, reason: str | None = None) -> CalculatedMetric:
    return CalculatedMetric(None, state, reason)


def _counter(row: SourceRow | None, header: str, missing: MetricState) -> CalculatedMetric:
    if row is None:
        return _unavailable(missing)
    try:
        metric = row.cell(header).metric
    except StopIteration:
        return _unavailable(MetricState.INVALID_SOURCE_VALUE, "missing_source_field")
    value = metric.value
    if value is None and metric.raw_token is None:
        return _unavailable(missing)
    if (
        metric.state != MetricState.AVAILABLE
        or not isinstance(value, Decimal)
        or not value.is_finite()
        or value < 0
        or value > BIGINT_MAX
        or value != value.to_integral_value()
    ):
        return _unavailable(MetricState.INVALID_SOURCE_VALUE)
    return CalculatedMetric(value, MetricState.AVAILABLE)


def _delta(start: SourceRow | None, end: SourceRow | None, header: str) -> CalculatedMetric:
    left = _counter(start, header, MetricState.MISSING_START)
    right = _counter(end, header, MetricState.MISSING_END)
    if left.value is None:
        return left
    if right.value is None:
        return right
    value = right.value - left.value
    if value < 0 and header not in ("Power", "Troops Power"):
        return _unavailable(MetricState.COUNTER_REGRESSION)
    return CalculatedMetric(value, MetricState.AVAILABLE)


def _derived(
    inputs: tuple[CalculatedMetric, ...], coefficients: tuple[Decimal, ...]
) -> CalculatedMetric:
    terms = []
    for item, coefficient in zip(inputs, coefficients, strict=True):
        if item.value is None:
            return _unavailable(item.state, item.reason)
        terms.append(item.value * coefficient)
    value = sum(terms, Decimal(0))
    if not fits_decimal(value, 6):
        return _unavailable(MetricState.INVALID_SOURCE_VALUE, "decimal_precision_or_overflow")
    return CalculatedMetric(value, MetricState.AVAILABLE)


def _ratio(numerator: CalculatedMetric, denominator: CalculatedMetric) -> CalculatedMetric:
    if numerator.value is None:
        return _unavailable(numerator.state, numerator.reason)
    if denominator.value is None:
        return _unavailable(denominator.state, denominator.reason)
    if denominator.value <= 0:
        return _unavailable(MetricState.INVALID_SOURCE_VALUE, "nonpositive_denominator")
    value = numerator.value / denominator.value
    if not fits_decimal(value, 12):
        return _unavailable(MetricState.INVALID_SOURCE_VALUE, "ratio_not_exact_decimal_38_12")
    return CalculatedMetric(value, MetricState.AVAILABLE)


def _rows(event: ObservationInput | None, selection: WindowInputSelection) -> dict[int, SourceRow]:
    if event is None:
        return {}
    config = selection.config
    observation = event.observation
    meta = observation.metadata.candidate
    if (meta.source_key, meta.kvk_no, meta.kind, observation.schema_version) != (
        config.source_key,
        config.kvk_no,
        SourceKind.PLAYERS,
        PLAYER_SCHEMA_VERSION,
    ):
        raise ValueError("Endpoint source/season/schema mismatch.")
    rows = {row.key: row for row in observation.rows}
    if len(rows) != len(observation.rows) or any(
        type(key) is not int or not 1 <= key <= BIGINT_MAX for key in rows
    ):
        raise ValueError("Invalid or duplicate player identity.")
    return rows


def _name(*rows: SourceRow | None) -> str | None:
    for row in rows:
        if row is not None:
            try:
                metric = row.cell("Name").metric
            except StopIteration:
                continue
            if (
                metric.state == MetricState.AVAILABLE
                and isinstance(metric.value, str)
                and metric.value
            ):
                return metric.value
    return None


def calculate_period(selection: WindowInputSelection, b0: ObservationInput) -> PeriodCalculation:
    """Calculate all eligible members; final coverage requires only the two exact endpoints.

    Derived fixed-point values reject loss rather than rounding. Rank percentages are labelled
    presentation ratios computed at a fixed 50-digit precision, never stored as exact counters.
    """
    config = selection.config
    if b0.revision_id != config.b0_revision_id:
        raise ValueError("Roster must use the configured B0 revision.")
    if config.period_kind == PeriodKind.OVERALL and selection.start != b0:
        raise ValueError("Overall player arithmetic must start at exact B0.")
    roster = _rows(b0, selection)
    starts = _rows(selection.start, selection)
    ends = _rows(selection.end, selection)
    if not roster or len(roster) > 50_000:
        raise ValueError("B0 roster size is outside the accepted contract.")
    camps = {kingdom: camp for kingdom, camp, _ in config.mapping.entries}
    if any(row.kingdom not in camps for row in roster.values()):
        raise ValueError("B0 kingdom is absent from the frozen map.")
    results = []
    with localcontext() as context:
        # 38-digit coefficient plus bigint products/sums fit without ambient rounding.
        context.prec = 100
        for governor_id, baseline in sorted(roster.items()):
            start, end = starts.get(governor_id), ends.get(governor_id)
            metrics = {key: _delta(start, end, header) for key, header in COUNTER_FIELDS}
            metrics["starting_power"] = _counter(baseline, "Power", MetricState.MISSING_START)
            metrics["fight_start_power"] = _counter(start, "Power", MetricState.MISSING_START)
            metrics["end_power"] = _counter(end, "Power", MetricState.MISSING_END)
            metrics["end_troops_power"] = _counter(end, "Troops Power", MetricState.MISSING_END)
            metrics["kills_gain"] = _derived(
                (metrics["t4_kills"], metrics["t5_kills"]), (Decimal(1), Decimal(1))
            )
            metrics["kp_t4_t5"] = _derived(
                (metrics["t4_kills"], metrics["t5_kills"]), (Decimal(10), Decimal(20))
            )
            metrics["dkp"] = (
                _unavailable(MetricState.MISSING_CONFIGURATION, "missing_frozen_weights")
                if config.weights is None
                else _derived(
                    (metrics["t4_kills"], metrics["t5_kills"], metrics["dead"]),
                    config.weights.coefficients,
                )
            )
            # Canonical helper reused only for its compatible healed*20 definition.
            # Its legacy engagement gate must not exclude genuine zero ranks.
            healed = metrics["healed"]
            if healed.value is not None:
                combat = calculate_combat_metrics(
                    kill_points=None, healed=int(healed.value), deads=None, t4_t5_kills=None
                )
                metrics["healed_points"] = CalculatedMetric(
                    Decimal(combat.kp_loss), MetricState.AVAILABLE
                )
            else:
                metrics["healed_points"] = healed
            metrics["dkp_power_ratio"] = _ratio(metrics["dkp"], metrics["starting_power"])
            for key in ("t4_dead", "t5_dead", "t4_t5_dead", "power_extrema", "tanking_score"):
                metrics[key] = _unavailable(MetricState.UNSUPPORTED, "no_approved_compatible_basis")
            results.append(
                PlayerPeriodResult(
                    governor_id,
                    baseline.kingdom,
                    camps[baseline.kingdom],
                    _name(end, start, baseline),
                    tuple(metrics.items()),
                    observed_kingdom_changed=any(
                        row is not None and row.kingdom != baseline.kingdom for row in (start, end)
                    ),
                )
            )
        ranked = {result.governor_id: [] for result in results}
        coverage = []
        for key, _ in results[0].metrics:
            usable = [result for result in results if result.metric(key).value is not None]
            coverage.append((key, len(usable)))
            if config.period_kind == PeriodKind.NO_FIGHT:
                continue
            usable.sort(key=lambda result: (-result.metric(key).value, result.governor_id))
            with localcontext() as rank_context:
                rank_context.prec = 50
                for position, result in enumerate(usable, 1):
                    ranked[result.governor_id].append(
                        (
                            key,
                            MetricRank(
                                position,
                                len(usable),
                                Decimal(position) / Decimal(len(usable)) * 100,
                            ),
                        )
                    )
        results = [replace(result, ranks=tuple(ranked[result.governor_id])) for result in results]
    eligible = set(roster)
    return PeriodCalculation(
        selection,
        tuple(results),
        len(roster),
        len(eligible & starts.keys() & ends.keys()),
        len(eligible - starts.keys()),
        len(eligible - ends.keys()),
        len((starts.keys() | ends.keys()) - eligible),
        tuple(coverage),
    )
