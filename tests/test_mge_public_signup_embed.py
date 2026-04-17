from __future__ import annotations

import os
import sys
import types

sys.modules.setdefault("aiofiles", types.ModuleType("aiofiles"))
os.environ.setdefault("OUR_KINGDOM", "0")
if "dotenv" not in sys.modules:
    dotenv = types.ModuleType("dotenv")
    dotenv.load_dotenv = lambda *args, **kwargs: None
    sys.modules["dotenv"] = dotenv

from mge import mge_embed_manager, mge_simplified_flow_service


def test_get_public_signup_rows_excludes_explicit_rejections(monkeypatch):
    monkeypatch.setattr(
        "mge.dal.mge_review_dal.fetch_signup_review_rows",
        lambda event_id: [
            {"SignupId": 2, "GovernorNameSnapshot": "Bravo", "RequestPriority": "High"},
            {"SignupId": 1, "GovernorNameSnapshot": "Alpha", "RequestPriority": "Medium"},
            {"SignupId": 3, "GovernorNameSnapshot": "Charlie", "RequestPriority": "Low"},
        ],
    )
    monkeypatch.setattr(
        "mge.dal.mge_roster_dal.fetch_event_awards",
        lambda event_id: [{"SignupId": 3, "AwardStatus": "rejected"}],
    )

    rows = mge_simplified_flow_service.get_public_signup_rows(101)

    assert [row["GovernorNameSnapshot"] for row in rows] == ["Bravo", "Alpha"]


def test_build_signup_embed_is_names_only():
    embed = mge_embed_manager.build_mge_signup_embed(
        {
            "EventName": "Test MGE",
            "VariantName": "Infantry",
            "EventMode": "controlled",
            "Status": "signup_open",
            "RulesText": "Rule 1",
        },
        public_signup_names=["Alpha", "Bravo"],
    )

    values = "\n".join(field.value for field in embed.fields)
    assert "Alpha" in values
    assert "Bravo" in values
    assert "#1" not in values
    assert "Waitlist" not in values
    assert "target:" not in values
