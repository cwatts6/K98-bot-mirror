from mge import mge_results_import
from mge.mge_xlsx_parser import ParsedMgeResultRow
from stats.dal.import_audit_dal import ImportAuditBatchRef


def _noop(*_args, **_kwargs):
    return None


def _audit_ref(*_args, **_kwargs):
    return ImportAuditBatchRef(12, "cid")


def _disable_audit(monkeypatch):
    monkeypatch.setattr(mge_results_import, "start_mge_results_audit_batch", _audit_ref)
    monkeypatch.setattr(mge_results_import, "record_mge_results_audit_phase", _noop)
    monkeypatch.setattr(mge_results_import, "complete_mge_results_audit_batch", _noop)
    monkeypatch.setattr(mge_results_import, "fail_mge_results_audit_batch", _noop)


def _sample_rows():
    return [
        {"rank": 1, "player_id": 17868677, "player_name": "Nikkiᵂᴬᴿ", "score": 39417197},
        {"rank": 2, "player_id": 18546768, "player_name": "Ì am Òðinn", "score": 20175585},
    ]


def test_auto_rejects_duplicate_same_file_hash(monkeypatch):
    _disable_audit(monkeypatch)
    monkeypatch.setattr(
        mge_results_import.mge_results_dal, "get_last_completed_event_id", lambda: 1001
    )
    monkeypatch.setattr(mge_results_import.mge_results_dal, "get_event_mode", lambda eid: "open")
    monkeypatch.setattr(
        mge_results_import.mge_results_dal,
        "has_successful_import_for_event_filehash",
        lambda eid, h: True,
    )

    try:
        mge_results_import.import_results_auto(
            content=b"abc",
            filename="mge_rankings_kd1198_20260311.xlsx",
            actor_discord_id=123,
        )
        raise AssertionError("Expected duplicate hash rejection")
    except ValueError as e:
        assert "same file hash" in str(e).lower()


def test_manual_force_overwrite_replaces_rows_and_returns_report(monkeypatch):
    _disable_audit(monkeypatch)
    monkeypatch.setattr(
        mge_results_import.mge_results_dal, "get_event_mode", lambda eid: "controlled"
    )
    monkeypatch.setattr(mge_results_import.mge_results_dal, "is_event_completed", lambda eid: True)
    monkeypatch.setattr(
        mge_results_import.mge_results_dal,
        "has_successful_import_for_event",
        lambda eid: True,
    )
    monkeypatch.setattr(
        mge_results_import,
        "parse_mge_results_xlsx",
        lambda content, filename: [ParsedMgeResultRow(**r) for r in _sample_rows()],
    )
    monkeypatch.setattr(
        mge_results_import.mge_results_dal, "create_import_batch", lambda **kwargs: 555
    )
    monkeypatch.setattr(
        mge_results_import.mge_results_dal, "replace_event_results", lambda *a, **k: 2
    )
    monkeypatch.setattr(
        mge_results_import.mge_results_dal, "mark_import_completed", lambda *a, **k: None
    )
    monkeypatch.setattr(
        mge_results_import.mge_results_dal, "mark_import_failed", lambda *a, **k: None
    )
    monkeypatch.setattr(
        mge_results_import.mge_results_dal,
        "fetch_controlled_awarded_vs_actual",
        lambda event_id: [{"AwardedRank": 1, "ActualRank": 2}],
    )

    out = mge_results_import.import_results_manual(
        content=b"xyz",
        filename="mge_rankings_kd1198_20260311.xlsx",
        event_id=2002,
        actor_discord_id=321,
        force_overwrite=True,
    )

    assert out["import_id"] == 555
    assert out["rows"] == 2
    assert out["report"]["type"] == "controlled_awarded_vs_actual"


def test_auto_success_returns_report(monkeypatch):
    _disable_audit(monkeypatch)
    monkeypatch.setattr(
        mge_results_import.mge_results_dal, "get_last_completed_event_id", lambda: 1001
    )
    monkeypatch.setattr(mge_results_import.mge_results_dal, "get_event_mode", lambda eid: "open")
    monkeypatch.setattr(
        mge_results_import.mge_results_dal,
        "has_successful_import_for_event_filehash",
        lambda eid, h: False,
    )
    monkeypatch.setattr(
        mge_results_import.mge_results_dal, "has_successful_import_for_event", lambda eid: False
    )
    monkeypatch.setattr(
        mge_results_import,
        "parse_mge_results_xlsx",
        lambda content, filename: [
            ParsedMgeResultRow(rank=1, player_id=1, player_name="A", score=10)
        ],
    )
    monkeypatch.setattr(
        mge_results_import.mge_results_dal, "create_import_batch", lambda **kwargs: 77
    )
    monkeypatch.setattr(
        mge_results_import.mge_results_dal, "replace_event_results", lambda *a, **k: 1
    )
    monkeypatch.setattr(
        mge_results_import.mge_results_dal, "mark_import_completed", lambda *a, **k: None
    )
    monkeypatch.setattr(
        mge_results_import.mge_results_dal, "mark_import_failed", lambda *a, **k: None
    )
    monkeypatch.setattr(
        mge_results_import.mge_results_dal,
        "fetch_open_top_15",
        lambda event_id: [{"Rank": 1, "PlayerId": 1, "PlayerName": "A", "Score": 10}],
    )

    out = mge_results_import.import_results_auto(b"x", "mge_rankings_kd1198_20260311.xlsx", 123)
    assert out["import_id"] == 77
    assert out["report"]["type"] == "open_top15"


def test_auto_success_report_failure_is_swallowed(monkeypatch):
    _disable_audit(monkeypatch)
    monkeypatch.setattr(
        mge_results_import.mge_results_dal, "get_last_completed_event_id", lambda: 1001
    )
    monkeypatch.setattr(mge_results_import.mge_results_dal, "get_event_mode", lambda eid: "open")
    monkeypatch.setattr(
        mge_results_import.mge_results_dal,
        "has_successful_import_for_event_filehash",
        lambda eid, h: False,
    )
    monkeypatch.setattr(
        mge_results_import.mge_results_dal, "has_successful_import_for_event", lambda eid: False
    )
    monkeypatch.setattr(
        mge_results_import,
        "parse_mge_results_xlsx",
        lambda content, filename: [
            ParsedMgeResultRow(rank=1, player_id=1, player_name="A", score=10)
        ],
    )
    monkeypatch.setattr(
        mge_results_import.mge_results_dal, "create_import_batch", lambda **kwargs: 77
    )
    monkeypatch.setattr(
        mge_results_import.mge_results_dal, "replace_event_results", lambda *a, **k: 1
    )
    monkeypatch.setattr(
        mge_results_import.mge_results_dal, "mark_import_completed", lambda *a, **k: None
    )
    monkeypatch.setattr(
        mge_results_import.mge_results_dal, "mark_import_failed", lambda *a, **k: None
    )
    monkeypatch.setattr(
        mge_results_import,
        "_build_import_report",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    out = mge_results_import.import_results_auto(b"x", "mge_rankings_kd1198_20260311.xlsx", 123)
    assert out["rows"] == 1
    assert out["report"] == {}


def test_auto_success_completes_generic_audit_with_import_correlation(monkeypatch):
    calls = []

    monkeypatch.setattr(mge_results_import, "start_mge_results_audit_batch", _audit_ref)
    monkeypatch.setattr(
        mge_results_import,
        "record_mge_results_audit_phase",
        lambda *args, **kwargs: calls.append(("phase", args, kwargs)),
    )
    monkeypatch.setattr(
        mge_results_import,
        "complete_mge_results_audit_batch",
        lambda *args, **kwargs: calls.append(("complete", args, kwargs)),
    )
    monkeypatch.setattr(
        mge_results_import,
        "fail_mge_results_audit_batch",
        lambda *args, **kwargs: calls.append(("fail", args, kwargs)),
    )
    monkeypatch.setattr(
        mge_results_import.mge_results_dal, "get_last_completed_event_id", lambda: 1001
    )
    monkeypatch.setattr(mge_results_import.mge_results_dal, "get_event_mode", lambda eid: "open")
    monkeypatch.setattr(
        mge_results_import.mge_results_dal,
        "has_successful_import_for_event_filehash",
        lambda eid, h: False,
    )
    monkeypatch.setattr(
        mge_results_import.mge_results_dal, "has_successful_import_for_event", lambda eid: False
    )
    monkeypatch.setattr(
        mge_results_import,
        "parse_mge_results_xlsx",
        lambda content, filename: [
            ParsedMgeResultRow(rank=1, player_id=1, player_name="A", score=10)
        ],
    )
    monkeypatch.setattr(
        mge_results_import.mge_results_dal, "create_import_batch", lambda **kwargs: 77
    )
    monkeypatch.setattr(
        mge_results_import.mge_results_dal, "replace_event_results", lambda *a, **k: 1
    )
    monkeypatch.setattr(
        mge_results_import.mge_results_dal, "mark_import_completed", lambda *a, **k: None
    )
    monkeypatch.setattr(
        mge_results_import.mge_results_dal,
        "fetch_open_top_15",
        lambda event_id: [{"Rank": 1, "PlayerId": 1, "PlayerName": "A", "Score": 10}],
    )

    out = mge_results_import.import_results_auto(
        b"x", "mge_rankings_kd1198_20260311.xlsx", 123
    )

    assert out["import_audit_batch_id"] == 12
    complete = [call for call in calls if call[0] == "complete"][-1]
    assert complete[2]["external_batch_id"] == "77"
    assert complete[2]["rows_in_source"] == 1
    assert complete[2]["rows_staged"] == 1
    assert complete[2]["rows_written"] == 1
    assert complete[2]["rows_skipped"] == 0
    assert [call[2]["phase_name"] for call in calls if call[0] == "phase"] == [
        mge_results_import.MGE_RESULTS_AUDIT_PRECHECK_PHASE,
        mge_results_import.MGE_RESULTS_AUDIT_PARSE_PHASE,
        mge_results_import.MGE_RESULTS_AUDIT_INGEST_PHASE,
    ]


def test_auto_duplicate_file_hash_records_uncorrelated_duplicate_audit(monkeypatch):
    calls = []

    monkeypatch.setattr(mge_results_import, "start_mge_results_audit_batch", _audit_ref)
    monkeypatch.setattr(
        mge_results_import,
        "record_mge_results_audit_phase",
        lambda *args, **kwargs: calls.append(("phase", args, kwargs)),
    )
    monkeypatch.setattr(
        mge_results_import,
        "complete_mge_results_audit_batch",
        lambda *args, **kwargs: calls.append(("complete", args, kwargs)),
    )
    monkeypatch.setattr(
        mge_results_import,
        "fail_mge_results_audit_batch",
        lambda *args, **kwargs: calls.append(("fail", args, kwargs)),
    )
    monkeypatch.setattr(
        mge_results_import.mge_results_dal, "get_last_completed_event_id", lambda: 1001
    )
    monkeypatch.setattr(mge_results_import.mge_results_dal, "get_event_mode", lambda eid: "open")
    monkeypatch.setattr(
        mge_results_import.mge_results_dal,
        "has_successful_import_for_event_filehash",
        lambda eid, h: True,
    )

    try:
        mge_results_import.import_results_auto(
            b"x", "mge_rankings_kd1198_20260311.xlsx", 123
        )
        raise AssertionError("Expected duplicate rejection")
    except ValueError:
        pass

    phase = [call for call in calls if call[0] == "phase"][-1]
    complete = [call for call in calls if call[0] == "complete"][-1]
    assert phase[2]["phase_status"] == "duplicate"
    assert complete[2]["status"] == "duplicate"
    assert complete[2].get("external_batch_id") is None


def test_auto_failure_after_import_batch_correlates_failed_audit(monkeypatch):
    calls = []

    monkeypatch.setattr(mge_results_import, "start_mge_results_audit_batch", _audit_ref)
    monkeypatch.setattr(
        mge_results_import,
        "record_mge_results_audit_phase",
        lambda *args, **kwargs: calls.append(("phase", args, kwargs)),
    )
    monkeypatch.setattr(
        mge_results_import,
        "complete_mge_results_audit_batch",
        lambda *args, **kwargs: calls.append(("complete", args, kwargs)),
    )
    monkeypatch.setattr(
        mge_results_import,
        "fail_mge_results_audit_batch",
        lambda *args, **kwargs: calls.append(("fail", args, kwargs)),
    )
    monkeypatch.setattr(
        mge_results_import.mge_results_dal, "get_last_completed_event_id", lambda: 1001
    )
    monkeypatch.setattr(mge_results_import.mge_results_dal, "get_event_mode", lambda eid: "open")
    monkeypatch.setattr(
        mge_results_import.mge_results_dal,
        "has_successful_import_for_event_filehash",
        lambda eid, h: False,
    )
    monkeypatch.setattr(
        mge_results_import.mge_results_dal, "has_successful_import_for_event", lambda eid: False
    )
    monkeypatch.setattr(
        mge_results_import,
        "parse_mge_results_xlsx",
        lambda content, filename: [
            ParsedMgeResultRow(rank=1, player_id=1, player_name="A", score=10)
        ],
    )
    monkeypatch.setattr(
        mge_results_import.mge_results_dal, "create_import_batch", lambda **kwargs: 77
    )
    monkeypatch.setattr(
        mge_results_import.mge_results_dal,
        "replace_event_results",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("sql down")),
    )
    failed_imports = []
    monkeypatch.setattr(
        mge_results_import.mge_results_dal,
        "mark_import_failed",
        lambda import_id, error: failed_imports.append((import_id, error)),
    )

    try:
        mge_results_import.import_results_auto(
            b"x", "mge_rankings_kd1198_20260311.xlsx", 123
        )
        raise AssertionError("Expected import failure")
    except RuntimeError:
        pass

    fail = [call for call in calls if call[0] == "fail"][-1]
    assert failed_imports == [(77, "sql down")]
    assert fail[2]["external_batch_id"] == "77"
    assert fail[2]["rows_in_source"] == 1
