"""Synthetic current-weight/window regressions; no live SQL or provider access."""

from dataclasses import replace
from datetime import datetime
from decimal import Decimal
import json
from unittest.mock import Mock

import pytest

from kvk.dal import source_weight_dal as dal
from kvk.dal.new_source_import_dal import SourceConflict
from kvk.models.source_configuration import configuration_meaning, weight_digest_tokens
from kvk.services import source_weight_service as service
from tests.test_kvk_season_source import Cursor
from tests.test_kvk_source_pairs import PairStore, uid, update_record


def imported(weights=("10", "20", "40")):
    return dict(
        weights=list(weights), effective="2026-10-12T10:19:48+00:00", mapping=[], windows=[]
    )


def test_import_time_and_decimal_spelling_are_not_calculation_authority():
    before = imported()
    after = dict(imported(("10.0", "2E1", "40.000")), effective="2026-10-13T00:00:00+00:00")
    assert configuration_meaning(before) == configuration_meaning(after)
    assert weight_digest_tokens(before["weights"]) == weight_digest_tokens(after["weights"])
    assert configuration_meaning(before) != configuration_meaning(imported(("11", "20", "40")))


@pytest.mark.parametrize("tamper", [None, "request", "mapping", "window", "source_fact"])
def test_weight_authority_cannot_expand_into_other_corrections(tamper):
    base = update_record()
    changed = update_record(
        ConfigVersionID=uid(40),
        BaseUpdateID=base["UpdateID"],
        RequestID=uid(41),
        ConfirmationJson=json.dumps(
            dict(action="correct", current_weights=True, automatic_weight_refresh=True)
        ),
    )
    if tamper == "source_fact":
        changed["EndRevisionID"] = uid(42)
    request = dict(
        RequestState="pending",
        ProvenanceJson='{"current_weights":true}',
        BaseConfigVersionID=base["ConfigVersionID"],
        DesiredConfigVersionID=changed["ConfigVersionID"],
        OldStartScanID=10,
        OldEndScanID=13,
        NewStartScanID=10,
        NewEndScanID=13,
    )
    config = dict(RosterID=base["RosterID"], MappingDigest=b"map", WindowDigest=b"window")

    def route(sql, args):
        if "FROM KVK.SourceConfigRequest" in sql:
            return [] if tamper == "request" else [request]
        if sql.startswith("SELECT ConfigVersionID"):
            return [
                dict(config, ConfigVersionID=base["ConfigVersionID"]),
                dict(
                    config,
                    ConfigVersionID=changed["ConfigVersionID"],
                    MappingDigest=b"other" if tamper == "mapping" else b"map",
                ),
            ]
        if sql.startswith("SELECT * FROM KVK.SourceUpdate"):
            return [base]
        if sql.startswith("SELECT c.RosterID"):
            return [
                dict(config, StartScanID=10, EndScanID=13),
                dict(config, StartScanID=10, EndScanID=14 if tamper == "window" else 13),
            ]
        raise AssertionError(sql)

    if tamper:
        with pytest.raises(SourceConflict):
            dal.validate_weight_authority(Cursor(route), changed)
    else:
        assert dal.validate_weight_authority(Cursor(route), changed)


@pytest.mark.parametrize("final,admin", [(False, False), (True, True), (True, False)])
def test_report_coverage_is_retained_independently_of_player_period(
    monkeypatch, tmp_path, final, admin
):
    from kvk.dal import new_source_import_dal as imports, season_source_dal as seasons
    from kvk.schemas.new_source_schema import ReportState
    from kvk.services.new_source_artifact_store import ArtifactStore
    from kvk.services.new_source_parser import parse_aggregate_workbook
    from tests.kvk_source_fixtures import MAPPING, aggregate_bytes, metadata
    from tests.test_kvk_source_sql_integration import admission

    artifacts = ArtifactStore(tmp_path)
    content = aggregate_bytes()
    artifact = artifacts.persist_artifact(content)
    meta = metadata(aggregate=True)
    if final:
        meta = replace(meta, candidate=replace(meta.candidate, report_state=ReportState.FINAL))
    prepared = parse_aggregate_workbook(content, meta, MAPPING)

    def route(sql, args):
        if sql.startswith("SELECT * FROM KVK.SourcePeriod"):
            return [
                dict(
                    PeriodKind="fight",
                    CoverageStartUTC=datetime(2026, 1, 1),
                    CoverageEndUTC=datetime(2026, 1, 2),
                )
            ]
        if sql.startswith("SELECT ISNULL(MAX(RevisionNo)"):
            return [{"n": 1}]
        return []

    cursor = Cursor(route)
    connection = Mock(autocommit=False)
    connection.cursor.return_value = cursor
    target = imports.SourceImportDAL(lambda: connection, artifacts)
    monkeypatch.setattr(imports, "lock_scope", Mock())
    monkeypatch.setattr(seasons, "require_source", Mock())
    monkeypatch.setattr(target, "_artifact", Mock())
    monkeypatch.setattr(target, "_replay", Mock(return_value=None))
    monkeypatch.setattr(target, "_attempt", Mock())
    if final and not admin:
        with pytest.raises(SourceConflict, match="authorized finalization"):
            target.accept_aggregate(prepared, artifact, admission(admin_authorized=admin))
        connection.commit.assert_not_called()
    else:
        accepted = target.accept_aggregate(prepared, artifact, admission(admin_authorized=admin))
        assert accepted.selected
        connection.commit.assert_called_once()
        statement = next(
            args
            for sql, args in cursor.statements
            if sql.startswith("INSERT KVK.SourceAggregateRevision")
        )
        assert prepared.metadata.candidate.coverage_start_utc.replace(tzinfo=None) in statement


@pytest.mark.parametrize("new_weight", ["10", "99"])
def test_new_period_retains_roster_but_accepts_current_weights_and_import_time(
    monkeypatch, new_weight
):
    from kvk.dal import new_source_admin_dal as admin, season_source_dal as seasons
    from tests.test_kvk_source_admin import NOW

    monkeypatch.setattr(seasons, "require_source", lambda *a, **k: {"SeasonState": "open"})
    cursor = Mock()
    answers = iter(
        [
            [{"RosterID": "roster", "B0RevisionID": "b0"}],
            [{"Kingdom": 101, "CampID": 1, "CampName": "North"}],
            [{"GovernorID": 1001, "kingdom": 101, "power": 1}],
        ]
    )
    singles = iter([{"ConfigVersionID": "prior"}, {"n": 2}, None])
    monkeypatch.setattr(admin, "rows", lambda c: next(answers))
    monkeypatch.setattr(admin, "one", lambda c: next(singles))
    spec = dict(
        period_key="fight:pass4",
        label="Pass 4",
        start=12,
        end=18,
        coverage_start="2026-09-05T15:26+00:00",
        coverage_end="2026-09-07T07:21+00:00",
        mapping=[(101, 1, "North")],
        weights=[new_weight, "20", "40", "2026-10-12T10:19:48+00:00"],
    )
    result = admin.SourceAdminDAL(Mock(), Mock()).onboard(
        cursor,
        kvk_no=16,
        proposal=dict(
            configuration=spec, guard=dict(config=None, period=None), receipt_id="receipt"
        ),
        b0_revision_id="b0",
        actor="admin",
        reason="Current weights",
        utc=NOW,
    )
    assert result["state"] == "configuration approved; not published"
    writes = [
        call.args for call in cursor.execute.call_args_list if call.args[0].startswith("INSERT")
    ]
    assert not any("SourceRoster " in call[0] for call in writes)
    weight = next(call for call in writes if "SourceWeightConfig" in call[0])
    assert Decimal(new_weight) in weight
    assert datetime(2026, 10, 12, 10, 19, 48) in weight


def assignment(update):
    return dict(
        reason="Reviewed scan window and independent report coverage",
        period_assignment=dict(
            period_id=update["PeriodID"],
            config_version_id=update["ConfigVersionID"],
            start_scan_id=update["StartScanID"],
            end_scan_id=update["EndScanID"],
            actor=update["ConfirmedBy"],
        ),
    )


@pytest.mark.parametrize("tamper", [None, "actor", "period_id", "end_scan_id"])
def test_confirmed_window_allows_independent_coverage_only_with_exact_authority(tamper):
    from kvk.dal.source_update_dal import validate_update

    update = update_record(
        CoverageStartUTC=datetime(2026, 8, 31), CoverageEndUTC=datetime(2026, 9, 3)
    )
    proof = assignment(update)
    if tamper:
        proof["period_assignment"][tamper] = 99 if tamper == "end_scan_id" else "wrong"
    update["ConfirmationJson"] = json.dumps(proof)
    store = PairStore(update)
    store.config["CoverageEndUTC"] = datetime(2026, 9, 2)
    store.aggregate.update(
        CoverageStartUTC=update["CoverageStartUTC"], CoverageEndUTC=update["CoverageEndUTC"]
    )
    cursor = Cursor(store.route)
    if tamper:
        with pytest.raises(SourceConflict, match="assignment"):
            validate_update(cursor, update)
    else:
        validate_update(cursor, update)


class WeightPlan:
    """Query fixture for the real planner, including interrupted A -> B -> A."""

    def __init__(self, *, desired="a", selected="a", window_changed=False):
        self.desired, self.selected = desired, selected
        self.weights = {
            "a": (Decimal(10), Decimal(20), Decimal(40)),
            "b": (Decimal(99), Decimal(20), Decimal(40)),
        }
        self.config = dict(RosterID="roster", MappingDigest=b"map", StartScanID=12, EndScanID=18)
        self.old_config = dict(self.config, EndScanID=17) if window_changed else self.config
        self.request = (
            None
            if desired == selected
            else dict(DesiredConfigVersionID=desired, ProvenanceJson='{"current_weights":true}')
        )
        self.base = dict(PeriodID="period", ConfigVersionID=selected)
        self.snapshots = []

    def route(self, sql, args):
        if sql.startswith("SELECT PeriodID,PeriodKey"):
            return [dict(PeriodID="period", PeriodKey="fight:pass4")]
        if sql.startswith("SELECT c.RosterID"):
            return [self.old_config if args[0] == self.selected else self.config]
        if sql.startswith("SELECT u.*"):
            return [self.base]
        if sql.startswith("SELECT WeightT4X"):
            return [
                dict(
                    zip(
                        ("WeightT4X", "WeightT5Y", "WeightDeadsZ"),
                        self.weights[args[0]],
                        strict=True,
                    )
                )
            ]
        raise AssertionError(sql)

    def install(self, monkeypatch):
        monkeypatch.setattr(
            dal, "locked_period", lambda *a: (None, None, [self.request] if self.request else [])
        )
        monkeypatch.setattr(dal, "current_config", lambda *a: self.desired)

        def snapshot(cursor, **kwargs):
            self.snapshots.append(kwargs)
            self.desired = "new"
            self.weights["new"] = tuple(Decimal(x) for x in kwargs["current_weights"]["weights"])
            self.request = dict(
                DesiredConfigVersionID="new", ProvenanceJson='{"current_weights":true}'
            )
            return self.request

        monkeypatch.setattr(dal, "snapshot_endpoint_request", snapshot)
        return Cursor(self.route)


@pytest.mark.parametrize(
    "desired,coefficients,window_changed,expected",
    [
        ("a", ("10.0", "20", "40"), False, 0),
        ("a", ("99", "20", "40"), False, 1),
        ("b", ("99", "20", "40"), False, 1),
        ("b", ("10", "20", "40"), False, 1),
        ("b", ("99", "20", "40"), True, 0),
    ],
)
def test_refresh_plan_noop_retry_roundtrip_and_pending_window(
    monkeypatch, desired, coefficients, window_changed, expected
):
    plan = WeightPlan(desired=desired, window_changed=window_changed)
    result = dal.refresh_requests(
        plan.install(monkeypatch), 16, imported(coefficients), datetime(2026, 10, 12)
    )
    assert len(result) == expected
    if desired == "a" and coefficients[0] == "10.0":
        assert plan.snapshots == []


@pytest.mark.parametrize("failure,blocked", [(False, False), (True, False), (False, True)])
def test_multi_period_refresh_is_one_transaction_with_one_final_export(
    monkeypatch, failure, blocked
):
    state = []
    cursor = Mock()
    connection = Mock(autocommit=False)
    connection.cursor.return_value = cursor
    connection.rollback.side_effect = state.clear
    bases = [update_record(PeriodID=uid(n), UpdateID=uid(n + 10)) for n in (2, 3)]
    pending = [
        (b, dict(DesiredConfigVersionID=uid(90 + i), RequestID=uid(80 + i)))
        for i, b in enumerate(bases)
    ]
    monkeypatch.setattr(service, "lock_scope", Mock())
    monkeypatch.setattr(
        service.SourceAdminReviewDAL, "imported_configuration", lambda *a: imported()
    )
    monkeypatch.setattr(service, "refresh_requests", lambda *a: pending)
    monkeypatch.setattr(
        service, "stale_weight_periods", lambda *a: {uid(2), uid(3), *([uid(4)] if blocked else [])}
    )
    monkeypatch.setattr(service, "selected_weights_current", lambda *a: len(state) == 2)

    class Publisher:
        def __init__(self, connect):
            assert connect().cursor() is cursor

        def create(self, context, **kwargs):
            self.context = context
            return dict(UpdateID=context.update_id, Version=1)

        def associate(self, update_id, **kwargs):
            return dict(UpdateID=update_id)

        def publish(self, update_id, *, emit_export_intent):
            if failure and state:
                raise RuntimeError("interrupted second period")
            state.append(emit_export_intent)
            return object()

    monkeypatch.setattr(service, "SourceUpdateService", Publisher)
    if failure or blocked:
        with pytest.raises(RuntimeError if failure else SourceConflict):
            service.refresh_season_weights(lambda: connection, 16, require_current=True)
        assert state == []
        assert connection.rollback.call_count == int(failure)
    else:
        assert service.refresh_season_weights(lambda: connection, 16, require_current=True)
        assert state == [False, True]
        connection.commit.assert_called_once()


def test_export_rejects_any_stale_member_of_the_full_vector(monkeypatch):
    monkeypatch.setattr(
        service.SourceAdminReviewDAL, "imported_configuration", lambda *a: imported()
    )
    monkeypatch.setattr(
        dal,
        "stored_weights",
        lambda c, config: tuple(
            Decimal(x) for x in (("10", "20", "40") if config == "current" else ("99", "20", "40"))
        ),
    )
    dal.require_current_export_weights(Mock(), {"KVK_NO": 16}, [{"ConfigVersionID": "current"}])
    with pytest.raises(SourceConflict, match="current season weights"):
        dal.require_current_export_weights(
            Mock(), {"KVK_NO": 16}, [{"ConfigVersionID": "current"}, {"ConfigVersionID": "stale"}]
        )


def test_repeated_weights_recalculate_from_retained_facts_and_preserve_aggregate():
    from kvk.services.new_source_calculation import calculate_period
    from kvk.services.new_source_window_resolver import resolve_window
    from tests.kvk_source_fixtures import worked_calculation_inputs
    from tests.test_kvk_source_reporting_models import snapshot

    original = snapshot()
    inputs = original.calculation.selection
    b0 = worked_calculation_inputs()[0]
    results = []
    for x in ("10", "99", "10"):
        config = replace(
            inputs.config,
            version_id="config-" + x,
            weights=replace(inputs.config.weights, x_source=x),
        )
        calc = calculate_period(resolve_window(config, (inputs.start, inputs.end)), b0)
        result = replace(original, requested_config=config, calculation=calc)
        assert result.aggregate is original.aggregate
        results.append([(p.metric("dkp"), p.ranks) for p in calc.players])
    assert results[0] == results[2]
    assert results[0] != results[1]


def test_weight_changes_reorder_player_dkp_ranks():
    from kvk.services.new_source_calculation import calculate_period
    from kvk.services.new_source_window_resolver import resolve_window
    from tests.kvk_source_fixtures import calculation_config, calculation_event, player_row

    b0 = calculation_event(1, day=1, rows=[player_row(1001), player_row(1002)])
    start = calculation_event(10, rows=[player_row(1001), player_row(1002)])
    end = calculation_event(
        13, day=7, rows=[player_row(1001, **{"T4 Kills": 10}), player_row(1002, **{"T5 Kills": 6})]
    )
    config = calculation_config()
    before = calculate_period(resolve_window(config, (start, end)), b0)
    changed = replace(config, weights=replace(config.weights, x_source="99"))
    after = calculate_period(resolve_window(changed, (start, end)), b0)
    assert [dict(p.ranks)["dkp"].rank for p in before.players] == [2, 1]
    assert [dict(p.ranks)["dkp"].rank for p in after.players] == [1, 2]
