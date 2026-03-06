from __future__ import annotations

from typing import ClassVar

import pytest

from event_calendar.event_generator import load_overrides


def test_load_overrides_rejects_invalid_action():
    class _Cur:
        description: ClassVar[tuple[tuple[str], ...]] = (
            ("OverrideID",),
            ("IsActive",),
            ("TargetKind",),
            ("TargetID",),
            ("TargetOccurrenceStartUTC",),
            ("ActionType",),
            ("NewStartUTC",),
            ("NewEndUTC",),
            ("NewTitle",),
            ("NewVariant",),
            ("NewEmoji",),
            ("NewImportance",),
            ("NewDescription",),
            ("NewLinkURL",),
            ("NewChannelID",),
            ("NewSignupURL",),
            ("NewTags",),
        )

        def execute(self, *_a, **_k):
            return None

        def fetchall(self):
            return [
                (
                    "ov1",
                    1,
                    "rule",
                    "r1",
                    None,
                    "noop",
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                )
            ]

    class _Conn:
        def cursor(self):
            return _Cur()

    with pytest.raises(ValueError, match="action must be cancel\\|modify"):
        load_overrides(_Conn())
