from services import profile_lookup_service as svc


def test_resolve_profile_lookup_prefers_positive_governor_id(monkeypatch):
    called = False

    def _search(_query, limit=10):
        nonlocal called
        called = True
        return [("Ignored", 1, 99)]

    monkeypatch.setattr(svc, "search_by_governor_name", _search)

    result = svc.resolve_profile_lookup(governor_id=123, governor_name="Someone")

    assert result.status == "found"
    assert result.governor_id == 123
    assert called is False


def test_resolve_profile_lookup_accepts_autocomplete_governor_id(monkeypatch):
    monkeypatch.setattr(
        svc,
        "search_by_governor_name",
        lambda _query, limit=10: (_ for _ in ()).throw(AssertionError("unexpected search")),
    )

    result = svc.resolve_profile_lookup(governor_name="456")

    assert result.status == "found"
    assert result.governor_id == 456


def test_resolve_profile_lookup_returns_missing_query_for_empty_inputs():
    result = svc.resolve_profile_lookup()

    assert result.status == "missing_query"
    assert "governor_id" in result.message


def test_resolve_profile_lookup_preserves_no_match_copy(monkeypatch):
    monkeypatch.setattr(svc, "search_by_governor_name", lambda _query, limit=10: [])

    result = svc.resolve_profile_lookup(governor_name="No Such Player")

    assert result.status == "not_found"
    assert result.message == "No matches found."


def test_resolve_profile_lookup_returns_single_match_as_found(monkeypatch):
    monkeypatch.setattr(
        svc,
        "search_by_governor_name",
        lambda _query, limit=10: [("Alice", "789", 87)],
    )

    result = svc.resolve_profile_lookup(governor_name="ali")

    assert result.status == "found"
    assert result.governor_id == 789
    assert result.matches == ()


def test_resolve_profile_lookup_preserves_multi_match_order(monkeypatch):
    monkeypatch.setattr(
        svc,
        "search_by_governor_name",
        lambda _query, limit=10: [("Alice", 111, 90), ("Alicia", 222, 75)],
    )

    result = svc.resolve_profile_lookup(governor_name="ali")

    assert result.status == "matches"
    assert result.matches == (("Alice", 111, 90), ("Alicia", 222, 75))


def test_profile_governor_select_adapter_strips_scores():
    lookup_matches = (("Alice", 111, 90), ("Alicia", 222, 75))

    governor_matches = [(name, governor_id) for name, governor_id, *_ in lookup_matches]

    assert governor_matches == [("Alice", 111), ("Alicia", 222)]
