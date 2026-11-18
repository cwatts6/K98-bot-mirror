"""
MGE Signup Flow Configuration.

Controls which input fields are active in the live player signup flow.
Toggle fields here to enable/disable without rewriting the view each time.

Fields disabled in the simplified flow still exist in the DB schema and remain
readable/writable by admin and legacy code paths.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MgeSignupFlowConfig:
    """Configuration for the live MGE player signup flow."""

    # If True, show a combined "Priority (Rank)" dropdown that sets both
    # RequestPriority and PreferredRankBand in one selection.
    use_combined_priority_rank: bool = True

    # Individual field toggles (only relevant when use_combined_priority_rank=False)
    show_priority: bool = True
    show_preferred_rank: bool = False

    # Modal fields
    show_current_heads: bool = False
    show_kingdom_role: bool = False
    show_gear_text: bool = False
    show_armament_text: bool = False

    # Post-signup DM attachment flow
    send_dm_followup: bool = False


# Live configuration — simplified flow (v2)
MGE_SIGNUP_FLOW_CONFIG = MgeSignupFlowConfig()
