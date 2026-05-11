import pytest

from inventory import profile_service
from inventory.vip_levels import InventoryVipLevel


@pytest.mark.asyncio
async def test_normal_user_can_update_vip_for_registered_governor(monkeypatch):
    calls = {}

    async def _can_import(**kwargs):
        calls["permission"] = kwargs
        return True

    def _upsert(**kwargs):
        calls["upsert"] = kwargs

    monkeypatch.setattr(profile_service, "user_can_import_for_governor", _can_import)
    monkeypatch.setattr(
        profile_service.inventory_profile_dal,
        "upsert_inventory_vip",
        _upsert,
    )

    profile = await profile_service.update_inventory_vip(
        discord_user_id=42,
        governor_id=111,
        vip_level_code=InventoryVipLevel.VIP_17.value,
    )

    assert calls["permission"]["discord_user_id"] == 42
    assert calls["permission"]["governor_id"] == 111
    assert calls["upsert"]["vip_level_code"] == "VIP_17"
    assert profile.vip_level_code == "VIP_17"
    assert profile.vip_level_label == "VIP 17"


@pytest.mark.asyncio
async def test_normal_user_cannot_update_unregistered_governor(monkeypatch):
    async def _can_import(**_kwargs):
        return False

    monkeypatch.setattr(profile_service, "user_can_import_for_governor", _can_import)

    with pytest.raises(PermissionError, match="registered"):
        await profile_service.update_inventory_vip(
            discord_user_id=42,
            governor_id=999,
            vip_level_code=InventoryVipLevel.VIP_17.value,
        )


@pytest.mark.asyncio
async def test_fetch_inventory_profile_defaults_when_no_row(monkeypatch):
    monkeypatch.setattr(
        profile_service.inventory_profile_dal,
        "fetch_inventory_profile",
        lambda _governor_id: None,
    )

    profile = await profile_service.fetch_inventory_profile(111)

    assert profile.governor_id == 111
    assert profile.vip_level_code is None
    assert profile.uses_default_vip is True
