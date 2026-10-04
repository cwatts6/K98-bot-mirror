import pytest

from inventory.vip_levels import (
    InventoryVipLevel,
    normalize_vip_level,
    persisted_vip_code,
    vip_label,
    vip_note,
)


def test_normalize_vip_level_accepts_supported_values():
    assert normalize_vip_level(None) == InventoryVipLevel.UNKNOWN
    assert normalize_vip_level("VIP 14 or less") == InventoryVipLevel.VIP_14_OR_LESS
    assert normalize_vip_level("vip_17") == InventoryVipLevel.VIP_17
    assert normalize_vip_level("SVIP") == InventoryVipLevel.SVIP


def test_vip_label_and_note_keep_unknown_as_default():
    assert persisted_vip_code(None) is None
    assert vip_label(None) == "Unknown / not set"
    assert vip_note(None) == "VIP: default"


def test_invalid_vip_level_is_rejected():
    with pytest.raises(ValueError, match="VIP level"):
        normalize_vip_level("VIP 20")
