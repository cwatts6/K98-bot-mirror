# tests/test_prune_on_forbidden.py
"""
Unit tests for _is_prunable_fetch_exception behavior re: discord.Forbidden pruning flag.
"""

import types

import rehydrate_views


def _make_dummy_exc(kind_name: str):
    """
    Create a minimal dummy exception instance whose type will match isinstance checks
    against rehydrate_views.discord.<Name> when we monkeypatch rehydrate_views.discord.
    """
    cls = type(kind_name, (Exception,), {})
    return cls()


def test_forbidden_not_pruned_by_default(monkeypatch):
    # Ensure module believes discord types are available and provide classes
    monkeypatch.setattr(rehydrate_views, "DISCORD_AVAILABLE", True)
    fake_discord = types.SimpleNamespace(
        NotFound=type("NotFound", (Exception,), {}),
        Forbidden=type("Forbidden", (Exception,), {}),
        HTTPException=type("HTTPException", (Exception,), {}),
    )
    monkeypatch.setattr(rehydrate_views, "discord", fake_discord)

    # Ensure the module-level flag is False (default)
    monkeypatch.setattr(rehydrate_views, "VIEW_PRUNE_ON_FORBIDDEN", False)

    exc = fake_discord.Forbidden()
    assert rehydrate_views._is_prunable_fetch_exception(exc) is False


def test_forbidden_pruned_when_flag_enabled(monkeypatch):
    # Prepare environment as above
    monkeypatch.setattr(rehydrate_views, "DISCORD_AVAILABLE", True)
    fake_discord = types.SimpleNamespace(
        NotFound=type("NotFound", (Exception,), {}),
        Forbidden=type("Forbidden", (Exception,), {}),
        HTTPException=type("HTTPException", (Exception,), {}),
    )
    monkeypatch.setattr(rehydrate_views, "discord", fake_discord)

    # Enable opt-in flag
    monkeypatch.setattr(rehydrate_views, "VIEW_PRUNE_ON_FORBIDDEN", True)

    exc = fake_discord.Forbidden()
    assert rehydrate_views._is_prunable_fetch_exception(exc) is True


def test_notfound_always_pruned(monkeypatch):
    monkeypatch.setattr(rehydrate_views, "DISCORD_AVAILABLE", True)
    fake_discord = types.SimpleNamespace(
        NotFound=type("NotFound", (Exception,), {}),
        Forbidden=type("Forbidden", (Exception,), {}),
        HTTPException=type("HTTPException", (Exception,), {}),
    )
    monkeypatch.setattr(rehydrate_views, "discord", fake_discord)

    exc = fake_discord.NotFound()
    assert rehydrate_views._is_prunable_fetch_exception(exc) is True
