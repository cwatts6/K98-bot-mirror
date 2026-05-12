from __future__ import annotations

from mge import mge_commander_service


def test_list_commanders_by_variant_uses_dal(monkeypatch):
    rows = [{"CommanderId": 1, "CommanderName": "Attila"}]
    monkeypatch.setattr(
        mge_commander_service.mge_commander_dal,
        "fetch_commanders_for_variant",
        lambda variant_id, include_inactive=True: rows,
    )

    assert mge_commander_service.list_commanders_by_variant(5) == rows


def test_add_new_commander_refreshes_cache(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        mge_commander_service.mge_commander_dal,
        "fetch_commander_by_name",
        lambda name: None,
    )
    monkeypatch.setattr(
        mge_commander_service.mge_commander_dal,
        "upsert_commander_assignment",
        lambda **kwargs: captured.update(kwargs)
        or {
            "CommanderId": 9,
            "CommanderName": kwargs["commander_name"],
            "VariantId": kwargs["variant_id"],
            "IsActive": kwargs["is_active"],
        },
    )
    monkeypatch.setattr(
        mge_commander_service.mge_cache,
        "refresh_mge_caches",
        lambda: {"commanders": True, "variant_commanders": True},
    )

    result = mge_commander_service.save_commander_assignment(
        commander_id=None,
        commander_name="  New   Commander ",
        variant_id=2,
        is_active=True,
    )

    assert result.success is True
    assert result.commander_id == 9
    assert captured["commander_name"] == "New Commander"
    assert captured["variant_id"] == 2


def test_update_name_and_active_flag(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        mge_commander_service.mge_commander_dal,
        "fetch_commander_by_name",
        lambda name: None,
    )
    monkeypatch.setattr(
        mge_commander_service.mge_commander_dal,
        "upsert_commander_assignment",
        lambda **kwargs: captured.update(kwargs)
        or {
            "CommanderId": kwargs["commander_id"],
            "CommanderName": kwargs["commander_name"],
            "VariantId": kwargs["variant_id"],
            "IsActive": kwargs["is_active"],
        },
    )
    monkeypatch.setattr(
        mge_commander_service.mge_cache,
        "refresh_mge_caches",
        lambda: {"commanders": True, "variant_commanders": True},
    )

    result = mge_commander_service.save_commander_assignment(
        commander_id=3,
        commander_name="Renamed",
        variant_id=4,
        is_active=False,
    )

    assert result.success is True
    assert captured["commander_id"] == 3
    assert captured["commander_name"] == "Renamed"
    assert captured["is_active"] is False


def test_move_variant_is_service_level_assignment(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        mge_commander_service.mge_commander_dal,
        "fetch_commander_by_name",
        lambda name: None,
    )
    monkeypatch.setattr(
        mge_commander_service.mge_commander_dal,
        "upsert_commander_assignment",
        lambda **kwargs: captured.update(kwargs)
        or {
            "CommanderId": kwargs["commander_id"],
            "CommanderName": kwargs["commander_name"],
            "VariantId": kwargs["variant_id"],
            "IsActive": kwargs["is_active"],
        },
    )
    monkeypatch.setattr(
        mge_commander_service.mge_cache,
        "refresh_mge_caches",
        lambda: {"commanders": True, "variant_commanders": True},
    )

    result = mge_commander_service.save_commander_assignment(
        commander_id=7,
        commander_name="Mover",
        variant_id=8,
        is_active=True,
    )

    assert result.success is True
    assert captured["variant_id"] == 8


def test_duplicate_active_commander_name_rejected(monkeypatch):
    monkeypatch.setattr(
        mge_commander_service.mge_commander_dal,
        "fetch_commander_by_name",
        lambda name: {"CommanderId": 5, "CommanderName": name, "IsActive": True},
    )
    monkeypatch.setattr(
        mge_commander_service.mge_commander_dal,
        "fetch_commanders_for_variant",
        lambda variant_id, include_inactive=False: [{"CommanderId": 5}],
    )

    result = mge_commander_service.save_commander_assignment(
        commander_id=6,
        commander_name="Duplicate",
        variant_id=1,
        is_active=True,
    )

    assert result.success is False
    assert "already exists" in result.message


def test_inactive_commanders_excluded_from_signup_cache(monkeypatch):
    from mge import mge_cache

    monkeypatch.setattr(
        mge_cache,
        "read_variant_commanders_cache",
        lambda: [
            {"VariantName": "Infantry", "CommanderName": "Active", "IsActive": True},
        ],
    )

    result = mge_cache.get_commanders_for_variant("Infantry")

    assert [row["CommanderName"] for row in result] == ["Active"]


def test_historical_snapshots_are_not_rewritten_by_commander_service(monkeypatch):
    called = {"upsert": False}
    monkeypatch.setattr(
        mge_commander_service.mge_commander_dal,
        "fetch_commander_by_name",
        lambda name: None,
    )

    def _upsert(**kwargs):
        called["upsert"] = True
        return {
            "CommanderId": kwargs["commander_id"],
            "CommanderName": kwargs["commander_name"],
            "VariantId": kwargs["variant_id"],
            "IsActive": kwargs["is_active"],
        }

    monkeypatch.setattr(
        mge_commander_service.mge_commander_dal, "upsert_commander_assignment", _upsert
    )
    monkeypatch.setattr(
        mge_commander_service.mge_cache,
        "refresh_mge_caches",
        lambda: {"commanders": True, "variant_commanders": True},
    )

    result = mge_commander_service.save_commander_assignment(
        commander_id=12,
        commander_name="Future Name",
        variant_id=1,
        is_active=True,
    )

    assert result.success is True
    assert called["upsert"] is True
