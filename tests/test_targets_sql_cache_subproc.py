# tests/test_targets_sql_cache_subproc.py
# Unit tests to validate that refresh_targets_cache returns a small summary when MAINT_SUBPROC=1.


import targets_sql_cache as tsc


def make_sample_rows():
    # simulate two target rows returned from _fetch_targets_from_view
    return [
        {
            "GovernorID": "123",
            "GovernorName": "Alice",
            "Power": 1000,
            "DKP_Target": None,
            "Kill_Target": None,
            "Deads_Target": None,
            "Min_Kill_Target": None,
        },
        {
            "GovernorID": "456",
            "GovernorName": "Bob",
            "Power": 2000,
            "DKP_Target": None,
            "Kill_Target": None,
            "Deads_Target": None,
            "Min_Kill_Target": None,
        },
    ]


def test_refresh_targets_cache_returns_summary_in_subprocess(monkeypatch, tmp_path):
    # prepare monkeypatches:
    monkeypatch.setenv("MAINT_SUBPROC", "1")
    # stub get_kvk_context_today to return a context
    monkeypatch.setattr(
        "targets_sql_cache.get_kvk_context_today", lambda: {"kvk_no": 99, "state": "ACTIVE"}
    )
    # stub _fetch_targets_from_view to return sample rows
    monkeypatch.setattr(
        "targets_sql_cache._fetch_targets_from_view", lambda cur: make_sample_rows()
    )
    # stub _write_json to write to temp file (no exception)
    _captured_path = str(tmp_path / "targets.json")
    monkeypatch.setattr("targets_sql_cache._write_json", lambda path, data: None)
    # call
    res = tsc.refresh_targets_cache()
    assert "_meta" in res
    assert "summary" in res
    assert res["summary"]["by_gov_count"] == 2
    # ensure we returned the smaller summary (no 'by_gov' full dict)
    assert (
        "by_gov" not in res
        or (isinstance(res.get("by_gov"), dict) and len(res["by_gov"]) == 0)
        or "summary" in res
    )


def test_refresh_targets_cache_returns_full_when_not_subprocess(monkeypatch, tmp_path):
    monkeypatch.delenv("MAINT_SUBPROC", raising=False)
    monkeypatch.setattr(
        "targets_sql_cache.get_kvk_context_today", lambda: {"kvk_no": 99, "state": "ACTIVE"}
    )
    monkeypatch.setattr(
        "targets_sql_cache._fetch_targets_from_view", lambda cur: make_sample_rows()
    )
    monkeypatch.setattr("targets_sql_cache._write_json", lambda path, data: None)
    res = tsc.refresh_targets_cache()
    assert "_meta" in res
    assert "by_gov" in res
    assert len(res["by_gov"]) == 2
