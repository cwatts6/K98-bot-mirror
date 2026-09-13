"""Opt-in synthetic SQL integration; no default server or production connection."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, replace
from datetime import UTC, datetime, timedelta
import os
from pathlib import Path
import tempfile
from threading import Event
from uuid import uuid4

import pytest

from kvk.dal.new_source_config_dal import snapshot_endpoint_request
from kvk.dal.new_source_import_dal import (
    Admission,
    SourceConflict,
    SourceImportDAL,
    UncertainCommit,
    digest,
    transaction,
)
from kvk.dal.new_source_reporting_dal import load_snapshot
from kvk.models.new_source_reporting import (
    EndpointChange,
    FrozenWeights,
    ObservationInput,
    PeriodKind,
    WindowConfig,
)
from kvk.schemas.new_source_schema import SOURCE_KEY
from kvk.services.new_source_artifact_store import ArtifactStore
from kvk.services.new_source_parser import parse_player_workbook
from kvk.services.new_source_publication_service import PublicationService
from tests.kvk_source_fixtures import MAPPING, metadata, player_bytes, player_row, rewrite_zip


@pytest.fixture
def database(tmp_path):
    server = os.environ.get("KVK_S8B_SQL_SERVER")
    name = os.environ.get("KVK_S8B_SQL_DATABASE")
    if os.environ.get("KVK_S8B_SQL_ENABLE") != "1":
        pytest.skip("Separate S8B disposable SQL execution approval required.")
    if (
        server not in (r"9SX2VF4\K98DEV", r"localhost\K98DEV")
        or not name
        or not name.startswith("K98_S8B_Disposable_")
        or not name.replace("_", "").isalnum()
        or os.environ.get("KVK_S8B_SQL_APPROVED_TARGET") != f"{server}|{name}"
    ):
        pytest.fail("Refusing an unapproved S8B SQL target.")
    import pyodbc

    def connect():
        conn = pyodbc.connect(
            "DRIVER={ODBC Driver 17 for SQL Server};SERVER=lpc:"
            + server
            + ";DATABASE="
            + name
            + ";Trusted_Connection=yes;TrustServerCertificate=yes",
            autocommit=False,
            timeout=10,
        )
        cursor = conn.cursor()
        cursor.execute("SELECT CONVERT(nvarchar(128),SERVERPROPERTY('ServerName')),DB_NAME()")
        actual = cursor.fetchone()
        if tuple(actual) != (r"9SX2VF4\K98DEV", name):
            conn.close()
            pytest.fail("Connected SQL target differs from authorization.")
        conn.rollback()
        return conn

    # Each test owns a distinct synthetic season; committed evidence remains in the separately approved S8B database.
    season = 1000000 + int(uuid4().hex[:7], 16)
    store = ArtifactStore(Path(tempfile.mkdtemp(prefix="k98-s8b-originals-")))
    from kvk.services.season_source_service import SeasonSourceService

    choices = SeasonSourceService(connect)
    choices.choose(
        season,
        SOURCE_KEY,
        actor="synthetic",
        reason="S8B fixture",
        provenance={"test": "S8B"},
        authorized=True,
    )
    choices.transition(
        season, "open", expected_version=1, actor="synthetic", reason="S8B fixture", authorized=True
    )
    return connect, season, store


def observation(season, number, store, *, value=None):
    original = metadata()
    candidate = replace(
        original.candidate,
        kvk_no=season,
        scan_start_utc=datetime(2000, 1, 1, tzinfo=UTC) + timedelta(days=number),
    )
    meta = replace(original, candidate=candidate, scope=replace(original.scope, kvk_no=season))
    content = player_bytes(
        [
            player_row(
                1001,
                101,
                **{"T4 Kills": value or number * 10, "Name": f"Synthetic season {season}"},
            ),
            player_row(1002, 102),
        ]
    )
    prepared = parse_player_workbook(content, meta)
    return prepared, store.persist_artifact(content)


def admission(key=None, **changes):
    return Admission(
        "synthetic-guild",
        key or uuid4().hex,
        "synthetic-attachment",
        "accept",
        "synthetic-operator",
        "synthetic-channel",
        "synthetic S8B validation",
        datetime.now(UTC).replace(microsecond=0),
        **changes,
    )


def accepted_event(dal, season, number, store):
    prepared, artifact = observation(season, number, store)
    accepted = dal.accept_observation(prepared, artifact, admission())
    return ObservationInput(
        accepted.logical_scan_id,
        accepted.identity_id,
        accepted.revision_id,
        prepared,
        ("fight:pass4", "overall"),
    )


def seed_config(
    connect,
    season,
    b0,
    *,
    start=1,
    end=3,
    sequence=1,
    period_key="fight:pass4",
    period_kind=PeriodKind.FIGHT,
):
    config_id, roster_id, period_id = (str(uuid4()) for _ in range(3))
    utc = datetime(2000, 1, 1)
    h = digest({"synthetic": season})
    with transaction(connect) as cur:
        cur.execute(
            "INSERT KVK.SourceRoster (RosterID,SourceKey,KVK_NO,RosterVersion,B0RevisionID,ScopeDigest,MemberDigest,MemberCount,ApprovedUTC,ApprovedBy,Reason,ProvenanceJson) VALUES (?,?,?,?,?,?,?,?,?,'synthetic','fixture','{}')",
            roster_id,
            SOURCE_KEY,
            season,
            sequence,
            b0.revision_id,
            h,
            h,
            2,
            utc,
        )
        for gov, kingdom in ((1001, 101), (1002, 102)):
            cur.execute(
                "INSERT KVK.SourceRosterMember VALUES (?,?,?,?,?,?)",
                roster_id,
                SOURCE_KEY,
                season,
                gov,
                kingdom,
                1,
            )
        cur.execute(
            "INSERT KVK.SourcePeriod VALUES (?,?,?,?,?,?,?,?)",
            period_id,
            SOURCE_KEY,
            season,
            period_key,
            period_kind.value,
            b0.scan_start_utc.replace(tzinfo=None),
            None,
            utc,
        )
        cur.execute(
            "INSERT KVK.SourceConfigVersion VALUES (?,?,?,?,?,?,?,?,?,?,'synthetic','fixture','{}')",
            config_id,
            SOURCE_KEY,
            season,
            sequence,
            roster_id,
            h,
            h,
            digest(asdict(MAPPING)),
            h,
            utc,
        )
        cur.execute(
            "INSERT KVK.SourceWindowConfig VALUES (?,?,?,'Fight',1,?,?,NULL,?,?)",
            config_id,
            SOURCE_KEY,
            season,
            start,
            end,
            utc,
            period_key,
        )
        for kingdom, camp, name in MAPPING.entries:
            cur.execute(
                "INSERT KVK.SourceCampConfig VALUES (?,?,?,?,?,?,?)",
                config_id,
                SOURCE_KEY,
                season,
                kingdom,
                camp,
                name,
                name.casefold(),
            )
        cur.execute(
            "INSERT KVK.SourceWeightConfig VALUES (?,?,?,10,20,40,'10','20','40',?)",
            config_id,
            SOURCE_KEY,
            season,
            utc,
        )
        cur.execute("INSERT KVK.SourceScanBinding VALUES (?,?,?,1)", config_id, SOURCE_KEY, season)
        cur.execute(
            "IF NOT EXISTS (SELECT 1 FROM KVK.SourceRouting WHERE SourceKey=? AND KVK_NO=?) INSERT KVK.SourceRouting (SourceKey,KVK_NO,RoutingVersion) VALUES (?,?,1)",
            SOURCE_KEY,
            season,
            SOURCE_KEY,
            season,
        )
    return WindowConfig(
        config_id,
        season,
        period_id,
        period_key,
        period_kind,
        "Fight",
        start,
        end,
        roster_id,
        b0.revision_id,
        "synthetic-map",
        MAPPING,
        FrozenWeights("synthetic-weights", "10", "20", "40", utc.replace(tzinfo=UTC)),
    )


def test_two_connection_duplicate_allocation_and_chronology(database):
    connect, season, store = database
    dal = SourceImportDAL(connect, store)
    prepared, artifact = observation(season, 1, store)
    with ThreadPoolExecutor(2) as pool:
        results = list(
            pool.map(lambda _: dal.accept_observation(prepared, artifact, admission()), range(2))
        )
    assert {r.logical_scan_id for r in results} == {1}
    assert len({r.revision_id for r in results}) == 1
    assert sorted(r.duplicate for r in results) == [False, True]
    # ZIP-only re-export remains the same accepted scan.
    alias = store.persist_artifact(rewrite_zip(store.read(artifact)))
    parsed = parse_player_workbook(store.read(alias), prepared.metadata)
    assert dal.accept_observation(parsed, alias, admission()).duplicate
    second = accepted_event(dal, season, 2, store)
    assert second.logical_scan_id == 2
    older, older_artifact = observation(season, 0, store, value=99)
    with pytest.raises(SourceConflict, match="oldest first"):
        dal.accept_observation(older, older_artifact, admission())
    with transaction(connect) as cur:
        cur.execute("SELECT COUNT(*) FROM KVK.SourceLogicalScan WHERE KVK_NO=?", season)
        assert cur.fetchone()[0] == 2


def test_candidate_visibility_cas_endpoint_request_and_restart(database):
    connect, season, store = database
    dal = SourceImportDAL(connect, store)
    b0 = accepted_event(dal, season, 1, store)
    config = seed_config(connect, season, b0)
    middle = accepted_event(dal, season, 2, store)
    service = PublicationService(connect)
    first = service.build_candidate(config=config, observations=(b0, middle), b0=b0)
    assert load_snapshot(connect, kvk_no=season, period_id=config.period_id)["publication"] is None
    second = service.build_candidate(config=config, observations=(b0, middle), b0=b0)

    def select(candidate):
        try:
            return service.select_publication(
                candidate,
                action_id=str(uuid4()),
                expected_selection_version=0,
                expected_routing_version=1,
                actor="synthetic",
                reason="CAS fixture",
                destinations=(),
            )
        except SourceConflict:
            return None

    with ThreadPoolExecutor(2) as pool:
        selected = list(pool.map(select, (first, second)))
    assert sum(r is not None for r in selected) == 1
    current = load_snapshot(connect, kvk_no=season, period_id=config.period_id)
    assert current["selection"]["SelectionVersion"] == 1
    with transaction(connect) as cur:
        cur.execute("BEGIN TRANSACTION")
        request = snapshot_endpoint_request(
            cur,
            kvk_no=season,
            period_id=config.period_id,
            base_config_id=config.version_id,
            new_end_scan_id=4,
            actor="synthetic",
            reason="authorized endpoint",
            requested_utc=datetime.now(UTC).replace(microsecond=0),
            origin="authorized_import",
            provenance={"synthetic": True},
        )
        cur.execute("COMMIT TRANSACTION")
    stale = load_snapshot(connect, kvk_no=season, period_id=config.period_id)
    assert not stale["is_current"] and stale["current_period_state"] == "missing_configuration"
    assert stale["pending_request"]["NewEndScanID"] == 4
    assert str(request["BaseConfigVersionID"]) == config.version_id


class CommitFault:
    def __init__(self, connection, *, after):
        self.connection, self.after = connection, after

    def __getattr__(self, name):
        return getattr(self.connection, name)

    def commit(self):
        if self.after:
            self.connection.commit()
        raise OSError("synthetic commit acknowledgement failure")


@pytest.mark.parametrize("after", [False, True])
def test_uncertain_commit_durable_readback_without_write_replay(database, after):
    connect, season, store = database
    prepared, artifact = observation(season, 1, store)
    key = admission()
    dal = SourceImportDAL(lambda: CommitFault(connect(), after=after), store)
    with pytest.raises(UncertainCommit):
        dal.accept_observation(prepared, artifact, key)
    recovery = SourceImportDAL(connect, store)
    outcome = recovery.read_outcome(key)
    assert (outcome is not None) == after
    accepted = recovery.accept_observation(prepared, artifact, key)
    assert accepted.logical_scan_id == 1 and accepted.duplicate == after


def test_t68_t69_t70_exact_11_10_to_14_10(database):
    connect, season, store = database
    dal = SourceImportDAL(connect, store)
    events = [accepted_event(dal, season, n, store) for n in range(1, 12)]
    b0 = events[0]
    config = seed_config(connect, season, b0, start=10, end=13)
    service = PublicationService(connect)
    for version, end in enumerate((11, 12, 13), 1):
        if end > 11:
            events.append(accepted_event(dal, season, end, store))
        candidate = service.build_candidate(config=config, observations=tuple(events), b0=b0)
        assert candidate.snapshot.calculation.selection.start.logical_scan_id == 10
        assert candidate.snapshot.calculation.selection.end.logical_scan_id == end
        service.select_publication(
            candidate,
            action_id=str(uuid4()),
            expected_selection_version=version - 1,
            expected_routing_version=1,
            actor="synthetic",
            reason="ordered progression",
        )
    assert candidate.snapshot.player_state.value == "final"
    prior = candidate.snapshot.calculation.selection
    # A caller rollback must roll back its request and cloned config too.
    conn = connect()
    cur = conn.cursor()
    cur.execute("BEGIN TRANSACTION")
    args = dict(
        kvk_no=season,
        period_id=config.period_id,
        base_config_id=config.version_id,
        new_end_scan_id=14,
        actor="synthetic",
        reason="endpoint only",
        requested_utc=datetime.now(UTC).replace(microsecond=0),
        origin="authorized_import",
        provenance={},
    )
    snapshot_endpoint_request(cur, **args)
    conn.rollback()
    conn.close()
    assert load_snapshot(connect, kvk_no=season, period_id=config.period_id)["is_current"]
    with transaction(connect) as cur:
        cur.execute("BEGIN TRANSACTION")
        request = snapshot_endpoint_request(cur, **args)
        repeat = snapshot_endpoint_request(cur, **args)
        assert repeat["RequestID"] == request["RequestID"]
        cur.execute("COMMIT TRANSACTION")
    pending = load_snapshot(connect, kvk_no=season, period_id=config.period_id)
    assert pending["publication"]["EndScanID"] == 13 and not pending["is_current"]
    events.append(accepted_event(dal, season, 14, store))
    desired = replace(config, version_id=request["DesiredConfigVersionID"], end_scan_id=14)
    change = EndpointChange(
        request["RequestID"],
        config.period_id,
        config.version_id,
        desired.version_id,
        13,
        14,
        "synthetic",
        "endpoint only",
    )
    replacement = service.build_candidate(
        config=desired, observations=tuple(events), b0=b0, previous=prior, endpoint_change=change
    )
    action_id = str(uuid4())
    action = dict(
        action_id=action_id,
        expected_selection_version=3,
        expected_routing_version=1,
        actor="synthetic",
        reason="authorized end 14",
        action_type="endpoint_update",
        request_id=request["RequestID"],
    )
    result = service.select_publication(replacement, **action)
    assert service.select_publication(replacement, **action)["ActionID"] == result["ActionID"]
    read = load_snapshot(connect, kvk_no=season, period_id=config.period_id)
    assert read["is_current"] and read["publication"]["EndScanID"] == 14
    assert read["publication"]["PlayerState"] == "corrected_final"
    assert read["publication"]["AggregateState"] == "not_received"
    assert prior.end.logical_scan_id == 13


def test_aggregate_both_tabs_replay_final_and_late_live(database):
    from kvk.services.new_source_parser import parse_aggregate_workbook
    from tests.kvk_source_fixtures import aggregate_bytes

    connect, season, store = database
    dal = SourceImportDAL(connect, store)
    original = metadata(aggregate=True)
    c = replace(original.candidate, kvk_no=season)
    meta = replace(original, candidate=c, scope=replace(original.scope, kvk_no=season))
    with transaction(connect) as cur:
        cur.execute(
            "INSERT KVK.SourcePeriod VALUES (?,?,?,'fight:pass4','fight',?,?,?)",
            str(uuid4()),
            SOURCE_KEY,
            season,
            c.coverage_start_utc.replace(tzinfo=None),
            c.coverage_end_utc.replace(tzinfo=None),
            datetime(2000, 1, 1),
        )
    artifact = store.persist_artifact(aggregate_bytes(token=f"{season}.1"))
    prepared = parse_aggregate_workbook(store.read(artifact), meta, MAPPING)
    first = dal.accept_aggregate(prepared, artifact, admission())
    assert first.selected and first.logical_scan_id is None
    assert dal.accept_aggregate(prepared, artifact, admission()).duplicate
    from kvk.schemas.new_source_schema import ReportState

    final_meta = replace(meta, candidate=replace(c, report_state=ReportState.FINAL))
    final = parse_aggregate_workbook(store.read(artifact), final_meta, MAPPING)
    selected = dal.accept_aggregate(
        final,
        artifact,
        admission(
            admin_authorized=True, expected_revision_id=first.revision_id, expected_version=1
        ),
    )
    assert selected.selected and not selected.duplicate
    later_artifact = store.persist_artifact(aggregate_bytes(token=f"{season}.2"))
    late = parse_aggregate_workbook(store.read(later_artifact), meta, MAPPING)
    late_result = dal.accept_aggregate(late, later_artifact, admission())
    assert not late_result.selected
    with transaction(connect) as cur:
        cur.execute(
            "SELECT COUNT(*) FROM KVK.SourceKingdomReportRow WHERE RevisionID=?",
            selected.revision_id,
        )
        assert cur.fetchone()[0] == 2
        cur.execute(
            "SELECT COUNT(*) FROM KVK.SourceCampReportRow WHERE RevisionID=?", selected.revision_id
        )
        assert cur.fetchone()[0] == 2
        cur.execute("SELECT COUNT(*) FROM KVK.SourceLogicalScan WHERE KVK_NO=?", season)
        assert cur.fetchone()[0] == 0


class StatementFault:
    """Interrupt a real transaction at a specific durable-write boundary."""

    def __init__(self, connection, marker):
        self.connection, self.marker = connection, marker

    def __getattr__(self, name):
        return getattr(self.connection, name)

    def cursor(self):
        cursor = self.connection.cursor()
        marker = self.marker

        class Cursor:
            def __getattr__(self, name):
                return getattr(cursor, name)

            def execute(self, statement, *args):
                if marker in statement:
                    raise OSError("synthetic statement interruption")
                cursor.execute(statement, *args)
                return self

        return Cursor()


def publication_action(version=0, **changes):
    return dict(
        action_id=str(uuid4()),
        expected_selection_version=version,
        expected_routing_version=1,
        actor="synthetic",
        reason="failure boundary",
        destinations=(),
        **changes,
    )


@pytest.mark.parametrize("after", [False, True])
def test_t48_private_publication_commit_readback_without_delivery(database, after):
    connect, season, store = database
    dal = SourceImportDAL(connect, store)
    b0 = accepted_event(dal, season, 1, store)
    end = accepted_event(dal, season, 2, store)
    config = seed_config(connect, season, b0, end=2)
    service = PublicationService(connect)
    candidate = service.build_candidate(config=config, observations=(b0, end), b0=b0)
    action = publication_action()
    faulty = PublicationService(lambda: CommitFault(connect(), after=after))
    with pytest.raises(UncertainCommit):
        faulty.select_publication(candidate, **action)
    assert (service.dal.read_action(action["action_id"]) is not None) == after
    service.select_publication(candidate, **action)
    service.select_publication(candidate, **action)
    read = load_snapshot(connect, kvk_no=season, period_id=config.period_id)
    assert read["selection"]["SelectionVersion"] == 1
    with transaction(connect) as cur:
        cur.execute(
            "SELECT COUNT(*) FROM KVK.SourceDelivery WHERE PublicationID=?",
            candidate.snapshot.publication_id,
        )
        assert cur.fetchone()[0] == 0


def test_t47_failed_candidate_and_t49_newer_input_fence(database):
    connect, season, store = database
    dal = SourceImportDAL(connect, store)
    b0 = accepted_event(dal, season, 1, store)
    end = accepted_event(dal, season, 2, store)
    config = seed_config(connect, season, b0, end=4)
    broken = PublicationService(lambda: StatementFault(connect(), "INSERT KVK.SourcePlayerResult"))
    with pytest.raises(OSError):
        broken.build_candidate(config=config, observations=(b0, end), b0=b0)
    assert load_snapshot(connect, kvk_no=season, period_id=config.period_id)["publication"] is None
    service = PublicationService(connect)
    stale = service.build_candidate(config=config, observations=(b0, end), b0=b0)
    newer = accepted_event(dal, season, 3, store)
    with pytest.raises(SourceConflict, match="Newer player"):
        service.select_publication(stale, **publication_action())
    fresh = service.build_candidate(config=config, observations=(b0, end, newer), b0=b0)
    service.select_publication(fresh, **publication_action())
    assert (
        load_snapshot(connect, kvk_no=season, period_id=config.period_id)["publication"][
            "EndScanID"
        ]
        == 3
    )


def test_t44_source_correction_does_not_rewrite_pinned_final(database):
    connect, season, store = database
    dal = SourceImportDAL(connect, store)
    b0 = accepted_event(dal, season, 1, store)
    end = accepted_event(dal, season, 2, store)
    config = seed_config(connect, season, b0, end=2)
    service = PublicationService(connect)
    final = service.build_candidate(config=config, observations=(b0, end), b0=b0)
    service.select_publication(final, **publication_action())
    prepared, artifact = observation(season, 2, store, value=999)
    with pytest.raises(SourceConflict):
        dal.accept_observation(prepared, artifact, admission())
    corrected = dal.accept_observation(
        prepared,
        artifact,
        admission(admin_authorized=True, expected_revision_id=end.revision_id, expected_version=1),
    )
    assert corrected.logical_scan_id == 2
    same = service.build_candidate(config=config, observations=(b0, end), b0=b0)
    assert same.snapshot.publication_id == final.snapshot.publication_id
    changed = replace(end, revision_id=corrected.revision_id, observation=prepared)
    replacement = service.build_candidate(config=config, observations=(b0, changed), b0=b0)
    with pytest.raises(SourceConflict, match="Pinned final"):
        service.select_publication(replacement, **publication_action(1))
    with pytest.raises(PermissionError):
        service.select_publication(replacement, **publication_action(1, action_type="correct"))
    service.select_publication(
        replacement, **publication_action(1, action_type="correct", admin_authorized=True)
    )
    assert (
        load_snapshot(connect, kvk_no=season, period_id=config.period_id)["publication"][
            "EndRevisionID"
        ]
        == corrected.revision_id
    )
    # Rollback reselects immutable old facts with an increasing fence.
    service.select_publication(
        final, **publication_action(2, action_type="rollback", admin_authorized=True)
    )
    read = load_snapshot(connect, kvk_no=season, period_id=config.period_id)
    assert read["selection"]["SelectionVersion"] == 3
    assert read["publication"]["EndRevisionID"] == end.revision_id


def test_t46_aggregate_midway_failure_rolls_back_both_tabs(database):
    from kvk.services.new_source_parser import parse_aggregate_workbook
    from tests.kvk_source_fixtures import aggregate_bytes

    connect, season, store = database
    original = metadata(aggregate=True)
    c = replace(original.candidate, kvk_no=season)
    meta = replace(original, candidate=c, scope=replace(original.scope, kvk_no=season))
    with transaction(connect) as cur:
        cur.execute(
            "INSERT KVK.SourcePeriod VALUES (?,?,?,'fight:pass4','fight',?,?,?)",
            str(uuid4()),
            SOURCE_KEY,
            season,
            c.coverage_start_utc.replace(tzinfo=None),
            c.coverage_end_utc.replace(tzinfo=None),
            datetime(2000, 1, 1),
        )
    artifact = store.persist_artifact(aggregate_bytes(token=f"{season}.3"))
    prepared = parse_aggregate_workbook(store.read(artifact), meta, MAPPING)
    key = admission()
    broken = SourceImportDAL(
        lambda: StatementFault(connect(), "INSERT KVK.SourceCampReportRow"), store
    )
    with pytest.raises(OSError):
        broken.accept_aggregate(prepared, artifact, key)
    with transaction(connect) as cur:
        for table in (
            "SourceAggregateReport",
            "SourceAggregateRevision",
            "SourceKingdomReportRow",
            "SourceCampReportRow",
            "SourceImportAttempt",
        ):
            cur.execute("SELECT COUNT(*) FROM KVK." + table + " WHERE KVK_NO=?", season)
            assert cur.fetchone()[0] == 0
    assert SourceImportDAL(connect, store).accept_aggregate(prepared, artifact, key).selected


def test_t07_t43_aggregate_order_correction_and_mixed_stream_rebuild(database):
    from kvk.models.new_source_reporting import AggregateSelection
    from kvk.schemas.new_source_schema import ReportState
    from kvk.services.new_source_parser import parse_aggregate_workbook
    from tests.kvk_source_fixtures import aggregate_bytes

    connect, season, store = database
    dal = SourceImportDAL(connect, store)
    b0 = accepted_event(dal, season, 1, store)
    end = accepted_event(dal, season, 2, store)
    config = seed_config(connect, season, b0, end=3)
    close = datetime(2000, 1, 4, tzinfo=UTC)
    with transaction(connect) as cur:
        cur.execute(
            "UPDATE KVK.SourcePeriod SET CoverageEndUTC=? WHERE PeriodID=?",
            close.replace(tzinfo=None),
            config.period_id,
        )
    config = replace(config, closes_at_utc=close)
    service = PublicationService(connect)
    stale_player = service.build_candidate(config=config, observations=(b0, end), b0=b0)

    def aggregate(number, state=ReportState.LIVE, **authorization):
        original = metadata(aggregate=True)
        candidate = replace(
            original.candidate,
            kvk_no=season,
            scan_start_utc=close,
            coverage_start_utc=b0.scan_start_utc,
            coverage_end_utc=close - timedelta(hours=number),
            as_of_utc=close - timedelta(hours=number),
            report_state=state,
        )
        confirmation = replace(
            original.confirmation,
            values=tuple((key, getattr(candidate, key)) for key, _ in original.confirmation.values),
        )
        meta = replace(
            original,
            candidate=candidate,
            confirmation=confirmation,
            scope=replace(original.scope, kvk_no=season),
        )
        artifact = store.persist_artifact(aggregate_bytes(token=f"{season}.{number + 5}"))
        prepared = parse_aggregate_workbook(store.read(artifact), meta, MAPPING)
        result = dal.accept_aggregate(prepared, artifact, admission(**authorization))
        return result, AggregateSelection(result.identity_id, result.revision_id, prepared)

    first, live = aggregate(1)
    older, _ = aggregate(2)
    assert not older.selected
    with pytest.raises(SourceConflict, match="aggregate input changed"):
        service.select_publication(stale_player, **publication_action())
    fresh = service.build_candidate(config=config, observations=(b0, end), b0=b0, aggregate=live)
    service.select_publication(fresh, **publication_action())
    final_result, final = aggregate(
        0,
        ReportState.FINAL,
        admin_authorized=True,
        expected_revision_id=first.revision_id,
        expected_version=1,
    )
    with pytest.raises(SourceConflict):
        aggregate(
            0,
            ReportState.CORRECTED_FINAL,
            admin_authorized=True,
            expected_revision_id=first.revision_id,
            expected_version=1,
        )
    corrected_result, corrected = aggregate(
        0,
        ReportState.CORRECTED_FINAL,
        admin_authorized=True,
        expected_revision_id=final_result.revision_id,
        expected_version=2,
    )
    assert corrected_result.selected
    next_end = accepted_event(dal, season, 3, store)
    with pytest.raises(SourceConflict, match="aggregate input changed"):
        service.build_candidate(
            config=config, observations=(b0, end, next_end), b0=b0, aggregate=final
        )
    combined = service.build_candidate(
        config=config, observations=(b0, end, next_end), b0=b0, aggregate=corrected
    )
    service.select_publication(combined, **publication_action(1))
    read = load_snapshot(connect, kvk_no=season, period_id=config.period_id)
    assert read["publication"]["EndScanID"] == 3
    assert read["publication"]["AggregateRevisionID"] == corrected_result.revision_id
    assert read["publication"]["PeriodState"] == "corrected_final"

    # Cancelling a fight retains its aggregate history but excludes it from the new report.
    with transaction(connect) as cur:
        cur.execute("BEGIN TRANSACTION")
        request = snapshot_endpoint_request(
            cur,
            kvk_no=season,
            period_id=config.period_id,
            base_config_id=config.version_id,
            new_end_scan_id=1,
            actor="synthetic",
            reason="cancel fight",
            requested_utc=datetime.now(UTC).replace(microsecond=0),
            origin="authorized_import",
            provenance={},
        )
        cur.execute("COMMIT TRANSACTION")
    cancelled = replace(config, version_id=request["DesiredConfigVersionID"], end_scan_id=1)
    change = EndpointChange(
        request["RequestID"],
        config.period_id,
        config.version_id,
        cancelled.version_id,
        3,
        1,
        "synthetic",
        "cancel fight",
    )
    cancelled_candidate = service.build_candidate(
        config=cancelled,
        observations=(b0, end, next_end),
        b0=b0,
        previous=combined.snapshot.calculation.selection,
        endpoint_change=change,
    )
    service.select_publication(
        cancelled_candidate,
        **publication_action(2, action_type="endpoint_update", request_id=request["RequestID"]),
    )
    cancelled_read = load_snapshot(connect, kvk_no=season, period_id=config.period_id)
    assert cancelled_read["publication"]["AggregateRevisionID"] is None
    assert cancelled_read["publication"]["AggregateState"] == "not_applicable"
    with transaction(connect) as cur:
        cur.execute(
            "SELECT COUNT(*) FROM KVK.SourceAggregateRevision WHERE RevisionID=?",
            corrected_result.revision_id,
        )
        assert cur.fetchone()[0] == 1


def test_t52_reader_holds_one_generation_across_concurrent_selection(database):
    connect, season, store = database
    dal = SourceImportDAL(connect, store)
    b0 = accepted_event(dal, season, 1, store)
    end = accepted_event(dal, season, 2, store)
    config = seed_config(connect, season, b0, end=4)
    service = PublicationService(connect)
    first = service.build_candidate(config=config, observations=(b0, end), b0=b0)
    service.select_publication(first, **publication_action())
    next_end = accepted_event(dal, season, 3, store)
    next_candidate = service.build_candidate(config=config, observations=(b0, end, next_end), b0=b0)
    reached, release, writer_started = Event(), Event(), Event()

    class PausedReader:
        def __init__(self):
            self.connection = connect()

        def __getattr__(self, name):
            return getattr(self.connection, name)

        def cursor(self):
            cursor = self.connection.cursor()

            class Cursor:
                def __getattr__(self, name):
                    return getattr(cursor, name)

                def execute(self, sql, *args):
                    cursor.execute(sql, *args)
                    if "FROM KVK.SourcePlayerResult" in sql:
                        reached.set()
                        assert release.wait(5)
                    return self

            return Cursor()

    def select():
        writer_started.set()
        return service.select_publication(next_candidate, **publication_action(1))

    with ThreadPoolExecutor(2) as pool:
        reader = pool.submit(load_snapshot, PausedReader, kvk_no=season, period_id=config.period_id)
        assert reached.wait(5)
        writer = pool.submit(select)
        assert writer_started.wait(5)
        try:
            assert not writer.done()
        finally:
            release.set()
        old_read = reader.result(timeout=10)
        writer.result(timeout=10)
    assert old_read["publication"]["PublicationID"] == first.snapshot.publication_id
    assert {row["GovernorID"] for row in old_read["players"]} == {1001, 1002}
    assert (
        load_snapshot(connect, kvk_no=season, period_id=config.period_id)["publication"][
            "PublicationID"
        ]
        == next_candidate.snapshot.publication_id
    )


def test_t70_two_endpoint_requests_reject_stale_base(database):
    connect, season, store = database
    b0 = accepted_event(SourceImportDAL(connect, store), season, 1, store)
    config = seed_config(connect, season, b0, end=3)

    def request(endpoint):
        try:
            with transaction(connect) as cur:
                cur.execute("BEGIN TRANSACTION")
                result = snapshot_endpoint_request(
                    cur,
                    kvk_no=season,
                    period_id=config.period_id,
                    base_config_id=config.version_id,
                    new_end_scan_id=endpoint,
                    actor="synthetic",
                    reason="concurrent endpoint",
                    requested_utc=datetime.now(UTC).replace(microsecond=0),
                    origin="authorized_import",
                    provenance={},
                )
                cur.execute("COMMIT TRANSACTION")
                return result
        except SourceConflict:
            return None

    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(request, (4, 5)))
    assert sum(item is not None for item in results) == 1
    selected_request = next(item for item in results if item is not None)
    assert (
        load_snapshot(connect, kvk_no=season, period_id=config.period_id)["desired_config_id"]
        == selected_request["DesiredConfigVersionID"]
    )


@pytest.mark.parametrize(
    "configured_end", [15, None], ids=["scenario_1_future_end", "scenario_2_blank_end"]
)
def test_operator_scenarios_1_and_2_use_scan_11(configured_end, database):
    connect, season, store = database
    dal = SourceImportDAL(connect, store)
    events = tuple(accepted_event(dal, season, n, store) for n in range(1, 12))
    config = seed_config(connect, season, events[0], start=10, end=configured_end)
    service = PublicationService(connect)
    candidate = service.build_candidate(config=config, observations=events, b0=events[0])
    selection = candidate.snapshot.calculation.selection
    assert (selection.start.logical_scan_id, selection.end.logical_scan_id) == (10, 11)
    assert candidate.snapshot.player_state.value == "live"
    assert candidate.snapshot.calculation.players[0].metric("dkp").value == 100
    service.select_publication(candidate, **publication_action())
    current = load_snapshot(connect, kvk_no=season, period_id=config.period_id)
    assert current["is_current"]
    assert (current["publication"]["StartScanID"], current["publication"]["EndScanID"]) == (10, 11)


def test_operator_scenario_3_extends_final_14_to_15(database):
    connect, season, store = database
    dal = SourceImportDAL(connect, store)
    events = tuple(accepted_event(dal, season, n, store) for n in range(1, 15))
    config = seed_config(connect, season, events[0], start=10, end=14)
    service = PublicationService(connect)
    final = service.build_candidate(config=config, observations=events, b0=events[0])
    service.select_publication(final, **publication_action())
    events += (accepted_event(dal, season, 15, store),)
    # Arrival alone must leave the configured final pinned at 14.
    assert (
        service.build_candidate(
            config=config, observations=events, b0=events[0]
        ).snapshot.publication_id
        == final.snapshot.publication_id
    )
    with transaction(connect) as cur:
        cur.execute("BEGIN TRANSACTION")
        request = snapshot_endpoint_request(
            cur,
            kvk_no=season,
            period_id=config.period_id,
            base_config_id=config.version_id,
            new_end_scan_id=15,
            actor="synthetic",
            reason="fight lasted longer",
            requested_utc=datetime.now(UTC).replace(microsecond=0),
            origin="authorized_import",
            provenance={},
        )
        cur.execute("COMMIT TRANSACTION")
    updated = replace(config, version_id=request["DesiredConfigVersionID"], end_scan_id=15)
    change = EndpointChange(
        request["RequestID"],
        config.period_id,
        config.version_id,
        updated.version_id,
        14,
        15,
        "synthetic",
        "fight lasted longer",
    )
    replacement = service.build_candidate(
        config=updated,
        observations=events,
        b0=events[0],
        previous=final.snapshot.calculation.selection,
        endpoint_change=change,
    )
    service.select_publication(
        replacement,
        **publication_action(1, action_type="endpoint_update", request_id=request["RequestID"]),
    )
    assert final.snapshot.calculation.players[0].metric("dkp").value == 400
    assert replacement.snapshot.calculation.players[0].metric("dkp").value == 500
    read = load_snapshot(connect, kvk_no=season, period_id=config.period_id)
    assert (read["publication"]["StartScanID"], read["publication"]["EndScanID"]) == (10, 15)


@pytest.mark.parametrize("new_start,new_end", [(11, 14), (9, 13), (10, None), (10, 10), (15, 16)])
def test_authorized_start_and_end_changes(new_start, new_end, database):
    connect, season, store = database
    dal = SourceImportDAL(connect, store)
    events = tuple(accepted_event(dal, season, n, store) for n in range(1, 15))
    config = seed_config(connect, season, events[0], start=10, end=14)
    service = PublicationService(connect)
    final = service.build_candidate(config=config, observations=events, b0=events[0])
    service.select_publication(final, **publication_action())
    with transaction(connect) as cur:
        cur.execute("BEGIN TRANSACTION")
        request = snapshot_endpoint_request(
            cur,
            kvk_no=season,
            period_id=config.period_id,
            base_config_id=config.version_id,
            new_start_scan_id=new_start,
            new_end_scan_id=new_end,
            actor="synthetic",
            reason="reviewed endpoint pair",
            requested_utc=datetime.now(UTC).replace(microsecond=0),
            origin="authorized_import",
            provenance={},
        )
        cur.execute("COMMIT TRANSACTION")
    desired = replace(
        config,
        version_id=request["DesiredConfigVersionID"],
        start_scan_id=new_start,
        end_scan_id=new_end,
    )
    assert not load_snapshot(connect, kvk_no=season, period_id=config.period_id)["is_current"]
    change = EndpointChange(
        request["RequestID"],
        config.period_id,
        config.version_id,
        desired.version_id,
        14,
        new_end,
        "synthetic",
        "reviewed endpoint pair",
        10,
        new_start,
    )
    if new_start == 15:
        # Missing future start must stay explicit; no fallback to the prior start.
        pending = service.build_candidate(
            config=desired,
            observations=events,
            b0=events[0],
            previous=final.snapshot.calculation.selection,
            endpoint_change=change,
        )
        assert pending.snapshot.player_state.value == "missing_start"
        events += (accepted_event(dal, season, 15, store), accepted_event(dal, season, 16, store))
    replacement = service.build_candidate(
        config=desired,
        observations=events,
        b0=events[0],
        previous=final.snapshot.calculation.selection,
        endpoint_change=change,
    )
    service.select_publication(
        replacement,
        **publication_action(1, action_type="endpoint_update", request_id=request["RequestID"]),
    )
    read = load_snapshot(connect, kvk_no=season, period_id=config.period_id)
    assert read["is_current"] and read["publication"]["StartScanID"] == new_start
    assert read["publication"]["EndScanID"] == (new_end if new_end is not None else 14)
    assert (
        replacement.snapshot.calculation.players[0].metric("dkp").value
        == ((new_end if new_end is not None else 14) - new_start) * 100
    )
    if new_end == new_start:
        assert all(p.metric("dkp").value == 0 for p in replacement.snapshot.calculation.players)
        assert read["publication"]["PlayerState"] == "not_applicable"
    assert final.snapshot.calculation.selection.start.logical_scan_id == 10


@pytest.mark.parametrize("old_state", ["confirmed", "claimed", "uncertain", "failed"])
def test_s8b_refuses_direct_delivery_without_touching_retained_receipts(database, old_state):
    connect, season, store = database
    dal = SourceImportDAL(connect, store)
    b0 = accepted_event(dal, season, 1, store)
    end = accepted_event(dal, season, 2, store)
    config = seed_config(connect, season, b0, end=3)
    service = PublicationService(connect)
    candidate = service.build_candidate(config=config, observations=(b0, end), b0=b0)
    service.select_publication(candidate, **publication_action())
    receipt_utc = datetime(2026, 9, 13, tzinfo=UTC)
    with transaction(connect) as cur:
        cur.execute(
            "INSERT KVK.SourceDelivery (PublicationID,SourceKey,KVK_NO,PeriodID,DestinationKind,DestinationID,DeliveryState,AttemptCount,Fence,Receipt,OwnerID,ClaimedUTC,ConfirmedUTC,CreatedUTC,UpdatedUTC) VALUES (?,?,?,?,'file','synthetic',?,2,7,'retained',?,?,?,?,?)",
            candidate.snapshot.publication_id,
            SOURCE_KEY,
            season,
            config.period_id,
            old_state,
            str(uuid4()),
            receipt_utc,
            receipt_utc if old_state == "confirmed" else None,
            receipt_utc,
            receipt_utc,
        )
    action = publication_action(1, action_type="rollback", admin_authorized=True)
    action["destinations"] = (("file", "synthetic"),)
    with pytest.raises(SourceConflict, match="S10"):
        service.select_publication(candidate, **action)
    with transaction(connect) as cur:
        cur.execute(
            "SELECT DeliveryState,Fence,AttemptCount,Receipt FROM KVK.SourceDelivery WHERE PublicationID=?",
            candidate.snapshot.publication_id,
        )
        assert tuple(cur.fetchone()) == (old_state, 7, 2, "retained")


@pytest.mark.parametrize(
    "changed", ["request_id", "reason", "expected_routing_version", "destinations"]
)
def test_review_action_replay_rejects_changed_scope(database, changed):
    connect, season, store = database
    dal = SourceImportDAL(connect, store)
    b0 = accepted_event(dal, season, 1, store)
    end = accepted_event(dal, season, 2, store)
    config = seed_config(connect, season, b0, end=2)
    service = PublicationService(connect)
    candidate = service.build_candidate(config=config, observations=(b0, end), b0=b0)
    action = publication_action()
    action["destinations"] = ()
    service.select_publication(candidate, **action)
    equivalent = {
        **action,
        "destinations": (),
    }
    assert service.select_publication(candidate, **equivalent)["NewSelectionVersion"] == 1
    changed_values = {
        "request_id": str(uuid4()),
        "reason": "changed reason",
        "expected_routing_version": 2,
        "destinations": (("file", "third"),),
    }
    with pytest.raises(SourceConflict, match=r"replay|S10"):
        service.select_publication(candidate, **{**action, changed: changed_values[changed]})
    assert (
        load_snapshot(connect, kvk_no=season, period_id=config.period_id)["selection"][
            "SelectionVersion"
        ]
        == 1
    )


@pytest.mark.parametrize("restricted_scan", [1, 2])
def test_review_rejects_forged_observation_period_scope(database, restricted_scan):
    connect, season, store = database
    dal = SourceImportDAL(connect, store)
    events = []
    for number in (1, 2):
        prepared, artifact = observation(season, number, store)
        if number == restricted_scan:
            meta = replace(
                prepared.metadata, scope=replace(prepared.metadata.scope, period_keys=("overall",))
            )
            prepared = parse_player_workbook(store.read(artifact), meta)
        accepted = dal.accept_observation(prepared, artifact, admission())
        events.append(
            ObservationInput(
                accepted.logical_scan_id,
                accepted.identity_id,
                accepted.revision_id,
                prepared,
                ("fight:pass4", "overall"),
            )
        )
    b0, end = events
    config = seed_config(connect, season, b0, end=2)
    with pytest.raises(SourceConflict, match="accepted scope"):
        PublicationService(connect).build_candidate(config=config, observations=(b0, end), b0=b0)
    with transaction(connect) as cur:
        cur.execute("SELECT COUNT(*) FROM KVK.SourcePublication WHERE KVK_NO=?", season)
        assert cur.fetchone()[0] == 0


def sealed_fixture(
    database, *, no_fight=False, sequence=1, period_key="fight:pass4", period_kind=PeriodKind.FIGHT
):
    from kvk.models.source_integration import AggregateRevision, PlayerRevisions, UpdateContext
    from kvk.services.new_source_parser import parse_aggregate_workbook
    from kvk.services.season_source_service import SeasonSourceService
    from kvk.services.source_update_service import SourceUpdateService
    from tests.kvk_source_fixtures import aggregate_bytes

    connect, season, store = database
    imports = SourceImportDAL(connect, store)
    b0 = accepted_event(imports, season, 1, store)
    end = b0 if no_fight else accepted_event(imports, season, 2, store)
    config = seed_config(
        connect,
        season,
        b0,
        end=1 if no_fight else 3,
        sequence=sequence,
        period_key=period_key,
        period_kind=period_kind,
    )
    report = None
    if not no_fight:
        original = metadata(aggregate=True)
        coverage = {
            "coverage_start_utc": b0.scan_start_utc,
            "coverage_end_utc": end.scan_start_utc,
            "as_of_utc": end.scan_start_utc,
        }
        candidate = replace(original.candidate, kvk_no=season, **coverage)
        meta = replace(
            original,
            candidate=candidate,
            confirmation=replace(original.confirmation, values=tuple(coverage.items())),
            scope=replace(original.scope, kvk_no=season),
        )
        content = aggregate_bytes(token=str(season))
        prepared = parse_aggregate_workbook(content, meta, MAPPING)
        report = imports.accept_aggregate(prepared, store.persist_artifact(content), admission())
    choice = SeasonSourceService(connect).read(season)
    context = UpdateContext(
        update_id=str(uuid4()),
        kvk_no=season,
        period_id=config.period_id,
        period_key=config.period_key,
        choice_id=choice["ChoiceID"],
        config_version_id=config.version_id,
        roster_id=config.roster_id,
        coverage_start_utc=b0.scan_start_utc,
        coverage_end_utc=end.scan_start_utc,
        as_of_utc=end.scan_start_utc,
        update_kind="no_fight" if no_fight else "fight",
        actor="synthetic",
        confirmed_utc=datetime.now(UTC).replace(microsecond=0),
        confirmation_json="{}",
    )
    service = SourceUpdateService(connect)
    update = service.create(context, authorized=True)
    update = service.associate(
        context.update_id,
        expected_version=update["Version"],
        player=PlayerRevisions(
            b0.logical_scan_id, end.logical_scan_id, b0.revision_id, end.revision_id
        ),
        aggregate=AggregateRevision(report.identity_id, report.revision_id) if report else None,
        authorized=True,
    )
    return service, update


def test_s8b_two_builders_replay_one_complete_intent(database):
    from kvk.services.source_update_service import SourceUpdateService

    connect, season, _ = database
    service, update = sealed_fixture(database)

    def publish():
        try:
            return SourceUpdateService(connect).publish(update["UpdateID"])
        except SourceConflict:
            return SourceUpdateService(connect).publish(update["UpdateID"])

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: publish(), range(2)))
    assert results[0] == results[1]
    assert service.publish(update["UpdateID"]) == results[0]
    with transaction(connect) as cur:
        cur.execute("SELECT COUNT(*) FROM KVK.SourceCompleteSelection WHERE KVK_NO=?", season)
        assert cur.fetchone()[0] == 1
        cur.execute("SELECT COUNT(*) FROM KVK.SourceExportIntent WHERE KVK_NO=?", season)
        assert cur.fetchone()[0] == 1
        cur.execute("SELECT COUNT(*) FROM KVK.SourceDelivery WHERE KVK_NO=?", season)
        assert cur.fetchone()[0] == 0


@pytest.mark.parametrize(
    "marker", ["INSERT KVK.SourceExportIntent (", "INSERT KVK.SourceExportIntentPublication"]
)
def test_s8b_complete_pointer_intent_vector_rollback(database, marker):
    connect, season, _ = database
    service, update = sealed_fixture(database)
    service.publisher.dal.connect = lambda: StatementFault(connect(), marker)
    with pytest.raises(OSError):
        service.publish(update["UpdateID"])
    with transaction(connect) as cur:
        for table in (
            "SourceCompleteSelection",
            "SourceExportIntent",
            "SourceExportIntentPublication",
            "SourceAction",
        ):
            cur.execute("SELECT COUNT(*) FROM KVK." + table + " WHERE KVK_NO=?", season)
            assert cur.fetchone()[0] == 0
        cur.execute("SELECT UpdateState FROM KVK.SourceUpdate WHERE UpdateID=?", update["UpdateID"])
        assert cur.fetchone()[0] == "ready"
    service.publisher.dal.connect = connect
    assert service.publish(update["UpdateID"]).commit_sequence == 1


@pytest.mark.parametrize("opposing", [False, True])
def test_s8b_two_connection_fixed_choice_race(database, opposing):
    from kvk.services.season_source_service import SeasonSourceService

    connect, _, _ = database
    season = 1000000 + int(uuid4().hex[:7], 16)

    def choose(source):
        try:
            return SeasonSourceService(connect).choose(
                season,
                source,
                actor="synthetic",
                reason="race",
                provenance={"test": "race"},
                authorized=True,
            )
        except SourceConflict:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(
            pool.map(choose, (SOURCE_KEY, "legacy_full_data" if opposing else SOURCE_KEY))
        )
    if opposing:
        assert sum(r is not None for r in results) == 1
    else:
        assert results[0]["ChoiceID"] == results[1]["ChoiceID"]


def prepared_selection(service, update):
    """Build and persist the candidate, retaining its exact selection CAS arguments."""
    select = service.publisher.select_publication
    service.publisher.select_publication = lambda candidate, **action: {
        "complete": (candidate, action)
    }
    try:
        return service.publish(update["UpdateID"])
    finally:
        service.publisher.select_publication = select


def complete_rows(connect, season):
    with transaction(connect) as cur:
        result = {}
        for table in (
            "SourceCompleteSelection",
            "SourceExportIntent",
            "SourceExportIntentPublication",
            "SourceAction",
        ):
            cur.execute("SELECT COUNT(*) FROM KVK." + table + " WHERE KVK_NO=?", season)
            result[table] = cur.fetchone()[0]
        return result


def test_s8b_no_fight_in_existing_fight_period_selects_zero_members_and_replays(database):
    from kvk.services.source_update_service import SourceUpdateService

    connect, season, _ = database
    service, update = sealed_fixture(database, no_fight=True)
    assert (update["PeriodKind"], update["UpdateKind"]) == ("fight", "no_fight")
    candidate, action = prepared_selection(service, update)
    players = candidate.snapshot.calculation.players
    assert len(players) == 2 and all(p.metric("dkp").value == 0 for p in players)
    assert candidate.snapshot.aggregate is None
    assert candidate.snapshot.player_state.value == "not_applicable"
    result = service.publisher.select_publication(candidate, **action)["complete"]
    assert SourceUpdateService(connect).publish(update["UpdateID"]) == result
    assert complete_rows(connect, season) == dict(
        SourceCompleteSelection=1,
        SourceExportIntent=1,
        SourceExportIntentPublication=1,
        SourceAction=1,
    )
    with transaction(connect) as cur:
        cur.execute(
            "SELECT PeriodKind,PeriodKey FROM KVK.SourcePeriod WHERE PeriodID=?", update["PeriodID"]
        )
        assert tuple(cur.fetchone()) == ("fight", "fight:pass4")


@pytest.mark.parametrize("fault", ["classification", "mode", "unequal", "aggregate"])
def test_s8b_sql_rejects_invalid_no_fight_shape(database, fault):
    import pyodbc

    connect, _, _ = database
    _, update = sealed_fixture(database)
    # Direct SQL is intentional here: prove constraints independently of DAL guards.
    changes = {
        "classification": "PeriodKind='overall'",
        "mode": "UpdateKind='overall'",
        "unequal": "UpdateKind='no_fight',AggregateReportID=NULL,AggregateRevisionID=NULL",
        "aggregate": "UpdateKind='no_fight',EndScanID=StartScanID,EndRevisionID=StartRevisionID",
    }
    with pytest.raises(pyodbc.IntegrityError):
        with transaction(connect) as cur:
            cur.execute(
                "UPDATE KVK.SourceUpdate SET " + changes[fault] + " WHERE UpdateID=?",
                update["UpdateID"],
            )
    with transaction(connect) as cur:
        cur.execute(
            "SELECT PeriodKind,UpdateKind FROM KVK.SourceUpdate WHERE UpdateID=?",
            update["UpdateID"],
        )
        assert tuple(cur.fetchone()) == ("fight", "fight")


class StatementGate:
    """Pause one real writer after its season lock; observe the other entering its lock."""

    def __init__(self, connection, *, reached, release=None):
        self.connection, self.reached, self.release = connection, reached, release

    def __getattr__(self, name):
        return getattr(self.connection, name)

    def cursor(self):
        cursor, gate = self.connection.cursor(), self

        class Cursor:
            def __getattr__(self, name):
                return getattr(cursor, name)

            def execute(self, statement, *args):
                marker = "SELECT * FROM KVK.SourceRouting" if gate.release else "sp_getapplock"
                if marker in statement:
                    gate.reached.set()
                    if gate.release and not gate.release.wait(25):
                        raise TimeoutError("Synthetic writer gate was not released")
                cursor.execute(statement, *args)
                return self

        return Cursor()


def ordered_writers(connect, first, second):
    """Two dedicated connections overlap while the first owns the common season lock."""
    held, entered, release = Event(), Event(), Event()
    first_connect = lambda: StatementGate(connect(), reached=held, release=release)
    second_connect = lambda: StatementGate(connect(), reached=entered)
    with ThreadPoolExecutor(2) as pool:
        a = pool.submit(first, first_connect)
        try:
            assert held.wait(15), "first writer did not reach its post-season-lock gate"
            b = pool.submit(second, second_connect)
            assert entered.wait(5), "second writer did not enter its season-lock call"
            assert not b.done()
        finally:
            release.set()
        return a.result(timeout=30), b.result(timeout=30)


@pytest.mark.parametrize("reverse", [False, True])
def test_s8b_simultaneous_periods_preserve_complete_vector(database, reverse):
    connect, season, _ = database
    a, ua = sealed_fixture(database)
    b, ub = sealed_fixture(
        database,
        no_fight=True,
        sequence=2,
        period_key="no_fight:baseline",
        period_kind=PeriodKind.NO_FIGHT,
    )
    ca, aa = prepared_selection(a, ua)
    cb, ab = prepared_selection(b, ub)
    selections = [(ca, aa), (cb, ab)]
    if reverse:
        selections.reverse()
    operations = [
        lambda factory, c=c, action=action: PublicationService(factory).select_publication(
            c, **action
        )["complete"]
        for c, action in selections
    ]
    first, second = ordered_writers(connect, *operations)
    assert (first.commit_sequence, second.commit_sequence) == (1, 2)
    with transaction(connect) as cur:
        cur.execute(
            "SELECT UpdateID,PublicationID,PublicSelectionVersion,ConfigVersionID FROM KVK.SourceExportIntentPublication WHERE IntentID=?",
            first.intent_id,
        )
        retained = tuple(cur.fetchone())
        cur.execute(
            "SELECT UpdateID,PublicationID,PublicSelectionVersion,ConfigVersionID FROM KVK.SourceExportIntentPublication WHERE IntentID=?",
            second.intent_id,
        )
        members = [tuple(r) for r in cur.fetchall()]
        assert len(members) == 2 and retained in members
        assert {str(r[0]).lower() for r in members} == {ua["UpdateID"], ub["UpdateID"]}
    assert complete_rows(connect, season) == dict(
        SourceCompleteSelection=2,
        SourceExportIntent=2,
        SourceExportIntentPublication=3,
        SourceAction=2,
    )


def endpoint_request(connect, update):
    with transaction(connect) as cur:
        cur.execute("BEGIN TRANSACTION")
        request = snapshot_endpoint_request(
            cur,
            kvk_no=update["KVK_NO"],
            period_id=update["PeriodID"],
            base_config_id=update["ConfigVersionID"],
            new_end_scan_id=4,
            actor="synthetic",
            reason="S8B config race",
            requested_utc=datetime.now(UTC).replace(microsecond=0),
            origin="authorized_import",
            provenance={"test": "S8B race"},
        )
        cur.execute("COMMIT TRANSACTION")
        return request


def test_s8b_config_change_rejects_prebuilt_candidate_without_partial_selection(database):
    connect, season, _ = database
    service, update = sealed_fixture(database)
    candidate, action = prepared_selection(service, update)
    endpoint_request(connect, update)
    with pytest.raises(SourceConflict):
        service.publisher.select_publication(candidate, **action)
    assert all(n == 0 for n in complete_rows(connect, season).values())
    assert service.dal.read(update["UpdateID"])["UpdateState"] == "ready"


@pytest.mark.parametrize("config_first", [False, True])
def test_s8b_config_and_other_period_selection_share_lock_order(database, config_first):
    connect, season, _ = database
    _, fight = sealed_fixture(database)
    service, other = sealed_fixture(
        database,
        no_fight=True,
        sequence=2,
        period_key="no_fight:baseline",
        period_kind=PeriodKind.NO_FIGHT,
    )
    candidate, action = prepared_selection(service, other)
    select = lambda factory: PublicationService(factory).select_publication(candidate, **action)
    configure = lambda factory: endpoint_request(factory, fight)
    ordered_writers(connect, *((configure, select) if config_first else (select, configure)))
    assert complete_rows(connect, season)["SourceCompleteSelection"] == 1
    with transaction(connect) as cur:
        cur.execute("SELECT COUNT(*) FROM KVK.SourceConfigRequest WHERE KVK_NO=?", season)
        assert cur.fetchone()[0] == 1


def test_s8b_season_lock_timeout_leaves_no_partial_selection(database):
    import pyodbc

    from kvk.dal.new_source_import_dal import lock_scope

    connect, season, _ = database
    service, update = sealed_fixture(database)
    candidate, action = prepared_selection(service, update)
    with transaction(connect) as cur:
        lock_scope(cur, season)
        with ThreadPoolExecutor(1) as pool:
            future = pool.submit(service.publisher.select_publication, candidate, **action)
            with pytest.raises(pyodbc.Error, match="Source transaction lock unavailable"):
                future.result(timeout=20)
    assert all(n == 0 for n in complete_rows(connect, season).values())
    assert service.publish(update["UpdateID"]).commit_sequence == 1


@pytest.mark.parametrize("after", [False, True])
def test_s8b_complete_commit_loss_fresh_client_readback(database, after):
    from kvk.services.source_update_service import SourceUpdateService

    connect, season, _ = database
    service, update = sealed_fixture(database)
    candidate, action = prepared_selection(service, update)
    faulted = PublicationService(lambda: CommitFault(connect(), after=after))
    with pytest.raises(UncertainCommit):
        faulted.select_publication(candidate, **action)
    assert set(complete_rows(connect, season).values()) == {int(after)}
    recovered = SourceUpdateService(connect).publish(update["UpdateID"])
    assert recovered.commit_sequence == 1
    assert SourceUpdateService(connect).publish(update["UpdateID"]) == recovered
    assert set(complete_rows(connect, season).values()) == {1}
