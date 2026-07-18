from __future__ import annotations

from dataclasses import replace
from datetime import UTC, date, datetime, timedelta, timezone
from io import BytesIO
import os
from pathlib import Path
import time

from PIL import Image, ImageDraw
import pytest

from player_self_service import stats_renderer
from player_self_service.stats_models import (
    PersonalStatsMetrics,
    PersonalStatsPayload,
    StatsCoverage,
    StatsDailyPoint,
    StatsGovernorOption,
    StatsMetricSummary,
    StatsMode,
    StatsPeriod,
    StatsResultState,
    StatsScopeType,
    StatsWindow,
)
from player_self_service.stats_renderer import render_personal_stats_card
from ui.views.player_self_service_stats_views import build_personal_stats_fallback_embed


def _metric(total: int, *, daily: tuple[int, ...] = (-5, 10)) -> StatsMetricSummary:
    points = tuple(
        StatsDailyPoint(date(2026, 7, 13 + index), value) for index, value in enumerate(daily)
    )
    peak = max(points, key=lambda point: point.value) if points else None
    return StatsMetricSummary(
        total=total,
        reporting_days=len(points),
        expected_days=3,
        daily=points,
        peak_date=peak.reporting_date if peak else None,
        peak_value=peak.value if peak else None,
    )


def _payload() -> PersonalStatsPayload:
    negative = _metric(-25)
    positive = _metric(75)
    metrics = PersonalStatsMetrics(
        power_change=positive,
        troop_power_change=negative,
        rss_gathered=negative,
        rss_assisted=positive,
        helps=positive,
        build_activity=negative,
        tech_donations=positive,
        forts_total=positive,
        forts_launched=negative,
        forts_joined=positive,
        kill_points=positive,
        t4_kills=positive,
        t5_kills=negative,
        t4_t5_kills=negative,
        deads=positive,
        healed_troops=positive,
        period_end_power=123_456_789,
        period_end_troop_power=98_765_432,
        period_end_date=date(2026, 7, 15),
    )
    return PersonalStatsPayload(
        discord_user_id=42,
        period=StatsPeriod.THIS_WEEK,
        window=StatsWindow(date(2026, 7, 13), date(2026, 7, 15)),
        stats_anchor_date=date(2026, 7, 15),
        scope_type=StatsScopeType.SELECTED,
        scope_governor_ids=(111,),
        scope_label="Governor 名称 with a deliberately long Unicode identity (2441482)",
        governor_options=(StatsGovernorOption(111, "Governor 名称", "Main", True),),
        duplicate_id_warning=True,
        registry_fingerprint=(("Main", 111),),
        coverage=StatsCoverage(3, 2, 1, 1, 3, 2, 1, 1),
        state=StatsResultState.PARTIAL,
        metrics=metrics,
        data_refreshed_at_utc=datetime(2026, 7, 15, 16, 25, 30, tzinfo=UTC),
        generated_at_utc=datetime(2026, 7, 15, 16, 30, 45, tzinfo=UTC),
    )


@pytest.mark.parametrize("mode", tuple(StatsMode))
def test_all_modes_render_one_opaque_1702x924_png_with_stable_filename(mode) -> None:
    rendered = render_personal_stats_card(
        _payload(),
        mode=mode,
        display_name="Invoking Player 🚀",
        avatar_bytes=b"not-an-image",
    )

    assert rendered.filename == "me_stats_42.png"
    assert rendered.width == 1702
    assert rendered.height == 924
    with Image.open(BytesIO(rendered.image_bytes)) as image:
        assert image.format == "PNG"
        assert image.size == (1702, 924)
        assert image.mode == "RGB"
        output_dir = os.environ.get("PHASE6_VISUAL_OUTPUT_DIR")
        if output_dir:
            destination = Path(output_dir)
            destination.mkdir(parents=True, exist_ok=True)
            image.save(destination / f"me_stats_{mode.value}_original.png")
            for label, width in (("desktop", 960), ("mobile", 430)):
                height = round(width * image.height / image.width)
                preview = image.resize((width, height), Image.Resampling.LANCZOS)
                try:
                    preview.save(destination / f"me_stats_{mode.value}_{label}.png")
                finally:
                    preview.close()


def test_activity_one_point_and_no_point_series_render_without_fake_trend() -> None:
    payload = _payload()
    one_point = _metric(5, daily=(5,))
    no_points = StatsMetricSummary(total=None, reporting_days=0, expected_days=3)
    metrics = payload.metrics
    changed = PersonalStatsMetrics(
        **{
            **{field: getattr(metrics, field) for field in metrics.__dataclass_fields__},
            "rss_gathered": one_point,
            "rss_assisted": no_points,
            "forts_total": one_point,
            "forts_launched": no_points,
            "forts_joined": no_points,
        }
    )
    payload = PersonalStatsPayload(
        **{
            **{field: getattr(payload, field) for field in payload.__dataclass_fields__},
            "metrics": changed,
        }
    )

    rendered = render_personal_stats_card(payload, mode=StatsMode.ACTIVITY, display_name="Player")

    assert rendered.image_bytes.startswith(b"\x89PNG")


def test_activity_keeps_only_fort_total_box_and_all_three_fort_chart_series(monkeypatch) -> None:
    metric_labels: list[str] = []
    charts: list[tuple[str, tuple[str, ...], date, date]] = []
    monkeypatch.setattr(
        stats_renderer,
        "_metric_box",
        lambda _draw, _box, label, _metric, **_kwargs: metric_labels.append(label),
    )
    monkeypatch.setattr(
        stats_renderer,
        "_draw_chart",
        lambda _draw, _box, title, series, **kwargs: charts.append(
            (
                title,
                tuple(label for label, _metric in series),
                kwargs["start_date"],
                kwargs["end_date"],
            )
        ),
    )

    stats_renderer._activity(object(), _payload())

    assert "Forts total" in metric_labels
    assert "Forts launched" not in metric_labels
    assert "Forts joined" not in metric_labels
    assert (
        "FORT DAILY TREND",
        ("Total", "Launched", "Joined"),
        date(2026, 7, 13),
        date(2026, 7, 15),
    ) in charts
    assert {chart[2:] for chart in charts} == {(date(2026, 7, 13), date(2026, 7, 15))}


def test_combat_adds_requested_three_series_daily_trend(monkeypatch) -> None:
    charts: list[tuple[str, tuple[str, ...], date, date]] = []
    monkeypatch.setattr(stats_renderer, "_metric_box", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        stats_renderer,
        "_draw_chart",
        lambda _draw, _box, title, series, **kwargs: charts.append(
            (
                title,
                tuple(label for label, _metric in series),
                kwargs["start_date"],
                kwargs["end_date"],
            )
        ),
    )

    stats_renderer._combat(object(), _payload())

    assert charts == [
        (
            "COMBAT DAILY TREND",
            ("T4+T5", "Deads", "Healed"),
            date(2026, 7, 13),
            date(2026, 7, 15),
        )
    ]


def test_chart_uses_even_selected_window_ticks_without_repeated_metric_summaries(
    monkeypatch,
) -> None:
    image = Image.new("RGBA", (800, 320), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    labels: list[str] = []
    monkeypatch.setattr(
        stats_renderer,
        "_font_text",
        lambda _draw, _xy, value, **_kwargs: labels.append(str(value)),
    )
    start = date(2026, 1, 19)
    end = date(2026, 7, 17)

    stats_renderer._draw_chart(
        draw,
        (10, 10, 790, 310),
        "DAILY TREND",
        (("Series A", _metric(75)), ("Series B", _metric(-25))),
        start_date=start,
        end_date=end,
    )

    expected_ticks = tuple(
        f"{value:%d %b}" for value in stats_renderer._axis_tick_dates(start, end)
    )
    assert expected_ticks == tuple(label for label in labels if label in expected_ticks)
    assert expected_ticks[0] == "19 Jan"
    assert expected_ticks[-1] == "17 Jul"
    assert len(expected_ticks) == 5
    assert "Series A" in labels and "Series B" in labels
    assert not any("total " in label or "avg " in label or "peak " in label for label in labels)
    image.close()


def test_data_refresh_text_uses_payload_refresh_in_utc_without_generated_wording() -> None:
    payload = replace(
        _payload(),
        data_refreshed_at_utc=datetime(
            2026,
            7,
            15,
            18,
            30,
            45,
            tzinfo=timezone(timedelta(hours=2)),
        ),
    )

    label = stats_renderer._data_refresh_text(payload)

    assert label == "Data last refreshed 15 Jul 2026 16:30:45 UTC"
    assert "Generated" not in label
    assert "Stats anchor" not in label


def test_partial_coverage_text_names_incomplete_source() -> None:
    assert stats_renderer._coverage_text(_payload()) == "Stats 2/3 • Activity 1/3 • Forts 1/3 days"

    complete_but_partial = replace(
        _payload(),
        coverage=StatsCoverage(3, 3, 1, 1, 3, 3, 3, 3),
    )
    assert stats_renderer._coverage_text(complete_but_partial).endswith("Source values incomplete")


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        (20_569_467.2, "+20.57M"),
        (479_819.8, "+479.82K"),
        (4_130.3, "+4.13K"),
        (84.5, "+84.5"),
        (17.0, "+17"),
        (-20_569_467.2, "-20.57M"),
    ),
)
def test_compact_average_values_match_headline_scale(value: float, expected: str) -> None:
    assert stats_renderer._compact(value, signed=True) == expected


def test_font_text_can_align_fitted_text_to_shared_right_edge(monkeypatch) -> None:
    image = Image.new("RGBA", (400, 100), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    drawn_at: list[tuple[int, int]] = []

    def capture_draw_text(_draw, xy, *_args, **_kwargs) -> None:
        drawn_at.append(xy)

    monkeypatch.setattr(stats_renderer.visual_text, "draw_text", capture_draw_text)
    stats_renderer._font_text(
        draw,
        (100, 20),
        "Aligned",
        width=200,
        size=20,
        right_align=True,
    )

    assert drawn_at[0][0] == drawn_at[1][0] + 2
    font = stats_renderer.visual_text.fit_font(draw, "Aligned", max_width=200, size=20, min_size=12)
    assert drawn_at[1][0] + stats_renderer.visual_text.text_width(draw, "Aligned", font=font) == 300
    image.close()


def test_all_linked_coverage_text_uses_account_days() -> None:
    payload = replace(
        _payload(),
        scope_type=StatsScopeType.ALL_LINKED,
        scope_governor_ids=(111, 222),
        scope_label="All Linked",
        coverage=StatsCoverage(3, 3, 2, 2, 6, 6, 5, 4),
    )

    assert stats_renderer._coverage_text(payload) == (
        "Stats 6/6 • Activity 5/6 • Forts 4/6 account-days"
    )


def test_activity_render_stays_within_explicit_worker_budget() -> None:
    started = time.perf_counter()

    rendered = render_personal_stats_card(
        _payload(), mode=StatsMode.ACTIVITY, display_name="Performance Player"
    )

    assert rendered.image_bytes.startswith(b"\x89PNG")
    assert time.perf_counter() - started < 3.5


def test_same_payload_fallback_contains_exact_dates_coverage_and_no_removed_features() -> None:
    embed = build_personal_stats_fallback_embed(_payload(), mode=StatsMode.ACTIVITY)
    serialized = " ".join(
        [embed.title or "", embed.description or "", *(field.value for field in embed.fields)]
    )

    assert "13 Jul 2026" in serialized
    assert "15 Jul 2026" in serialized
    assert "Stats account-days: 2/3" in serialized
    assert "RSS gathered" in serialized
    assert "Forts joined" in serialized
    assert "Ark" not in serialized
    assert "download" not in serialized.casefold()
    assert "export" not in serialized.casefold()


def test_fallback_footer_normalizes_generated_time_to_utc() -> None:
    payload = replace(
        _payload(),
        generated_at_utc=datetime(
            2026,
            7,
            15,
            18,
            30,
            45,
            tzinfo=timezone(timedelta(hours=2)),
        ),
    )

    embed = build_personal_stats_fallback_embed(payload, mode=StatsMode.OVERVIEW)

    assert embed.footer.text == "Private report • Generated 15 Jul 2026 16:30:45 UTC"


@pytest.mark.parametrize("mode", tuple(StatsMode))
def test_fallback_fields_respect_discord_limits(mode) -> None:
    embed = build_personal_stats_fallback_embed(_payload(), mode=mode)

    assert len(embed.fields) <= 25
    assert all(len(field.name) <= 256 and len(field.value) <= 1_024 for field in embed.fields)
