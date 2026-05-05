from __future__ import annotations

from enum import StrEnum


class InventoryVipLevel(StrEnum):
    UNKNOWN = "UNKNOWN"
    VIP_14_OR_LESS = "VIP_14_OR_LESS"
    VIP_15 = "VIP_15"
    VIP_16 = "VIP_16"
    VIP_17 = "VIP_17"
    VIP_18 = "VIP_18"
    VIP_19 = "VIP_19"
    SVIP = "SVIP"


VIP_LABELS: dict[InventoryVipLevel, str] = {
    InventoryVipLevel.UNKNOWN: "Unknown / not set",
    InventoryVipLevel.VIP_14_OR_LESS: "VIP 14 or less",
    InventoryVipLevel.VIP_15: "VIP 15",
    InventoryVipLevel.VIP_16: "VIP 16",
    InventoryVipLevel.VIP_17: "VIP 17",
    InventoryVipLevel.VIP_18: "VIP 18",
    InventoryVipLevel.VIP_19: "VIP 19",
    InventoryVipLevel.SVIP: "SVIP",
}


def normalize_vip_level(value: str | InventoryVipLevel | None) -> InventoryVipLevel:
    if isinstance(value, InventoryVipLevel):
        return value
    normalized = (value or "").strip().upper().replace(" ", "_").replace("-", "_")
    aliases = {
        "": InventoryVipLevel.UNKNOWN,
        "UNKNOWN": InventoryVipLevel.UNKNOWN,
        "NONE": InventoryVipLevel.UNKNOWN,
        "NOT_SET": InventoryVipLevel.UNKNOWN,
        "VIP14": InventoryVipLevel.VIP_14_OR_LESS,
        "VIP_14": InventoryVipLevel.VIP_14_OR_LESS,
        "VIP_14_OR_LESS": InventoryVipLevel.VIP_14_OR_LESS,
        "14_OR_LESS": InventoryVipLevel.VIP_14_OR_LESS,
        "VIP15": InventoryVipLevel.VIP_15,
        "VIP_15": InventoryVipLevel.VIP_15,
        "VIP16": InventoryVipLevel.VIP_16,
        "VIP_16": InventoryVipLevel.VIP_16,
        "VIP17": InventoryVipLevel.VIP_17,
        "VIP_17": InventoryVipLevel.VIP_17,
        "VIP18": InventoryVipLevel.VIP_18,
        "VIP_18": InventoryVipLevel.VIP_18,
        "VIP19": InventoryVipLevel.VIP_19,
        "VIP_19": InventoryVipLevel.VIP_19,
        "SVIP": InventoryVipLevel.SVIP,
    }
    if normalized in aliases:
        return aliases[normalized]
    try:
        return InventoryVipLevel(normalized)
    except ValueError as exc:
        raise ValueError("VIP level must be Unknown, VIP 14 or less, VIP 15-19, or SVIP.") from exc


def vip_label(value: str | InventoryVipLevel | None) -> str:
    return VIP_LABELS[normalize_vip_level(value)]


def vip_note(value: str | InventoryVipLevel | None) -> str:
    level = normalize_vip_level(value)
    if level == InventoryVipLevel.UNKNOWN:
        return "VIP: default"
    if level == InventoryVipLevel.VIP_14_OR_LESS:
        return "VIP: <=14"
    if level == InventoryVipLevel.SVIP:
        return "VIP: SVIP"
    return f"VIP: {level.value.removeprefix('VIP_')}"


def persisted_vip_code(value: str | InventoryVipLevel | None) -> str | None:
    level = normalize_vip_level(value)
    return None if level == InventoryVipLevel.UNKNOWN else level.value
