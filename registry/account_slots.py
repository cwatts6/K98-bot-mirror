"""Canonical account slot ordering shared across services and UI helpers.

This module is intentionally discord-free so it can be imported safely from
maintenance scripts, unit tests, and any service layer code that must not
pull in discord.py transitively.
"""

from __future__ import annotations

# 16-slot canonical ordering: Main, Alt 1-5, Farm 1-10.
# Both account_picker.ACCOUNT_ORDER and the governor_account_service import this.
ACCOUNT_ORDER: list[str] = (
    ["Main"] + [f"Alt {i}" for i in range(1, 6)] + [f"Farm {i}" for i in range(1, 11)]
)
