from __future__ import annotations

from event_calendar import sheets_sync


def test_sync_sheets_to_sql_fetch_fail_graceful(monkeypatch):
    monkeypatch.setattr(sheets_sync, "_insert_sync_log_start", lambda _src: 123)

    captured = {"finished": None}

    def _finish(sync_id, result):
        captured["finished"] = (sync_id, result)

    monkeypatch.setattr(sheets_sync, "_finish_sync_log", _finish)
    monkeypatch.setattr(
        sheets_sync,
        "fetch_sheet_csv",
        lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    res = sheets_sync.sync_sheets_to_sql("dummy")
    assert res.ok is False
    assert res.status == "failed_fetch_or_validate"
    assert "RuntimeError" in (res.error_message or "")
    assert captured["finished"] is not None


def test_sync_sheets_to_sql_happy_path(monkeypatch):
    monkeypatch.setattr(sheets_sync, "_insert_sync_log_start", lambda _src: 999)
    monkeypatch.setattr(sheets_sync, "_finish_sync_log", lambda *_a, **_k: None)

    def _fetch(_sheet, tab):
        if tab == "recurring_rules":
            return [
                {
                    "active": "TRUE",
                    "rule_id": "r1",
                    "emoji": "",
                    "title": "T",
                    "type": "mge",
                    "variant": "",
                    "recurrence_type": "every_n_days",
                    "interval_days": "7",
                    "first_start_utc": "2026-03-01 00:00:00",
                    "duration_days": "1",
                    "repeat_until_utc": "",
                    "max_occurrences": "",
                    "all_day": "TRUE",
                    "importance": "",
                    "description": "",
                    "link_url": "",
                    "channel_id": "",
                    "signup_url": "",
                    "tags": "",
                    "sort_order": "",
                    "notes_internal": "",
                }
            ]
        if tab == "oneoff_events":
            return [
                {
                    "active": "TRUE",
                    "event_id": "e1",
                    "emoji": "",
                    "title": "E",
                    "type": "ak",
                    "variant": "",
                    "start_utc": "2026-03-06 20:00:00",
                    "end_utc": "2026-03-06 20:30:00",
                    "all_day": "FALSE",
                    "importance": "",
                    "description": "",
                    "link_url": "",
                    "channel_id": "",
                    "signup_url": "",
                    "tags": "",
                    "sort_order": "",
                    "notes_internal": "",
                }
            ]
        return [
            {
                "active": "TRUE",
                "override_id": "o1",
                "target_kind": "rule",
                "target_id": "r1",
                "target_occurrence_start_utc": "2026-03-07 00:00:00",
                "action": "cancel",
                "new_start_utc": "",
                "new_end_utc": "",
                "new_title": "",
                "new_variant": "",
                "new_emoji": "",
                "new_importance": "",
                "new_description": "",
                "new_link_url": "",
                "new_channel_id": "",
                "new_signup_url": "",
                "new_tags": "",
                "notes_internal": "",
            }
        ]

    monkeypatch.setattr(sheets_sync, "fetch_sheet_csv", _fetch)
    monkeypatch.setattr(
        sheets_sync,
        "upsert_sql_rows",
        lambda **kwargs: len(kwargs["rows"]),
    )

    res = sheets_sync.sync_sheets_to_sql("dummy")
    assert res.ok is True
    assert res.status == "success"
    assert res.rows_read_recurring == 1
    assert res.rows_upserted_recurring == 1
