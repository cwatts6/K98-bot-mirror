from __future__ import annotations

import datetime
from pathlib import Path

if not hasattr(datetime, "UTC"):
    datetime.UTC = datetime.UTC


def test_ark_preference_command_names_present():
    text = Path("commands/ark_cmds.py").read_text(encoding="utf-8")
    assert 'name="ark_set_preference"' in text
    assert 'name="ark_clear_preference"' in text
