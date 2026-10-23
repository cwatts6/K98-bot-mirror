"""Offline fixed-choice/CAS tests. These do not establish SQL concurrency evidence."""

from copy import deepcopy
from datetime import datetime
from unittest.mock import Mock

import pytest

from kvk.dal.new_source_import_dal import SourceConflict, UncertainCommit, transaction
from kvk.dal.season_source_dal import SeasonSourceDAL, audit_json, require_source
from kvk.services.season_source_service import SeasonSourceService


class Cursor:
    def __init__(self, route):
        self.route = route
        self.data = []
        self.description = []
        self.statements = []

    def execute(self, sql, *args):
        self.statements.append((sql, args))
        records = self.route(sql, args) or []
        self.description = [(key,) for key in records[0]] if records else []
        self.data = [tuple(row.values()) for row in records]
        return self

    def fetchone(self):
        return self.data.pop(0) if self.data else None

    def fetchall(self):
        result, self.data = self.data, []
        return result


class ChoiceStore:
    def __init__(self):
        self.choices = {}
        self.commits = 0
        self.lose_ack = False

    def route(self, sql, args):
        if sql.startswith("SELECT") and "KVK.SeasonSource" in sql:
            row = self.choices.get(args[0])
            return [deepcopy(row)] if row else []
        if sql.startswith("INSERT KVK.SeasonSource"):
            season, source, choice, actor, reason, evidence = args
            self.choices[season] = dict(
                KVK_NO=season,
                SourceKey=source,
                ChoiceID=choice,
                ChosenBy=actor,
                Reason=reason,
                ProvenanceJson=evidence,
                SeasonState="planned",
                SeasonVersion=1,
            )
        if sql.startswith("SELECT SYSUTCDATETIME"):
            return [dict(utc=datetime(2026, 9, 13))]
        if sql.startswith("UPDATE KVK.SeasonSource"):
            state, evidence, season, version = args
            row = self.choices[season]
            if row["SeasonVersion"] != version:
                return []
            row.update(SeasonState=state, ProvenanceJson=evidence, SeasonVersion=version + 1)
            return [deepcopy(row)]
        return []

    def connect(self):
        store = self
        before = deepcopy(self.choices)

        class Connection:
            autocommit = False

            def cursor(self):
                return Cursor(store.route)

            def commit(self):
                store.commits += 1
                if store.lose_ack:
                    store.lose_ack = False
                    raise OSError("lost acknowledgement")

            def rollback(self):
                store.choices = before

            def close(self):
                pass

        return Connection()


def choose(dal, source="snapshot_report_v1", **changes):
    return dal.choose(
        16,
        source,
        **dict(
            actor="operator", reason="Explicit choice", provenance={}, authorized=True, **changes
        ),
    )


def test_choice_retry_returns_original_audit_and_opposing_choice_conflicts():
    store = ChoiceStore()
    dal = SeasonSourceDAL(store.connect)
    first = choose(dal)
    assert choose(dal) == first
    with pytest.raises(SourceConflict, match="different source"):
        choose(dal, "legacy_full_data")
    assert store.choices[16] == first


def test_lost_ack_then_fresh_service_returns_committed_choice():
    store = ChoiceStore()
    store.lose_ack = True
    with pytest.raises(UncertainCommit):
        choose(SeasonSourceDAL(store.connect))
    saved = deepcopy(store.choices[16])
    assert choose(SeasonSourceService(store.connect)) == saved


def test_lifecycle_cas_preserves_fixed_choice_and_audit():
    store = ChoiceStore()
    dal = SeasonSourceDAL(store.connect)
    first = choose(dal)
    authority = dict(actor="operator", reason="Open season", authorized=True)
    opened = dal.transition(16, "open", expected_version=1, **authority)
    assert opened["ChoiceID"] == first["ChoiceID"]
    assert opened["SeasonVersion"] == 2
    with pytest.raises(SourceConflict, match="CAS"):
        dal.transition(16, "closing", expected_version=1, **authority)
    with pytest.raises(SourceConflict, match="one state"):
        dal.transition(16, "closed", expected_version=2, **authority)
    assert '"new":"open"' in store.choices[16]["ProvenanceJson"]


@pytest.mark.parametrize(
    "state,source,onboarding,valid",
    [
        ("planned", "snapshot_report_v1", True, True),
        ("planned", "snapshot_report_v1", False, False),
        ("open", "snapshot_report_v1", False, True),
        ("closing", "snapshot_report_v1", False, False),
        ("closed", "snapshot_report_v1", True, False),
        ("open", "legacy_full_data", False, False),
    ],
)
def test_admission_lifecycle_and_source(state, source, onboarding, valid):
    cursor = Cursor(lambda *_: [dict(SourceKey=source, SeasonState=state, SeasonVersion=2)])
    if valid:
        assert (
            require_source(cursor, 16, "snapshot_report_v1", onboarding=onboarding)["SeasonVersion"]
            == 2
        )
    else:
        with pytest.raises(SourceConflict):
            require_source(cursor, 16, "snapshot_report_v1", onboarding=onboarding)


def test_missing_source_and_authorization_fail_closed_before_write():
    with pytest.raises(SourceConflict, match="setup"):
        require_source(Cursor(lambda *_: []), 16, "legacy_full_data")
    connect = Mock()
    with pytest.raises(PermissionError):
        SeasonSourceDAL(connect).choose(
            16, "legacy_full_data", actor="x", reason="x", provenance={}, authorized=False
        )
    connect.assert_not_called()


def test_unicode_provenance_capacity_is_utf16_bytes():
    with pytest.raises(ValueError):
        audit_json({"reason": "x" * 32768})


def test_transaction_failure_rolls_back_without_commit():
    store = ChoiceStore()
    with pytest.raises(ValueError):
        with transaction(store.connect):
            store.choices[16] = {"bad": True}
            raise ValueError("failure")
    assert store.choices == {} and store.commits == 0
