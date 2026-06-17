from ui.views import calendar as cv


def test_allowed_days_has_365_not_356():
    days = cv.allowed_days()
    assert 365 in days
    assert 356 not in days


def test_cache_footer_uses_payload_fields():
    s = {
        "cache_age_minutes": 5,
        "payload": {"generated_utc": "x", "horizon_days": 30, "source": "sql"},
    }
    out = cv.cache_footer(s)
    assert "generated_utc=x" in out
    assert "horizon_days=30" in out
    assert "source=sql" in out


def test_grouped_embed_build_smoke():
    events = [
        {
            "title": "A",
            "start_utc": "2026-03-10T00:00:00+00:00",
            "end_utc": "2026-03-10T01:00:00+00:00",
        },
        {
            "title": "B",
            "start_utc": "2026-03-10T02:00:00+00:00",
            "end_utc": "2026-03-10T03:00:00+00:00",
        },
    ]
    emb = cv.build_pinned_calendar_embed(events=events, footer="f")
    assert emb.fields
    assert emb.footer.text == "f"
