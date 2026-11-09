"""Ordinary callers through the real resolver/DAL/formatter, using offline SQL rows."""

from copy import deepcopy
from dataclasses import replace
from unittest.mock import AsyncMock, Mock

import pytest

from kvk.dal import source_routing_dal as dal
from kvk.dal.new_source_import_dal import SourceConflict
from kvk.dal.new_source_publication_dal import result_digest
from kvk.models.source_integration import PUBLIC_REPORT_CAPABILITY, SeasonRead
from kvk.services import source_routing_service as service
from stats_alerts import allkingdoms
from tests.test_kvk_season_source import Cursor
from tests.test_kvk_source_pairs import uid, update_record
from tests.test_kvk_source_reporting import source_inputs


class RoutingStore:
    def __init__(self, **options):
        self.envelope, self.meta = source_inputs(**options)
        self.choice = dict(
            KVK_NO=16,
            SourceKey="snapshot_report_v1",
            ChoiceID=uid(3),
            SeasonVersion=1,
            SeasonState="open",
        )
        self.routing = dict(
            SourceKey="snapshot_report_v1",
            KVK_NO=16,
            Enabled=True,
            DisplayPeriodID=uid(2),
            RoutingVersion=1,
            CapabilitiesVersion=PUBLIC_REPORT_CAPABILITY,
        )
        pub = self.envelope["publication"]
        no_fight = options.get("end_scan") == 10
        self.update = update_record(
            UpdateState="selected",
            EndScanID=pub["EndScanID"],
            EndRevisionID=uid(10) if no_fight else uid(13),
            UpdateKind="no_fight" if no_fight else "overall" if options.get("overall") else "fight",
            PeriodKey=pub["PeriodKey"],
            AggregateReportID=None if no_fight else uid(20),
            AggregateRevisionID=None if no_fight else uid(21),
        )
        pub.update(
            {
                k: self.update[k]
                for k in (
                    "SourceKey",
                    "KVK_NO",
                    "PeriodID",
                    "ConfigVersionID",
                    "RosterID",
                    "StartRevisionID",
                    "EndRevisionID",
                    "AggregateReportID",
                    "AggregateRevisionID",
                )
            }
        )
        pub.update(
            PublicationID=uid(30),
            BuildState="complete",
            ResultCount=len(self.envelope["players"]),
            KingdomCount=len(self.envelope["aggregates"]["SourceKingdomReportRow"]),
            CampCount=len(self.envelope["aggregates"]["SourceCampReportRow"]),
            ManifestHash=result_digest(self.envelope["players"]),
        )
        self.publication = pub
        self.selection = dict(
            SourceKey=pub["SourceKey"],
            KVK_NO=16,
            PeriodID=uid(2),
            PublicationID=uid(30),
            UpdateID=uid(1),
            PublicSelectionVersion=7,
        )
        self.requested = None
        self.pending = None
        self.events = []
        self.closed = set()
        self.connections = 0
        self.fail = None
        self.on_results = None

    def route(self, sql, args, connection):
        self.events.append((connection, sql, args))
        if self.fail and self.fail in sql:
            raise OSError("synthetic unavailable")
        if "SourcePlayerResult" in sql:
            assert 1 in self.closed, "heavy result read retained the routing transaction"
            if self.on_results:
                self.on_results()
            return deepcopy(self.envelope["players"])
        if "SourceKingdomReportRow" in sql or "SourceCampReportRow" in sql:
            return deepcopy(
                self.envelope["aggregates"][
                    (
                        "SourceKingdomReportRow"
                        if "SourceKingdomReportRow" in sql
                        else "SourceCampReportRow"
                    )
                ]
            )
        if "FROM KVK.SeasonSource" in sql:
            return [self.choice] if self.choice else []
        if "FROM KVK.SourceRouting" in sql:
            return [self.routing] if self.routing else []
        if "FROM KVK.SourceSelection" in sql:
            return [{"PeriodID": uid(2)}]  # Component pointer deliberately isn't public authority.
        if "FROM KVK.SourceCompleteSelection" in sql:
            return [self.selection] if self.selection else []
        if "FROM KVK.SourceConfigRequest" in sql:
            return [self.requested] if self.requested else []
        if "SELECT TOP (1) UpdateID" in sql:
            return [self.pending] if self.pending else []
        if "FROM KVK.SourceUpdate" in sql:
            return [self.update]
        if "FROM KVK.SourcePublication" in sql:
            assert args[0] == uid(30)
            return [self.publication]
        if "SELECT ConfigVersion FROM" in sql:
            return [dict(ConfigVersion=1)]
        if "SELECT w.*,p.PeriodKind" in sql:
            return [self.meta["configs"]["requested" if args[0] == uid(40) else "selected"]]
        if "SourceObservationRevision r JOIN" in sql:
            return [self.meta["endpoints"]["start" if args[0] == uid(10) else "end"]]
        if "FROM KVK.SourceCampConfig" in sql:
            return self.meta["camps"]
        if "SELECT CoverageStartUTC" in sql:
            return [self.meta["aggregate"]] if self.meta["aggregate"] else []
        if sql.startswith("SET ") or "sp_getapplock" in sql:
            return []
        raise AssertionError(f"Unexpected SQL: {sql}")

    def connect(self):
        self.connections += 1
        number = self.connections
        cursor = Cursor(lambda sql, args: self.route(sql, args, number))
        return Mock(
            autocommit=False,
            cursor=Mock(return_value=cursor),
            close=Mock(side_effect=lambda: self.closed.add(number)),
        )

    def install(self, monkeypatch):
        monkeypatch.setattr(dal, "get_conn_with_retries", self.connect)
        monkeypatch.setattr(service, "get_conn_with_retries", self.connect)


@pytest.fixture
def store(monkeypatch):
    state = RoutingStore()
    state.install(monkeypatch)
    return state


def test_ordinary_complete_report_uses_one_publication_and_releases_authority_lock(store):
    report = allkingdoms.load_allkingdom_blocks(16)
    assert report["publication_id"] == uid(30)
    assert report["update_id"] == uid(1)
    assert report["public_selection_version"] == 7
    assert report["availability"] == "current"
    assert len(report["blocks"]) == 12
    assert report["blocks"]["camps_by_dkp"][0]["reported"]["dkp"]["raw"] == "25.3M"
    assert report["blocks"]["camps_by_dkp"][0]["kp_gain"] is None
    assert all("sp_getapplock" not in sql for connection, sql, _ in store.events if connection > 1)
    assert store.closed == {1, 2, 3}


@pytest.mark.parametrize(
    "failure,reason",
    [
        ("choice", "season_choice_missing"),
        ("routing", "routing_missing"),
        ("disabled", "serving_disabled"),
        ("capability", "capability_unsupported"),
        ("component_only", "waiting_pair"),
        ("database", "authority_unavailable"),
    ],
)
def test_ordinary_unavailable_never_queries_legacy_or_immutable_facts(store, failure, reason):
    if failure == "choice":
        store.choice = None
    elif failure == "routing":
        store.routing = None
    elif failure == "disabled":
        store.routing["Enabled"] = False
    elif failure == "capability":
        store.routing["CapabilitiesVersion"] = "unknown"
    elif failure == "component_only":
        store.selection = None
    else:
        store.fail = "SeasonSource"
    report = allkingdoms.load_allkingdom_blocks(16)
    assert report["availability_reason"] == reason
    assert not report["is_current"] and report["publication_id"] is None
    assert all(not block for block in report["blocks"].values())
    assert not any("SourcePlayerResult" in sql or "fn_KVK" in sql for _, sql, _ in store.events)


@pytest.mark.parametrize("state", ["waiting_player", "waiting_aggregate", "ready"])
@pytest.mark.parametrize("previous", [True, False])
def test_first_pair_and_failed_second_side_never_replace_complete_result(store, state, previous):
    store.pending = dict(UpdateID=uid(50), Version=2, UpdateState=state)
    if not previous:
        store.selection = None
    report = allkingdoms.load_allkingdom_blocks(16)
    assert report["availability_reason"] == state
    assert report["availability"] == ("previous_complete" if previous else "unavailable")
    assert report["publication_id"] == (uid(30) if previous else None)


def test_desired_endpoint_changes_cache_identity_and_old_final_label(store):
    before = dal.resolve_season_read(16)
    store.requested = dict(DesiredConfigVersionID=uid(40), ConfigVersion=2)
    store.meta["configs"]["requested"] = dict(store.meta["configs"]["selected"], EndScanID=14)
    report = allkingdoms.load_allkingdom_blocks(16)
    after = SeasonRead(**report["public_read"])
    assert before.cache_key != after.cache_key
    assert report["player_state"] == "final"  # Selected input retains its own historical finality.
    assert not report["is_current"] and report["endpoint_pending"]
    assert (report["selected_end_scan_id"], report["requested_end_scan_id"]) == (13, 14)
    with pytest.raises(SourceConflict, match="authority changed"):
        service.require_current_read(before.as_dict())


@pytest.mark.parametrize(
    "field,value",
    [
        ("KVK_NO", 17),
        ("ChoiceID", uid(90)),
        ("PeriodID", uid(90)),
        ("ConfigVersionID", uid(90)),
        ("RosterID", uid(90)),
        ("AggregateRevisionID", None),
        ("ContentHash", b"x" * 32),
        ("UpdateState", "ready"),
    ],
)
def test_cross_scope_or_unsealed_update_is_unavailable(store, field, value):
    store.update[field] = value
    report = allkingdoms.load_allkingdom_blocks(16)
    assert report["availability"] == "unavailable"
    assert not any("SourcePlayerResult" in sql for _, sql, _ in store.events)


@pytest.mark.parametrize("broken", ["player_hash", "aggregate_count", "missing_metric"])
def test_immutable_corruption_never_returns_partial_blocks(store, broken):
    if broken == "player_hash":
        store.publication["ManifestHash"] = b"x" * 32
    elif broken == "aggregate_count":
        store.publication["CampCount"] += 1
    else:
        store.envelope["aggregates"]["SourceCampReportRow"][0]["dkp"] = None
    report = allkingdoms.load_allkingdom_blocks(16)
    assert report["availability_reason"] == "publication_integrity_failed"
    assert all(not block for block in report["blocks"].values())


def test_pointer_changes_during_fact_load_do_not_mix_blocks_or_pass_action_check(store):
    store.on_results = lambda: store.selection.update(PublicSelectionVersion=8)
    report = allkingdoms.load_allkingdom_blocks(16)
    assert report["public_selection_version"] == 7
    assert report["publication_id"] == uid(30)
    with pytest.raises(SourceConflict):
        service.require_current_read(report["public_read"])


def test_fixed_legacy_choice_preserves_block_contract(store, monkeypatch):
    from kvk.dal import kvk_reporting_dal

    store.choice["SourceKey"] = "legacy_full_data"
    fetch = Mock(return_value={"players_by_kills": [{"name": "legacy", "kills_gain": 4}]})
    monkeypatch.setattr(kvk_reporting_dal, "fetch_allkingdom_reporting_rows", fetch)
    blocks = allkingdoms.load_allkingdom_blocks(16)
    assert blocks["players_by_kills"][0]["acclaim_gain"] == 0
    assert blocks.read.availability == "legacy"
    assert not any("SourceRouting" in sql for _, sql, _ in store.events)


@pytest.mark.parametrize("options", [{"end_scan": 10}, {"overall": True}])
def test_public_no_fight_and_independent_overall(monkeypatch, options):
    state = RoutingStore(**options)
    state.install(monkeypatch)
    report = allkingdoms.load_allkingdom_blocks(16)
    assert report["availability"] == "current"
    if options.get("end_scan") == 10:
        assert report["aggregate_state"] == "not_applicable"
        assert not report["blocks"]["camps_by_dkp"]
        assert all(row["rank"] is None for row in report["blocks"]["players_by_dkp"])
    else:
        assert report["period_kind"] == "overall" and report["aggregate_state"] == "final"


@pytest.mark.asyncio
async def test_ordinary_preview_selects_source_without_injected_provider(store, monkeypatch):
    from stats_alerts.embeds import kvk

    monkeypatch.setattr(
        kvk,
        "get_latest_kvk_metadata_sql",
        lambda: dict(kvk_no=16, kvk_name="KVK", start_date=1, end_date=2),
    )
    honor = AsyncMock(side_effect=AssertionError("daily honor read"))
    monkeypatch.setattr(kvk, "get_latest_honor_top", honor)
    preview = await kvk.build_kvk_preview("display timestamp")
    assert preview.available and len(preview.payload) == 1
    assert preview.public_read["update_id"] == uid(1)
    honor.assert_not_awaited()


@pytest.mark.parametrize(
    "change",
    [
        "routing_version",
        "season_version",
        "capabilities_version",
        "desired_config_id",
        "roster_id",
        "publication_id",
        "public_selection_version",
        "update_id",
    ],
)
def test_cache_identity_covers_authority_dimensions(store, change):
    before = dal.resolve_season_read(16)
    value = (
        "unsupported"
        if change == "capabilities_version"
        else uid(90) if change.endswith("_id") else 99
    )
    after = replace(before, **{change: value}, availability="unavailable")
    assert before.cache_key != after.cache_key
