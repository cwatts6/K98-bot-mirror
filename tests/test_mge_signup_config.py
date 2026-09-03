"""Tests for mge_signup_config — MgeSignupFlowConfig defaults and singleton."""

from __future__ import annotations

from mge.mge_signup_config import MGE_SIGNUP_FLOW_CONFIG, MgeSignupFlowConfig


def test_config_default_values() -> None:
    cfg = MgeSignupFlowConfig()
    assert cfg.use_combined_priority_rank is True
    assert cfg.show_priority is True
    assert cfg.show_preferred_rank is False
    assert cfg.show_current_heads is False
    assert cfg.show_kingdom_role is False
    assert cfg.show_gear_text is False
    assert cfg.show_armament_text is False
    assert cfg.send_dm_followup is False


def test_live_singleton_is_simplified_flow() -> None:
    assert isinstance(MGE_SIGNUP_FLOW_CONFIG, MgeSignupFlowConfig)
    assert MGE_SIGNUP_FLOW_CONFIG.use_combined_priority_rank is True
    assert MGE_SIGNUP_FLOW_CONFIG.send_dm_followup is False


def test_config_is_frozen() -> None:
    cfg = MgeSignupFlowConfig()
    try:
        cfg.send_dm_followup = True  # type: ignore[misc]
        raise AssertionError("Should have raised FrozenInstanceError")
    except Exception as exc:
        assert "frozen" in str(exc).lower() or "cannot" in str(exc).lower()
