"""Synthetic sealed-pair contracts and transaction-fault models; no SQL connection."""

from copy import deepcopy
from dataclasses import replace
from datetime import UTC, datetime, timedelta
import json
from unittest.mock import Mock
from uuid import UUID

import pytest

from kvk.dal import source_update_dal as dal
from kvk.dal.new_source_import_dal import SourceConflict, UncertainCommit, transaction
from kvk.models.source_integration import AggregateRevision, PlayerRevisions, UpdateContext
from kvk.services.source_update_service import SourceUpdateService
from tests.test_kvk_season_source import Cursor


def uid(number):
    return str(UUID(int=number))


def update_record(**changes):
    record = dict(
        UpdateID=uid(1),
        SourceKey="snapshot_report_v1",
        KVK_NO=16,
        PeriodID=uid(2),
        PeriodKey="fight:pass4",
        ChoiceID=uid(3),
        ConfigVersionID=uid(4),
        RosterID=uid(5),
        CoverageStartUTC=datetime(2026, 9, 1),
        CoverageEndUTC=datetime(2026, 9, 2),
        AsOfUTC=datetime(2026, 9, 2),
        UpdateKind="fight",
        StartScanID=10,
        EndScanID=11,
        StartRevisionID=uid(10),
        EndRevisionID=uid(11),
        AggregateReportID=uid(20),
        AggregateRevisionID=uid(21),
        BaseUpdateID=None,
        CounterpartRevisionID=None,
        ConfirmedBy="operator",
        ConfirmedUTC=datetime(2026, 9, 2),
        ConfirmationJson="{}",
        RequestID=None,
        Version=3,
        UpdateState="ready",
    )
    record.update(changes)
    record["ContentHash"] = dal.update_hash(record)
    return record


class PairStore:
    def __init__(self, update=None):
        update = update or update_record()
        self.state = dict(
            updates={update["UpdateID"]: update},
            selections={},
            intents={},
            members=[],
            publications={},
        )
        self.config = dict(
            RosterID=uid(5),
            MappingDigest=b"m" * 32,
            B0RevisionID=uid(10),
            StartScanID=10,
            EndScanID=13,
            PeriodKind="fight",
            CoverageStartUTC=datetime(2026, 9, 1),
            CoverageEndUTC=None,
        )
        self.aggregate = dict(
            PeriodKey="fight:pass4",
            PeriodKind="fight",
            SelectedRevisionID=uid(21),
            MappingDigest=b"m" * 32,
            CoverageStartUTC=datetime(2026, 9, 1),
            CoverageEndUTC=datetime(2026, 9, 2),
            AsOfUTC=datetime(2026, 9, 2),
        )
        self.missing_tab = False
        self.wrong_scan = False
        self.stale_revision = False
        self.fail_on = None
        self.commits = 0
        self.lose_ack = False
        self.last_cursor = None

    def route(self, sql, args):
        if self.fail_on and self.fail_on in sql:
            raise RuntimeError("injected transaction failure")
        state = self.state
        if sql.startswith("SELECT TOP (1) PublicationID,PublicSelectionVersion"):
            return [
                dict(
                    PublicationID=r["PublicationID"],
                    PublicSelectionVersion=r["PublicSelectionVersion"],
                )
                for r in state["members"]
                if r["UpdateID"] == args[0]
            ][:1]
        if sql.startswith("SELECT TOP (1) i.IntentID,i.CommitSequence,i.VectorHash"):
            matches = [
                state["intents"][r["IntentID"]]
                for r in state["members"]
                if (r["UpdateID"], r["PublicationID"], r["PublicSelectionVersion"]) == args
            ]
            return sorted(matches, key=lambda r: r["CommitSequence"])[:1]
        if sql.startswith("SET ") or "sp_getapplock" in sql or "SourceScanBinding" in sql:
            return []
        if "SELECT" == sql[:6] and "FROM KVK.SeasonSource" in sql:
            return [
                dict(
                    ChoiceID=uid(3),
                    SourceKey="snapshot_report_v1",
                    SeasonState="open",
                    SeasonVersion=2,
                )
            ]
        if sql.startswith("SELECT c.RosterID"):
            return [deepcopy(self.config)]
        if sql.startswith("SELECT s.LogicalScanID"):
            number = UUID(args[-1]).int
            return [
                dict(
                    LogicalScanID=99 if self.wrong_scan else number,
                    ScanStartUTC=datetime(2026, 9, 1) + timedelta(hours=number),
                    SelectedRevisionID=uid(999) if self.stale_revision else args[-1],
                    MetadataJson=json.dumps(
                        {"scope": {"period_keys": ["fight:pass4", "overall", "no_fight:baseline"]}}
                    ),
                )
            ]
        if sql.startswith("SELECT r.*,f.PeriodKey"):
            return [deepcopy(self.aggregate)]
        if sql.startswith("SELECT COUNT_BIG"):
            return [dict(n=0 if self.missing_tab else 2)]
        if "FROM KVK.SourcePlayerResult" in sql:
            return []
        if (
            "FROM KVK.SourceRouting" in sql
            or "FROM KVK.SourceSelection" in sql
            or "SourceConfigRequest r" in sql
        ):
            return []
        if sql.startswith("SELECT u.* FROM KVK.SourceCompleteSelection"):
            row = state["selections"].get(args[-1])
            return [deepcopy(state["updates"][row["UpdateID"]])] if row else []
        if sql.startswith("SELECT UpdateID FROM KVK.SourceCompleteSelection"):
            row = state["selections"].get(args[-1])
            return [dict(UpdateID=row["UpdateID"])] if row else []
        if sql.startswith("SELECT * FROM KVK.SourceCompleteSelection"):
            return [deepcopy(v) for _, v in sorted(state["selections"].items())]
        if sql.startswith("SELECT * FROM KVK.SourceUpdate"):
            if "ContentHash=?" in sql:
                return [
                    deepcopy(v)
                    for v in state["updates"].values()
                    if v["ContentHash"] == args[3] and v["UpdateState"] in ("ready", "selected")
                ]
            row = state["updates"].get(args[0])
            return [deepcopy(row)] if row else []
        if sql.startswith("UPDATE KVK.SourceUpdate SET StartScanID"):
            row = state["updates"][args[-2]]
            if row["Version"] != args[-1]:
                return []
            row.update(
                dict(
                    zip(
                        (*dal.INPUT_COLUMNS, "CounterpartRevisionID", "ContentHash", "UpdateState"),
                        args[:-2],
                        strict=True,
                    )
                )
            )
            row["Version"] += 1
            return [deepcopy(row)]
        if sql.startswith("SELECT * FROM KVK.SourcePublication"):
            return [deepcopy(state["publications"][args[0]])]
        if sql.startswith("UPDATE KVK.SourceCompleteSelection"):
            update, pub, _, _, period, version = args
            row = state["selections"][period]
            if row["PublicSelectionVersion"] != version:
                return []
            row.update(UpdateID=update, PublicationID=pub, PublicSelectionVersion=version + 1)
            return [dict(PublicSelectionVersion=version + 1)]
        if sql.startswith("INSERT KVK.SourceCompleteSelection"):
            source, season, period, update, pub = args
            state["selections"][period] = dict(
                SourceKey=source,
                KVK_NO=season,
                PeriodID=period,
                UpdateID=update,
                PublicationID=pub,
                PublicSelectionVersion=1,
            )
            return []
        if sql.startswith("UPDATE KVK.SourceUpdate SET UpdateState"):
            row = state["updates"][args[0]]
            if row["Version"] != args[1]:
                return []
            row.update(UpdateState="selected", Version=row["Version"] + 1)
            return [dict(Version=row["Version"])]
        if sql.startswith("SELECT s.PeriodID,s.UpdateID"):
            return [
                dict(
                    PeriodID=s["PeriodID"],
                    UpdateID=s["UpdateID"],
                    PublicationID=s["PublicationID"],
                    PublicSelectionVersion=s["PublicSelectionVersion"],
                    ConfigVersionID=state["updates"][s["UpdateID"]]["ConfigVersionID"],
                    ManifestHash=state["publications"][s["PublicationID"]]["ManifestHash"],
                )
                for _, s in sorted(state["selections"].items())
            ]
        if sql.startswith("SELECT * FROM KVK.SourceExportIntent"):
            return [deepcopy(i) for i in state["intents"].values() if i["VectorHash"] == args[2]]
        if sql.startswith("SELECT ISNULL(MAX(CommitSequence)"):
            return [dict(n=len(state["intents"]) + 1)]
        if sql.startswith("INSERT KVK.SourceExportIntent ("):
            ident, source, season, choice, sequence, vector_hash, schema = args
            state["intents"][ident] = dict(
                IntentID=ident,
                SourceKey=source,
                KVK_NO=season,
                ChoiceID=choice,
                CommitSequence=sequence,
                VectorHash=vector_hash,
                ExportSchemaVersion=schema,
                IntentState="waiting_destination",
            )
            return []
        if sql.startswith("INSERT KVK.SourceExportIntentPublication"):
            state["members"].append(
                dict(
                    zip(
                        (
                            "IntentID",
                            "PeriodID",
                            "SourceKey",
                            "KVK_NO",
                            "UpdateID",
                            "PublicationID",
                            "PublicSelectionVersion",
                            "ConfigVersionID",
                        ),
                        args,
                        strict=True,
                    )
                )
            )
            return []
        if sql.startswith(
            "SELECT PeriodID,UpdateID,PublicationID,PublicSelectionVersion,ConfigVersionID FROM KVK.SourceExportIntentPublication"
        ):
            return [
                {
                    k: row[k]
                    for k in (
                        "PeriodID",
                        "UpdateID",
                        "PublicationID",
                        "PublicSelectionVersion",
                        "ConfigVersionID",
                    )
                }
                for row in sorted(state["members"], key=lambda r: r["PeriodID"])
                if row["IntentID"] == args[0]
            ]
        raise AssertionError("Unexpected SQL in offline model: " + sql)

    def connect(self):
        store, before = self, deepcopy(self.state)

        class Connection:
            autocommit = False

            def cursor(self):
                store.last_cursor = Cursor(store.route)
                return store.last_cursor

            def commit(self):
                store.commits += 1
                if store.lose_ack:
                    store.lose_ack = False
                    raise OSError("lost commit acknowledgement")

            def rollback(self):
                store.state = before

            def close(self):
                pass

        return Connection()


@pytest.mark.parametrize("aggregate_first", [False, True])
def test_both_orders_wait_then_seal_and_replay_without_generation(aggregate_first):
    waiting = update_record(
        **dict.fromkeys(dal.INPUT_COLUMNS), UpdateState="waiting_player", Version=1
    )
    store = PairStore(waiting)
    service = dal.SourceUpdateDAL(store.connect)
    player = dict(player=PlayerRevisions(10, 11, uid(10), uid(11)))
    aggregate = dict(aggregate=AggregateRevision(uid(20), uid(21)))
    first, second = (aggregate, player) if aggregate_first else (player, aggregate)
    partial = service.associate(uid(1), expected_version=1, authorized=True, **first)
    assert partial["UpdateState"] == ("waiting_player" if aggregate_first else "waiting_aggregate")
    assert not store.state["selections"] and not store.state["intents"]
    sealed = service.associate(uid(1), expected_version=2, authorized=True, **second)
    assert sealed["UpdateState"] == "ready"
    assert service.associate(uid(1), expected_version=2, authorized=True, **second) == sealed
    assert not store.state["publications"] and not store.state["intents"]


@pytest.mark.parametrize("fault", ["wrong_scan", "stale_revision", "missing_tab"])
def test_binding_and_both_tab_failures_preserve_accepted_update(fault):
    record = update_record()
    store = PairStore(record)
    setattr(store, fault, True)
    before = deepcopy(store.state)
    with pytest.raises(SourceConflict):
        dal.validate_update(Cursor(store.route), record, complete=True)
    assert store.state == before


@pytest.mark.parametrize(
    "key,value",
    [
        ("RosterID", uid(999)),
        ("PeriodKey", "fight:other"),
        ("CoverageStartUTC", datetime(2026, 8, 1)),
        ("AsOfUTC", datetime(2026, 9, 3)),
        ("UpdateKind", "overall"),
    ],
)
def test_wrong_context_is_rejected(key, value):
    store = PairStore()
    with pytest.raises(SourceConflict):
        dal.validate_update(Cursor(store.route), update_record(**{key: value}), complete=True)


def test_sealed_inputs_and_stale_cas_cannot_be_replaced():
    store = PairStore()
    service = dal.SourceUpdateDAL(store.connect)
    with pytest.raises(SourceConflict, match=r"sealed|CAS"):
        service.associate(
            uid(1),
            expected_version=3,
            player=PlayerRevisions(10, 12, uid(10), uid(12)),
            authorized=True,
        )
    waiting = update_record(
        **dict.fromkeys(dal.INPUT_COLUMNS), UpdateState="waiting_player", Version=2
    )
    store.state["updates"][uid(1)] = waiting
    with pytest.raises(SourceConflict, match="CAS"):
        service.associate(
            uid(1),
            expected_version=1,
            player=PlayerRevisions(10, 11, uid(10), uid(11)),
            authorized=True,
        )


@pytest.mark.parametrize(
    "period_kind,period_key", [("no_fight", "no_fight:baseline"), ("fight", "fight:pass4")]
)
def test_typed_no_fight_does_not_need_fabricated_aggregate(period_kind, period_key):
    record = update_record(
        UpdateKind="no_fight",
        PeriodKey=period_key,
        PeriodKind=period_kind,
        EndScanID=10,
        EndRevisionID=uid(10),
        AggregateReportID=None,
        AggregateRevisionID=None,
    )
    store = PairStore(record)
    store.config.update(PeriodKind=period_kind, EndScanID=10)
    assert dal.validate_update(Cursor(store.route), record, complete=True) == period_kind


@pytest.mark.parametrize(
    "fault", ["overall", "classification", "unequal_config", "open_config", "revision", "aggregate"]
)
def test_no_fight_exception_rejects_incompatible_context(fault):
    record = update_record(
        UpdateKind="no_fight",
        PeriodKind="fight",
        EndScanID=10,
        EndRevisionID=uid(10),
        AggregateReportID=None,
        AggregateRevisionID=None,
    )
    store = PairStore(record)
    store.config["EndScanID"] = 10
    if fault == "overall":
        store.config["PeriodKind"] = record["PeriodKind"] = "overall"
    elif fault == "classification":
        record["PeriodKind"] = "no_fight"
    elif fault in ("unequal_config", "open_config"):
        store.config["EndScanID"] = 11 if fault == "unequal_config" else None
    elif fault == "revision":
        record["EndRevisionID"] = uid(11)
    else:
        record.update(AggregateReportID=uid(20), AggregateRevisionID=uid(21))
    with pytest.raises(SourceConflict):
        dal.validate_update(Cursor(store.route), record, complete=True)


def test_explicit_no_fight_association_seals_existing_fight_without_retagging():
    record = update_record(
        **dict.fromkeys(dal.INPUT_COLUMNS),
        UpdateKind="no_fight",
        PeriodKind="fight",
        UpdateState="waiting_player",
        Version=1,
    )
    store = PairStore(record)
    store.config["EndScanID"] = 10
    service = dal.SourceUpdateDAL(store.connect)
    result = service.associate(
        uid(1),
        expected_version=1,
        authorized=True,
        player=PlayerRevisions(10, 10, uid(10), uid(10)),
    )
    assert result["UpdateState"] == "ready"
    assert (result["PeriodKind"], result["PeriodKey"], result["UpdateKind"]) == (
        "fight",
        "fight:pass4",
        "no_fight",
    )
    assert result["AggregateRevisionID"] is None
    assert (
        service.associate(
            uid(1),
            expected_version=1,
            authorized=True,
            player=PlayerRevisions(10, 10, uid(10), uid(10)),
        )
        == result
    )
    assert not store.state["selections"] and not store.state["intents"]


def test_reused_aggregate_requires_exact_counterpart_confirmation():
    prior = update_record(UpdateID=uid(100))
    record = update_record(EndScanID=12, EndRevisionID=uid(12), BaseUpdateID=uid(100))
    store = PairStore(record)
    store.state["updates"][uid(100)] = prior
    store.state["selections"][uid(2)] = dict(UpdateID=uid(100))
    with pytest.raises(SourceConflict, match="counterpart"):
        dal.validate_update(Cursor(store.route), record, complete=True)
    record.update(BaseUpdateID=uid(100), CounterpartRevisionID=uid(21))
    confirmation = dict(
        base_update_id=uid(100),
        revision_id=uid(21),
        config_version_id=uid(4),
        roster_id=uid(5),
        coverage_start_utc=record["CoverageStartUTC"].isoformat(),
        coverage_end_utc=record["CoverageEndUTC"].isoformat(),
        as_of_utc=record["AsOfUTC"].isoformat(),
        actor="operator",
    )
    record["ConfirmationJson"] = json.dumps(dict(counterpart=confirmation))
    dal.validate_update(Cursor(store.route), record, complete=True)
    record["AsOfUTC"] += timedelta(seconds=1)
    with pytest.raises(SourceConflict, match="confirmation"):
        dal.validate_update(Cursor(store.route), record, complete=True)


def seed_publication(store, update, pub_id):
    store.state["publications"][pub_id] = dict(
        **{k: update[k] for k in (*dal.INPUT_COLUMNS, "ConfigVersionID", "RosterID")},
        BuildState="complete",
        EligibleCount=0,
        ResultCount=0,
        ManifestHash=dal.digest([]),
    )


@pytest.mark.parametrize(
    "fault", ["INSERT KVK.SourceExportIntent (", "INSERT KVK.SourceExportIntentPublication", None]
)
def test_pointer_and_full_vector_are_atomic_and_preserve_unchanged_period(fault):
    record = update_record()
    store = PairStore(record)
    seed_publication(store, record, uid(30))
    prior = update_record(UpdateID=uid(100), PeriodID=uid(200), UpdateState="selected")
    store.state["updates"][uid(100)] = prior
    seed_publication(store, prior, uid(300))
    store.state["selections"][uid(200)] = dict(
        PeriodID=uid(200), UpdateID=uid(100), PublicationID=uid(300), PublicSelectionVersion=7
    )
    before = deepcopy(store.state)
    store.fail_on = fault

    def commit():
        with transaction(store.connect) as cursor:
            return dal.commit_complete(
                cursor,
                update=record,
                publication_id=uid(30),
                expected_public_version=0,
                expected_update_version=3,
            )

    if fault:
        with pytest.raises(RuntimeError, match="injected"):
            commit()
        assert store.state == before
    else:
        result = commit()
        members = store.state["members"]
        assert len(members) == 2 and {r["PeriodID"] for r in members} == {uid(2), uid(200)}
        assert next(r for r in members if r["PeriodID"] == uid(200))["PublicSelectionVersion"] == 7
        assert store.state["intents"][result.intent_id]["IntentState"] == "waiting_destination"
        assert result.public_selection_version == 1


def test_waiting_and_selected_restart_paths_do_not_rebuild_or_import():
    service = SourceUpdateService(Mock())
    service.dal, service.inputs, service.publisher = Mock(), Mock(), Mock()
    service.dal.resume_endpoint.return_value = update_record(UpdateState="waiting_aggregate")
    assert service.publish(uid(1)) is None
    service.publisher.build_candidate.assert_not_called()
    service.dal.resume_endpoint.return_value = update_record(UpdateState="selected")
    assert service.publish(uid(1)) is service.dal.selected_result.return_value
    service.inputs.load_inputs.assert_not_called()


def test_context_requires_real_ids_bounded_actor_and_utc():
    context = UpdateContext(
        uid(1),
        16,
        uid(2),
        "fight:pass4",
        uid(3),
        uid(4),
        uid(5),
        datetime(2026, 9, 1, tzinfo=UTC),
        datetime(2026, 9, 2, tzinfo=UTC),
        datetime(2026, 9, 2, tzinfo=UTC),
        "fight",
        "operator",
        datetime(2026, 9, 2, tzinfo=UTC),
        "{}",
    )
    with pytest.raises(ValueError):
        replace(context, update_id="filename.xlsx")
    with pytest.raises(ValueError):
        replace(context, confirmed_utc=datetime(2026, 9, 2))
    connect = Mock()
    with pytest.raises(PermissionError):
        dal.SourceUpdateDAL(connect).create(context, authorized=False)
    connect.assert_not_called()


def test_exact_interims_final_and_authorized_pending_14_without_second_correction():
    from kvk.models.new_source_reporting import AggregateSelection
    from kvk.services.new_source_parser import parse_aggregate_workbook
    from kvk.services.new_source_publication_service import PublicationService
    from tests.kvk_source_fixtures import (
        MAPPING,
        aggregate_bytes,
        calculation_config,
        metadata,
        worked_calculation_inputs,
    )

    b0, start, eleven, thirteen = worked_calculation_inputs()

    def event(original, number, delta):
        observation = original.observation
        return replace(
            original,
            logical_scan_id=number,
            observation_id=uid(1000 + number),
            revision_id=uid(number),
            observation=replace(
                observation,
                metadata=replace(
                    observation.metadata,
                    candidate=replace(
                        observation.metadata.candidate,
                        scan_start_utc=original.scan_start_utc + delta,
                    ),
                ),
            ),
        )

    start, eleven, thirteen = (
        event(start, 10, timedelta()),
        event(eleven, 11, timedelta()),
        event(thirteen, 13, timedelta()),
    )
    twelve, fourteen = event(eleven, 12, timedelta(hours=12)), event(
        thirteen, 14, timedelta(days=1)
    )
    config = replace(calculation_config(), period_id=uid(2))
    aggregate = AggregateSelection(
        uid(20),
        uid(21),
        parse_aggregate_workbook(aggregate_bytes(), metadata(aggregate=True), MAPPING),
    )
    data = dict(
        config=config,
        observations=(start, eleven),
        b0=b0,
        previous=None,
        aggregate=aggregate,
        request=None,
        requests=[],
        selected=None,
        routing=None,
        season_version=2,
        public_version=0,
    )
    service = SourceUpdateService(Mock())
    service.dal, service.inputs = Mock(), Mock()
    service.publisher = PublicationService(Mock())
    service.publisher.dal = Mock()
    service.publisher.dal.build_candidate.return_value = {"Generation": 1}
    service.inputs.load_inputs.return_value = data
    snapshots = []

    def select(**kwargs):
        snapshot = service.publisher.dal.build_candidate.call_args.args[0]
        snapshots.append(snapshot)
        data.update(
            selected=dict(PublicationID=snapshot.publication_id, SelectionVersion=len(snapshots)),
            previous=snapshot.calculation.selection,
            public_version=len(snapshots),
        )
        return {"complete": snapshot.publication_id}

    service.publisher.dal.select_publication.side_effect = select
    for endpoint in (eleven, twelve, thirteen):
        data["observations"] = (start, endpoint)
        service.dal.resume_endpoint.return_value = update_record(
            UpdateID=uid(100 + endpoint.logical_scan_id),
            EndScanID=endpoint.logical_scan_id,
            EndRevisionID=endpoint.revision_id,
        )
        service.publish(uid(100 + endpoint.logical_scan_id))
    assert [
        (s.calculation.selection.end.logical_scan_id, s.player_state.value) for s in snapshots
    ] == [(11, "live"), (12, "live"), (13, "final")]
    request = dict(
        RequestID=uid(99),
        SourceKey="snapshot_report_v1",
        KVK_NO=config.kvk_no,
        PeriodID=uid(2),
        BaseConfigVersionID=config.version_id,
        DesiredConfigVersionID="desired-14",
        OldStartScanID=10,
        NewStartScanID=10,
        OldEndScanID=13,
        NewEndScanID=14,
        Actor="operator",
        Reason="authorized endpoint",
        RequestState="pending",
    )
    data.update(
        config=replace(config, version_id="desired-14", end_scan_id=14),
        request=request,
        requests=[request],
    )
    service.dal.resume_endpoint.return_value = update_record(
        UpdateState="waiting_player", RequestID=uid(99)
    )
    assert service.publish(uid(114)) is None and len(snapshots) == 3
    assert snapshots[-1].requested_config.version_id != data["config"].version_id
    data["observations"] = (start, thirteen, fourteen)
    service.dal.resume_endpoint.return_value = update_record(
        UpdateID=uid(114), RequestID=uid(99), EndScanID=14, EndRevisionID=uid(14)
    )
    service.publish(uid(114))
    assert snapshots[-1].calculation.selection.end.logical_scan_id == 14
    assert snapshots[-1].player_state.value == "corrected_final"
    assert (
        service.publisher.dal.select_publication.call_args.kwargs["action_type"]
        == "endpoint_update"
    )
    assert all(s.aggregate is aggregate for s in snapshots)


def test_older_ready_update_cannot_regress_selected_endpoint():
    store = PairStore()
    prior = update_record(
        UpdateID=uid(90), EndScanID=12, EndRevisionID=uid(12), UpdateState="selected"
    )
    store.state["updates"][prior["UpdateID"]] = prior
    store.state["selections"][uid(2)] = dict(UpdateID=prior["UpdateID"])
    with pytest.raises(SourceConflict, match="base CAS"):
        dal.validate_update(Cursor(store.route), update_record(), complete=True)


@pytest.mark.parametrize(
    "changed", [None, "RosterID", "MappingDigest", "WeightDigest", "StartScanID"]
)
def test_display_configuration_reuses_exact_inputs_and_rejects_numerical_changes(changed):
    prior = update_record(UpdateID=uid(90), UpdateState="selected")
    new = update_record(
        ConfigVersionID=uid(91), BaseUpdateID=uid(90), CounterpartRevisionID=uid(21)
    )
    confirmation = dict(
        base_update_id=uid(90),
        revision_id=uid(21),
        config_version_id=uid(91),
        roster_id=uid(5),
        coverage_start_utc=new["CoverageStartUTC"].isoformat(),
        coverage_end_utc=new["CoverageEndUTC"].isoformat(),
        as_of_utc=new["AsOfUTC"].isoformat(),
        actor="operator",
    )
    new["ConfirmationJson"] = json.dumps(dict(action="configure", counterpart=confirmation))
    store = PairStore(new)
    store.state["updates"][uid(90)] = prior
    store.state["selections"][uid(2)] = dict(UpdateID=uid(90))
    old_config = dict(
        ConfigVersionID=uid(4),
        ConfigVersion=1,
        RosterID=uid(5),
        MappingDigest=b"m" * 32,
        WeightDigest=b"w" * 32,
        StartScanID=10,
        EndScanID=13,
        WindowName="Old",
    )
    new_config = dict(
        old_config, ConfigVersionID=uid(91), ConfigVersion=2, WindowName="Reviewed name"
    )
    if changed:
        new_config[changed] = "different"

    def route(sql, args):
        if sql.startswith("SELECT c.ConfigVersionID,c.ConfigVersion"):
            return [old_config, new_config]
        return store.route(sql, args)

    if changed:
        with pytest.raises(SourceConflict, match="Display-only"):
            dal.validate_update(Cursor(route), new, complete=True)
    else:
        dal.validate_update(Cursor(route), new, complete=True)


def test_tampered_unchanged_period_hash_rolls_back_complete_pointer():
    record = update_record()
    store = PairStore(record)
    seed_publication(store, record, uid(30))
    store.state["publications"][uid(30)]["ManifestHash"] = b"x" * 32
    before = deepcopy(store.state)
    with pytest.raises(SourceConflict, match="invalid sealed"):
        with transaction(store.connect) as cursor:
            dal.commit_complete(
                cursor,
                update=record,
                publication_id=uid(30),
                expected_public_version=0,
                expected_update_version=3,
            )
    assert store.state == before


@pytest.mark.parametrize("stream", ["player", "aggregate"])
def test_sealed_pair_survives_later_unmatched_revision_but_new_association_does_not(stream):
    store = PairStore()
    if stream == "player":
        store.stale_revision = True
    else:
        store.aggregate["SelectedRevisionID"] = uid(999)
    with pytest.raises(SourceConflict, match="stale"):
        dal.validate_update(Cursor(store.route), update_record(), complete=True)
    dal.validate_update(Cursor(store.route), update_record(), complete=True, sealed=True)


def test_sealed_successor_cannot_rebase_after_another_pair_wins():
    store = PairStore()
    prior = update_record(
        UpdateID=uid(90),
        EndScanID=12,
        EndRevisionID=uid(12),
        AggregateRevisionID=uid(99),
        UpdateState="selected",
    )
    store.state["updates"][uid(90)] = prior
    store.state["selections"][uid(2)] = dict(UpdateID=uid(90))
    # Both streams differ; this still requires the persisted complete base.
    with pytest.raises(SourceConflict, match="base CAS"):
        dal.validate_update(Cursor(store.route), update_record(), complete=True, sealed=True)


def test_complete_commit_lost_ack_restart_reads_same_intent_without_replay():
    record = update_record()
    store = PairStore(record)
    seed_publication(store, record, uid(30))
    store.lose_ack = True
    with pytest.raises(UncertainCommit):
        with transaction(store.connect) as cursor:
            dal.commit_complete(
                cursor,
                update=record,
                publication_id=uid(30),
                expected_public_version=0,
                expected_update_version=3,
            )
    assert store.state["updates"][uid(1)]["UpdateState"] == "selected"
    result = dal.SourceUpdateDAL(store.connect).selected_result(uid(1))
    assert result.publication_id == uid(30) and result.commit_sequence == 1
    assert len(store.state["intents"]) == 1
