"""Pinned context and reader handoff regressions, without database/provider calls."""

from contextlib import contextmanager
from copy import deepcopy
from uuid import UUID

import pytest

from kvk.dal import new_source_delivery_dal as delivery, new_source_report_context_dal as dal
from kvk.dal.new_source_import_dal import SourceConflict
from kvk.schemas.new_source_schema import SOURCE_KEY

PUB, CONFIG, ROSTER, BASE, START, END, AGG, PERIOD = [str(UUID(int=n)) for n in range(1, 9)]


class Cursor:
    def __init__(self):
        self.publication = dict(
            PublicationID=PUB,
            ConfigVersionID=CONFIG,
            RosterID=ROSTER,
            KVK_NO=16,
            SourceKey=SOURCE_KEY,
            BuildState="complete",
            PeriodID=PERIOD,
            StartRevisionID=START,
            EndRevisionID=END,
            AggregateRevisionID=AGG,
        )
        self.windows = [
            dict(
                PeriodKey="fight:altar",
                WindowName="2nd Altar",
                WindowSeq=3,
                StartScanID=30,
                EndScanID=30,
            )
        ]
        self.executed = []
        self.powers = [
            dict(
                GovernorID=n,
                b0_kingdom=1098,
                BaselinePower=100 + n,
                StartPower=200 + n,
                EndPower=None if n == 3 else 300 + n,
                BaselineTroopsPower=80 + n,
                StartTroopsPower=90 + n,
                EndTroopsPower=None if n == 3 else 110 + n,
            )
            for n in range(1, 7)
        ]
        self.missing_roster = False

    def execute(self, sql, *args):
        self.executed.append((sql, args))
        if "FROM KVK.SourcePublication" in sql:
            data = [deepcopy(self.publication)] if args == (PUB, SOURCE_KEY, 16) else []
        elif "FROM KVK.SourceRoster WHERE" in sql:
            data = [] if self.missing_roster else [{"B0RevisionID": BASE}]
        elif "FROM KVK.SourceWindowConfig" in sql:
            assert args == (CONFIG, SOURCE_KEY, 16)
            data = deepcopy(self.windows)
        elif "FROM KVK.SourceRosterMember" in sql:
            size, *pins, after = args
            assert pins == [
                BASE,
                SOURCE_KEY,
                16,
                START,
                SOURCE_KEY,
                16,
                END,
                SOURCE_KEY,
                16,
                ROSTER,
                SOURCE_KEY,
                16,
            ]
            data = deepcopy([r for r in self.powers if r["GovernorID"] > after][:size])
        else:
            raise AssertionError(sql)
        names = tuple(data[0]) if data else ()
        self.description = [(n,) for n in names]
        self.data = [tuple(r[n] for n in names) for r in data]

    def fetchone(self):
        return self.data.pop(0) if self.data else None

    def fetchall(self):
        return self.data


@pytest.fixture
def cursor(monkeypatch):
    cursor = Cursor()

    @contextmanager
    def transaction(connect):
        yield cursor

    def metadata(connect, envelope):
        assert envelope["desired_config_id"] == CONFIG
        return {
            "camps": [{"CampID": 1, "CampName": "Fire", "Kingdom": 1098}],
            "endpoints": {"start": {"ObservationID": START}, "end": {"ObservationID": END}},
        }

    monkeypatch.setattr(dal, "transaction", transaction)
    monkeypatch.setattr(dal, "fetch_source_report_metadata", metadata)
    return cursor


def load(**kwargs):
    return dal.load_report_context(
        connect=lambda: None, publication_id=PUB, **({"kvk_no": 16} | kwargs)
    )


def test_pinned_labels_powers_and_no_fight_configuration_retained(cursor):
    context = load()
    assert context["metadata"]["camps"][0]["CampName"] == "Fire"
    assert context["windows"][0]["StartScanID"] == context["windows"][0]["EndScanID"] == 30
    assert context["revisions"] == dict(baseline=BASE, start=START, end=END, aggregate=AGG)
    powers = list(dal.iter_player_powers(connect=lambda: None, context=context, batch_size=2))
    assert powers == cursor.powers
    assert powers[2]["EndPower"] is None
    assert len(powers) == len({r["GovernorID"] for r in powers})
    assert all(
        "SelectedRevisionID" not in sql and "DesiredConfigVersionID" not in sql
        for sql, _ in cursor.executed
    )


def test_old_context_survives_new_selection_and_config(cursor):
    context = load()
    cursor.publication.update(
        ConfigVersionID=str(UUID(int=900)), StartRevisionID=str(UUID(int=901))
    )
    cursor.windows[0]["WindowName"] = "New label"
    assert context["windows"][0]["WindowName"] == "2nd Altar"
    assert (
        list(dal.iter_player_powers(connect=lambda: None, context=context, batch_size=1))
        == cursor.powers
    )


def test_same_revision_can_supply_baseline_and_fight_start(cursor):
    cursor.publication["StartRevisionID"] = BASE
    assert load()["revisions"]["start"] == BASE


def test_wrong_season_and_incomplete_publication_fail_closed(cursor):
    with pytest.raises(SourceConflict):
        load(kvk_no=17)
    cursor.publication["BuildState"] = "building"
    with pytest.raises(SourceConflict):
        load()


def test_missing_roster_and_bad_scope(cursor):
    cursor.missing_roster = True
    with pytest.raises(SourceConflict):
        load()
    with pytest.raises(ValueError):
        load(kvk_no=True)


def test_reader_entry_point_pins_context_and_history(monkeypatch, cursor):
    from types import SimpleNamespace

    from kvk.dal import new_source_history_dal as history

    selection = SimpleNamespace(publication_id=PUB)
    snapshot = {"envelope": {"publication": deepcopy(cursor.publication)}}
    intent = dict(SourceKey=SOURCE_KEY, KVK_NO=16, VectorHash=b"v" * 32)
    monkeypatch.setattr(
        delivery,
        "load_intent_export_snapshots",
        lambda **kw: (intent, iter([(selection, snapshot)])),
    )
    captured = []
    monkeypatch.setattr(history, "capture_history", lambda **kw: captured.append(kw) or "history")
    args = dict(
        connect=lambda: None,
        intent_id=str(UUID(int=123)),
        kvk_no=16,
        guild_id="123",
        expected_hash=b"v" * 32,
    )
    result, frozen, periods = delivery.load_reader_export_inputs(**args)
    assert result == intent and frozen == "history"
    assert captured[0]["guild_id"] == "123"
    assert next(iter(periods))[1]["reader_context"]["revisions"]["end"] == END
    captured.clear()
    with pytest.raises(SourceConflict):
        delivery.load_reader_export_inputs(**(args | {"expected_hash": b"x" * 32}))
    assert not captured


def test_reader_handoff_rejects_changed_publication(monkeypatch, cursor):
    from types import SimpleNamespace

    from kvk.dal import new_source_history_dal as history

    monkeypatch.setattr(
        delivery,
        "load_intent_export_snapshots",
        lambda **kw: (
            dict(SourceKey=SOURCE_KEY, KVK_NO=16, VectorHash=b"v" * 32),
            iter([(SimpleNamespace(publication_id=PUB), {"envelope": {"publication": {}}})]),
        ),
    )
    monkeypatch.setattr(history, "capture_history", lambda **kw: "history")
    _, _, periods = delivery.load_reader_export_inputs(
        connect=lambda: None,
        intent_id=str(UUID(int=123)),
        kvk_no=16,
        guild_id="123",
        expected_hash=b"v" * 32,
    )
    with pytest.raises(SourceConflict):
        list(periods)
