import asyncio
from datetime import UTC, datetime

from ui.views.ark_views import ArkConfirmationView


def test_confirmation_view_hides_checkin_button():
    async def _case():
        view = ArkConfirmationView(
            match_id=1,
            match_name="Ark Match — K98",
            match_datetime_utc=datetime(2026, 3, 7, 11, 0, tzinfo=UTC),
            on_check_in=lambda *_: None,
            on_emergency_withdraw=lambda *_: None,
            show_check_in=False,
        )
        labels = [getattr(c, "label", "") for c in view.children]
        assert "Check in" not in labels

    asyncio.run(_case())
