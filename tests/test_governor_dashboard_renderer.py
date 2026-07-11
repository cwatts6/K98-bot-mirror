from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from io import BytesIO

from PIL import Image

from player_self_service import governor_dashboard_renderer as renderer
from player_self_service.governor_dashboard_models import (
    GovernorDashboardAccessDecision,
    GovernorDashboardActivityHonours,
    GovernorDashboardContext,
    GovernorDashboardFreshness,
    GovernorDashboardHistoricalHighlights,
    GovernorDashboardIdentity,
    GovernorDashboardLatestMetrics,
    GovernorDashboardPayload,
    GovernorDashboardProfileStatus,
    GovernorDashboardSelfView,
)


def _payload(
    *, name: str = "Governor One", alliance: str | None = "KD98"
) -> GovernorDashboardPayload:
    context = GovernorDashboardContext(
        viewer_discord_id=42,
        viewer_mode="self",
        selected_governor_id=123456789,
        selected_governor_name=name,
        is_linked_to_viewer=True,
        account_type_for_self_view="Main",
        access_decision=GovernorDashboardAccessDecision(True, "linked"),
        privacy_profile="self_view",
    )
    return GovernorDashboardPayload(
        context=context,
        identity=GovernorDashboardIdentity(
            governor_name=name,
            governor_id=123456789,
            alliance=alliance,
            civilisation="France",
            location_x=321,
            location_y=654,
        ),
        latest_metrics=GovernorDashboardLatestMetrics(
            power=123_850_000,
            kill_points=8_520_000_000,
            dead=26_220_000,
            helps=189_260,
            healed=357_160_000,
        ),
        historical_highlights=GovernorDashboardHistoricalHighlights(
            highest_acclaim=10_010_000,
            times_named_autarch=3,
            times_autarch_participated=11,
        ),
        activity_honours=GovernorDashboardActivityHonours(
            ark_joined=75,
            ark_won=28,
            ark_win_ratio=0.3733,
            ark_win_ratio_label="37.33%",
        ),
        profile_status=GovernorDashboardProfileStatus(conduct_score=100),
        freshness=GovernorDashboardFreshness(
            updated_at_utc=datetime(2026, 7, 10, 12, 30, tzinfo=UTC)
        ),
        available_actions=("accounts",),
        missing_fields=(),
        self_view=GovernorDashboardSelfView("Main", "VIP 19"),
    )


def test_renderer_outputs_stable_png_contract() -> None:
    rendered = renderer.render_governor_dashboard(_payload())

    assert rendered.filename == "governor_dashboard.png"
    assert (rendered.width, rendered.height) == (1180, 640)
    assert rendered.image_bytes.startswith(b"\x89PNG\r\n\x1a\n")
    with Image.open(BytesIO(rendered.image_bytes)) as image:
        assert image.size == (1180, 640)
        assert image.format == "PNG"


def test_renderer_draws_every_approved_field_and_no_olympia(monkeypatch) -> None:
    drawn: list[str] = []
    original = renderer.visual_text.draw_text

    def recording_draw(draw, xy, text, **kwargs):
        drawn.append(text)
        return original(draw, xy, text, **kwargs)

    monkeypatch.setattr(renderer.visual_text, "draw_text", recording_draw)
    renderer.render_governor_dashboard(_payload())
    output = " ".join(drawn)

    for expected in (
        "Governor One",
        "123456789",
        "KD98",
        "Main",
        "VIP 19",
        "France",
        "321:654",
        "POWER",
        "KILL POINTS",
        "HIGHEST ACCLAIM",
        "DEAD",
        "HELPS",
        "HEALED",
        "ARK JOINED",
        "ARK WON",
        "WIN RATIO",
        "NAMED AUTARCH",
        "AUTARCH PARTICIPATED",
        "CONDUCT SCORE",
    ):
        assert expected in output
    assert "Olympia" not in output


def test_renderer_handles_sparse_zero_negative_huge_and_unicode_values() -> None:
    payload = _payload(
        name="ãƒ… 义Vìper🦊‍🔥 with a deliberately very long governor name",
        alliance="联盟 à¹› with an exceptionally long alliance name",
    )
    payload = replace(
        payload,
        identity=replace(
            payload.identity,
            civilisation=None,
            location_x=None,
            location_y=None,
        ),
        latest_metrics=GovernorDashboardLatestMetrics(
            power=0,
            kill_points=-1,
            dead=10**30,
            helps=None,
            healed=0,
        ),
        historical_highlights=GovernorDashboardHistoricalHighlights(),
        activity_honours=GovernorDashboardActivityHonours(
            ark_joined=0, ark_won=0, ark_win_ratio=None, ark_win_ratio_label="N/A"
        ),
        profile_status=GovernorDashboardProfileStatus(conduct_score=None),
        freshness=GovernorDashboardFreshness(),
        self_view=None,
    )

    rendered = renderer.render_governor_dashboard(payload)
    with Image.open(BytesIO(rendered.image_bytes)) as image:
        assert image.size == (1180, 640)
        assert image.convert("RGB").getpixel((1100, 20)) != (0, 0, 0)


def test_renderer_places_optional_avatar_and_survives_invalid_avatar() -> None:
    avatar = BytesIO()
    Image.new("RGB", (64, 64), (240, 20, 30)).save(avatar, format="PNG")

    with_avatar = renderer.render_governor_dashboard(_payload(), avatar_bytes=avatar.getvalue())
    invalid = renderer.render_governor_dashboard(_payload(), avatar_bytes=b"not-an-image")

    with Image.open(BytesIO(with_avatar.image_bytes)) as image:
        red, green, blue = image.getpixel((184, 178))
        assert red > 200 and green < 80 and blue < 80
    assert invalid.image_bytes.startswith(b"\x89PNG")
