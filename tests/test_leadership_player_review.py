from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from PIL import Image, ImageDraw
import pytest

from core.leadership_player_permissions import LeadershipPlayerAuthorization
from leadership_player_review import dal, renderer, service
from leadership_player_review.models import (
    ActivityIndex,
    ActivityMetric,
    AliasRecord,
    AllianceEpisode,
    HistoryDepth,
    KvkIndex,
    KvkPerformance,
    LastActive,
    LeadershipPlayerPayload,
    LinkedGovernor,
    LookupCandidate,
    ReviewHeader,
    ScanPresence,
    SourceCoverage,
)
from leadership_player_review.record_paging import (
    alias_pages,
    alliance_pages,
    record_page_count,
)
from ui.views.leadership_player_review_views import (
    LeadershipChangePlayerModal,
    LeadershipPlayerAmbiguityView,
    LeadershipPlayerView,
    build_fallback_embed,
)

NOW = datetime(2026, 7, 19, 12, tzinfo=UTC)


def _candidate(governor_id: int, name: str, *, alliance: str = "K98") -> LookupCandidate:
    return LookupCandidate(
        governor_id=governor_id,
        governor_name=name,
        normalized_name=service.normalize_name(name),
        current_name=name,
        current_alliance=alliance,
        last_scan_at_utc=NOW,
        present_latest=True,
        is_current_name=True,
        last_seen=NOW,
    )


def _metric(order: int, code: str) -> ActivityMetric:
    return ActivityMetric(
        order=order,
        code=code,
        current_total=Decimal(order * 1000),
        current_valid_days=90,
        current_average=Decimal(order * 10),
        previous_total=Decimal(order * 900),
        previous_valid_days=90,
        previous_average=Decimal(order * 9),
        comparison_mode="EQUAL_PERIOD",
        comparison_percent=Decimal("11.1"),
        expected_units=90,
        missing_units=0,
        reset_count=0,
        available=True,
        kingdom_rank=order,
        cohort_count=100,
        percentile=Decimal(100 - order),
        top_percent=Decimal(order),
    )


def _kvk(kvk_no: int) -> KvkPerformance:
    return KvkPerformance(
        kvk_no=kvk_no,
        kvk_name=f"KVK {kvk_no} Name",
        governor_id=123,
        governor_name="Governor Alpha",
        kvk_rank=10,
        t4_t5_kills=1_000_000,
        kill_target=900_000,
        kill_target_percent=Decimal("111.1"),
        kill_points=2_000_000,
        deads=10_000,
        dead_target=10_000,
        dead_target_percent=Decimal("100"),
        healed=50_000,
        kp_loss=1_000_000,
        tanking_score=Decimal("198.0198"),
        acclaim=20_000,
        acclaim_rank=6,
        dkp=100_000,
        dkp_target=100_000,
        dkp_target_percent=Decimal("100"),
        prekvk_points=90_000,
        prekvk_rank=4,
        honor_points=80_000,
        honor_rank=5,
        exempt=False,
        engaged=True,
        healed_rank=2,
        tanking_rank=3,
        engaged_cohort_count=80,
        tanking_cohort_count=70,
        final_data_at_utc=NOW - timedelta(days=kvk_no),
        final_output_state="OUTPUT_COMPLETE",
        finalization_basis="AUDIT_PROOF",
        personal_completed_kvk_best_acclaim=25_000,
        kill_points_rank=4,
        deads_rank=12,
        healed_data_available=True,
    )


def _payload(*, page="overview", aliases=1, episodes=1, linked=2) -> LeadershipPlayerPayload:
    header = ReviewHeader(
        governor_id=123,
        governor_name="Governor Alpha",
        current_alliance="K98",
        current_power=123_456_789,
        current_power_rank=3,
        city_hall=25,
        effective_now_utc=NOW,
        anchor_date=date(2026, 7, 19),
        current_start_date=date(2026, 4, 21),
        current_end_date=date(2026, 7, 19),
        previous_start_date=date(2026, 1, 21),
        previous_end_date=date(2026, 4, 20),
        period_days=90,
        latest_complete_scan_order=100,
        latest_complete_scan_at_utc=NOW,
        latest_governor_scan_order=100,
        latest_governor_scan_at_utc=NOW,
        present_latest=True,
        first_observed_date=date(2025, 1, 1),
        first_observed_offset_days=None,
        location_x=123,
        location_y=456,
        location_updated_at_utc=NOW - timedelta(hours=3),
        shield_ends_at_utc=NOW + timedelta(hours=4),
    )
    metrics = tuple(
        _metric(index, code)
        for index, code in enumerate(
            (
                "FORTS_TOTAL",
                "HELPS",
                "TECH_DONATIONS",
                "RSS_GATHERED",
                "BUILDING_MINUTES",
                "POWER_CHANGE",
            ),
            start=1,
        )
    )
    return LeadershipPlayerPayload(
        header=header,
        freshness="CURRENT",
        period_days=90,
        page=page,
        presence=(ScanPresence("CURRENT", 90, 89, 90, 89),),
        coverage=(
            SourceCoverage("CURRENT", "STATS_SCANS", True, 90, 90, 0, 0, "COMPLETE"),
            SourceCoverage("CURRENT", "ALLIANCE_ACTIVITY", True, 90, 90, 0, 0, "COMPLETE"),
            SourceCoverage("CURRENT", "RALLY_COMPLETED_DATES", True, 90, 90, 0, 0, "COMPLETE"),
        ),
        metrics=metrics,
        activity_index=ActivityIndex(
            Decimal("88.5"),
            4,
            100,
            tuple(
                (name, Decimal("80"))
                for name in ("Forts", "Helps", "Tech", "RSS", "Building", "Power")
            ),
            "AVAILABLE",
        ),
        history_depth=(
            HistoryDepth(
                "KINGDOM_SCANS", "SCANS", date(2024, 1, 1), date(2026, 7, 19), 400, 2, 3, "OBSERVED"
            ),
        ),
        aliases=tuple(
            AliasRecord(123, f"Alias {index}", NOW - timedelta(days=20), NOW, 5)
            for index in range(aliases)
        ),
        alliance_episodes=tuple(
            AllianceEpisode(
                123, index, f"A{index}", date(2026, 1, 1), date(2026, 2, 1), 5, index == episodes
            )
            for index in range(1, episodes + 1)
        ),
        linked_governors=tuple(
            LinkedGovernor(123 + index, f"Governor {index}", current=index == 0)
            for index in range(linked)
        ),
        kvk_rows=(_kvk(15), _kvk(14), _kvk(13)),
        prompts=(
            "Forts is the strongest result, ranked #1 of 100 in the kingdom.",
            "Review Power Change with the player; it is the weakest result, ranked #6 of 100 in the kingdom.",
        ),
        warnings=(),
        generated_at_utc=NOW,
        last_active=LastActive(
            governor_id=123,
            effective_utc_date=NOW.date(),
            history_start_date=date(2024, 7, 31),
            history_end_date=NOW.date(),
            last_active_date=NOW.date() - timedelta(days=1),
            activity_state="ACTIVE",
            qualifying_source_code="HELPS",
            qualifying_scan_order=99,
            compared_complete_scans=88,
            history_days=720,
        ),
        kvk_index=replace(
            service._kvk_index((_kvk(15), _kvk(14), _kvk(13))),
            rank=5,
            cohort_count=308,
        ),
    )


def test_name_normalization_exact_and_ambiguous_lookup(monkeypatch) -> None:
    rows = (
        _candidate(1, "Ａｌｐｈａ   One"),
        _candidate(2, "Alpha One"),
    )

    async def directory(*, refresh=False):
        return rows

    monkeypatch.setattr(service, "_lookup_directory", directory)
    assert service.normalize_name("  Alpha\tOne ") == "alpha one"

    result = asyncio.run(service.resolve_name(" alpha one "))
    assert result.status == "matches"
    assert {row.governor_id for row in result.candidates} == {1, 2}


def test_lookup_input_shape_rejects_neither_both_and_non_positive() -> None:
    assert service.validate_command_inputs(None, None)
    assert service.validate_command_inputs(123, "Alpha")
    assert service.validate_command_inputs(-1, None)
    assert service.validate_command_inputs(0, None)
    assert service.validate_command_inputs(0, "Alpha")
    assert service.validate_command_inputs(10**30, None)
    assert service.validate_command_inputs(None, "x" * 101)
    assert service.validate_command_inputs(123, None) is None


def test_governor_not_found_message_is_clear_and_specific() -> None:
    assert service.governor_not_found_message(123) == (
        "No governor with ID `123` was found in the database. " "Please check the ID and try again."
    )


def test_dal_exact_governor_existence_contract_is_parameterized(monkeypatch) -> None:
    executed: list[tuple[str, tuple[int]]] = []

    class _Cursor:
        timeout = None
        description = (("GovernorID",), ("ExistsInDatabase",))

        def execute(self, statement, parameters) -> None:
            executed.append((statement, parameters))

        def fetchall(self):
            return [(123, True)]

    class _Connection:
        def __enter__(self):
            return self

        def __exit__(self, *_args) -> None:
            return None

        def cursor(self):
            return _Cursor()

    monkeypatch.setattr(dal, "get_conn_with_retries", _Connection)

    assert dal.fetch_governor_exists(123) is True
    assert executed == [
        (
            "EXEC dbo.usp_LeadershipPlayerGovernorExists @GovernorID = ?;",
            (123,),
        )
    ]


def test_stale_wins_over_partial_and_no_data_wins_without_presence() -> None:
    payload = _payload()
    partial = replace(payload.coverage[0], state="PARTIAL", missing_units=1)
    stale_header = replace(
        payload.header,
        latest_governor_scan_at_utc=NOW - timedelta(hours=49),
    )

    assert service._freshness(stale_header, (partial,), payload.presence) == "STALE"
    assert service._freshness(payload.header, (partial,), payload.presence) == "PARTIAL"
    assert (
        service._freshness(
            payload.header,
            payload.coverage,
            (ScanPresence("CURRENT", 90, 0, 90, 0),),
        )
        == "NO DATA"
    )


def test_leadership_review_returns_one_plain_english_insight_and_action() -> None:
    payload = _payload()

    insight, action = service._prompts(
        freshness=payload.freshness,
        header=payload.header,
        metrics=payload.metrics,
        activity_index=payload.activity_index,
    )

    assert insight == "Forts is the strongest result, ranked #1 of 100 in the kingdom."
    assert action == (
        "Review Power Change with the player; it is the weakest result, "
        "ranked #6 of 100 in the kingdom."
    )


def test_leadership_review_recommends_no_player_action_when_safeguarded() -> None:
    payload = _payload()

    assert service._prompts(
        freshness="PARTIAL",
        header=payload.header,
        metrics=payload.metrics,
        activity_index=payload.activity_index,
    ) == (
        "The data is not complete enough for a fair player comparison.",
        "No player action is recommended from this review.",
    )


@pytest.mark.parametrize("page", ["overview", "activity", "kvk", "record"])
def test_renderer_produces_accepted_card_geometry_for_every_page(page) -> None:
    rendered = renderer.render_leadership_player(_payload(page=page))
    with Image.open(BytesIO(rendered.image_bytes)) as image:
        assert image.size == (1702, 924)
    assert rendered.filename.endswith(f"_{page}_90d.png")


def test_activity_renderer_labels_reporting_average_per_day(monkeypatch) -> None:
    rendered_text: list[str] = []
    original_text = renderer._text

    def capture_text(*args, **kwargs):
        rendered_text.append(args[2])
        return original_text(*args, **kwargs)

    monkeypatch.setattr(renderer, "_text", capture_text)
    renderer.render_leadership_player(_payload(page="activity"))

    averages = [text for text in rendered_text if text.startswith("Average ")]
    assert len(averages) == 6
    assert all(text.endswith("/valid day") for text in averages)


def test_activity_renderer_explains_counter_reset_exclusion(monkeypatch) -> None:
    rendered_text: list[str] = []
    original_text = renderer._text

    def capture_text(*args, **kwargs):
        rendered_text.append(args[2])
        return original_text(*args, **kwargs)

    payload = _payload(page="activity")
    payload = replace(
        payload, metrics=(replace(payload.metrics[0], reset_count=2), *payload.metrics[1:])
    )
    monkeypatch.setattr(renderer, "_text", capture_text)

    renderer.render_leadership_player(payload)

    assert "Coverage 90/90" in rendered_text
    assert "2 counter reset(s); decreases not counted" in rendered_text


def test_overview_renderer_uses_equal_scorecards_and_balanced_lower_panels(monkeypatch) -> None:
    panels: list[tuple[int, int, int, int]] = []
    original_panel = renderer._panel

    def capture_panel(draw, box):
        panels.append(box)
        return original_panel(draw, box)

    monkeypatch.setattr(renderer, "_panel", capture_panel)
    renderer.render_leadership_player(_payload(page="overview"))

    assert panels[-6:-2] == [
        (70, 226, 444, 486),
        (466, 226, 840, 486),
        (862, 226, 1236, 486),
        (1258, 226, 1632, 486),
    ]
    assert panels[-2:] == [(70, 508, 840, 810), (862, 508, 1632, 810)]


@pytest.mark.parametrize("page", ["activity"])
def test_unavailable_metric_does_not_render_sql_zero_as_genuine_zero(monkeypatch, page) -> None:
    payload = _payload(page=page)
    unavailable_forts = replace(
        payload.metrics[0],
        current_total=Decimal(0),
        current_valid_days=0,
        current_average=None,
        missing_units=90,
        available=False,
        kingdom_rank=None,
        cohort_count=None,
        percentile=None,
        top_percent=None,
    )
    payload = replace(payload, metrics=(unavailable_forts, *payload.metrics[1:]))
    rendered_text: list[str] = []
    original_text = renderer._text

    def capture_text(*args, **kwargs):
        rendered_text.append(str(args[2]))
        return original_text(*args, **kwargs)

    monkeypatch.setattr(renderer, "_text", capture_text)
    renderer.render_leadership_player(payload)

    assert "—" in rendered_text
    assert (
        build_fallback_embed(payload)
        .fields[-1]
        .value.splitlines()[0]
        .endswith("— · rank unavailable")
    )


@pytest.mark.parametrize("page", ["activity"])
def test_partial_metric_renders_observed_total_without_rank(monkeypatch, page) -> None:
    payload = _payload(page=page)
    partial_tech = replace(
        payload.metrics[2],
        current_total=Decimal("801060"),
        current_valid_days=79,
        current_average=Decimal("10140"),
        missing_units=11,
        available=False,
        kingdom_rank=None,
        cohort_count=None,
        percentile=None,
        top_percent=None,
    )
    payload = replace(payload, metrics=(*payload.metrics[:2], partial_tech, *payload.metrics[3:]))
    rendered_text: list[str] = []
    original_text = renderer._text

    def capture_text(*args, **kwargs):
        rendered_text.append(str(args[2]))
        return original_text(*args, **kwargs)

    monkeypatch.setattr(renderer, "_text", capture_text)
    renderer.render_leadership_player(payload)

    assert renderer.current_metric_total(partial_tech) == Decimal("801060")
    assert "801.06K" in rendered_text
    assert (
        build_fallback_embed(payload)
        .fields[-1]
        .value.splitlines()[2]
        .endswith("801060 · rank unavailable")
    )


def test_partial_metric_renders_genuine_zero_when_observations_exist() -> None:
    partial_zero = replace(
        _payload().metrics[2],
        current_total=Decimal(0),
        current_valid_days=79,
        current_average=Decimal(0),
        missing_units=11,
        available=False,
    )

    assert renderer.current_metric_total(partial_zero) == Decimal(0)


def test_alias_pages_group_id_once_and_keep_nine_aliases_on_one_page() -> None:
    aliases = tuple(
        AliasRecord(
            35_711_701,
            name,
            datetime(2024, 5, 16),
            datetime(2026, 7, 21),
            index,
        )
        for index, name in enumerate(
            (
                "TroIl",
                "JohnPaulV",
                "TrolI",
                "Stylebender",
                "TroII",
                "NICOLAl",
                "RaBBit",
                "Killionaire",
                "M4t1c0",
            ),
            start=1,
        )
    )

    pages = alias_pages(aliases)

    assert len(pages) == 1
    assert sum(row.is_heading for row in pages[0]) == 1
    assert [row.alias.governor_name for row in pages[0] if row.alias] == [
        row.governor_name for row in aliases
    ]
    assert record_page_count(linked_count=0, aliases=aliases, episodes=()) == 1


def test_alias_pages_repeat_group_heading_only_when_group_continues() -> None:
    aliases = tuple(AliasRecord(123, f"Alias {index}", NOW, NOW, 1) for index in range(10))

    pages = alias_pages(aliases)

    assert [len(page) for page in pages] == [10, 2]
    assert all(page[0].is_heading for page in pages)


def test_alliance_pages_group_governor_ids_and_preserve_every_episode() -> None:
    episodes = tuple(
        AllianceEpisode(
            123 if index < 10 else 456,
            index,
            f"A{index}",
            date(2026, 1, 1),
            date(2026, 2, 1),
            index,
            False,
        )
        for index in range(1, 15)
    )

    pages = alliance_pages(episodes)

    assert len(pages) == 2
    assert all(page[0].is_heading for page in pages)
    assert [row.episode for page in pages for row in page if row.episode] == list(episodes)
    assert record_page_count(linked_count=0, aliases=(), episodes=episodes) == 2


def test_overview_promotes_presence_last_active_and_removes_duplicate_metrics(
    monkeypatch,
) -> None:
    rendered_text: list[str] = []
    original_text = renderer._text

    def capture_text(*args, **kwargs):
        rendered_text.append(str(args[2]))
        return original_text(*args, **kwargs)

    monkeypatch.setattr(renderer, "_text", capture_text)
    payload = _payload(page="overview")
    payload = replace(payload, header=replace(payload.header, shield_ends_at_utc=None))
    renderer.render_leadership_player(payload)

    assert "PRESENCE" in rendered_text
    assert "89 / 90 scans" in rendered_text
    assert "99%" in rendered_text
    assert "LAST ACTIVE" in rendered_text
    assert "18 Jul 2026" in rendered_text
    assert "UTC calendar date" not in rendered_text
    assert "KVK INDEX" in rendered_text
    assert "LATEST LOCATION" in rendered_text
    assert "INACTIVE" in rendered_text
    assert "INSIGHT" in rendered_text
    assert "ACTION" in rendered_text
    assert "90 days • 21 Apr 2026–19 Jul 2026" in rendered_text
    assert "Previous 21 Jan 2026–20 Apr 2026" in rendered_text
    assert "RANK" in rendered_text
    assert "3" in rendered_text
    assert not any(text.startswith("Presence 89/90 scans") for text in rendered_text)
    assert "Stats Scans 89/90" not in rendered_text
    assert not any(text.startswith("Prompts suppressed") for text in rendered_text)
    assert not {"FORTS TOTAL", "HELPS", "TECH DONATIONS"} & set(rendered_text)


def test_kvk_cards_keep_numeric_context_without_state_or_met_words(monkeypatch) -> None:
    rendered_text: list[str] = []
    original_text = renderer._text

    def capture_text(*args, **kwargs):
        rendered_text.append(str(args[2]))
        return original_text(*args, **kwargs)

    monkeypatch.setattr(renderer, "_text", capture_text)
    renderer.render_leadership_player(_payload(page="kvk"))
    combined = "\n".join(rendered_text)

    assert all(
        any(text.startswith(f"KVK {value} -") for text in rendered_text) for value in (15, 14, 13)
    )
    assert "111.1% Target" in combined
    assert "100.0% Target" in combined
    assert any(text == "KP: 2M" for text in rendered_text)
    assert "rank 12" in combined
    assert "Acclaim: 20K  •  rank 6" in combined
    assert "Healed: 50K  •  KP Loss: 1M" in combined
    assert "DKP:" not in combined
    assert "Pre-KVK:" not in combined
    assert "Honor:" not in combined
    assert "rank 4" not in combined
    assert "rank 2" not in combined
    assert "OUTPUT_COMPLETE" not in combined
    assert "Final " not in combined
    assert "NOT MET" not in combined
    assert "\nMET\n" not in f"\n{combined}\n"


def test_kvk_index_uses_approved_weights_without_capping() -> None:
    row = replace(
        _kvk(15),
        kill_target_percent=Decimal("205.5"),
        dead_target_percent=Decimal("88.4"),
        tanking_score=Decimal("117"),
    )

    result = service._kvk_index((row,))

    assert result.value == Decimal("164.380")
    assert result.scored_kvks == 1
    assert result.candidate_kvks == 1
    assert result.availability == "AVAILABLE"


@pytest.mark.parametrize("field", ("t4_t5_kills", "deads", "healed"))
def test_kvk_index_scores_an_observed_zero_as_zero(field: str) -> None:
    row = replace(_kvk(15), **{field: 0})

    result = service._kvk_index((row,))

    assert result.value == Decimal(0)
    assert result.per_kvk_scores == ((15, Decimal(0)),)


def test_kvk_index_averages_only_scoreable_non_exempt_completed_kvks() -> None:
    scored = replace(
        _kvk(15),
        kill_target_percent=Decimal("100"),
        dead_target_percent=Decimal("100"),
        tanking_score=Decimal("100"),
    )
    exempt = replace(_kvk(14), exempt=True)
    missing_healed_source = replace(_kvk(13), healed_data_available=False)

    result = service._kvk_index((scored, exempt, missing_healed_source))

    assert result.value == Decimal("100.00")
    assert result.scored_kvks == 1
    assert result.candidate_kvks == 3
    assert result.availability == "PARTIAL"
    assert result.per_kvk_scores == ((15, Decimal("100.00")), (14, None), (13, None))


def test_kvk_index_is_not_recorded_without_scoreable_rows() -> None:
    result = service._kvk_index(
        (
            replace(_kvk(13), healed_data_available=False),
            replace(_kvk(12), healed_data_available=None),
            replace(_kvk(11), exempt=True),
        )
    )

    assert result.value is None
    assert result.scored_kvks == 0
    assert result.availability == "NOT_RECORDED"


def test_kvk_normalisation_suppresses_uncaptured_or_zero_healed_tanking() -> None:
    uncaptured = service._normalise_kvk_performance(
        replace(_kvk(13), healed=0, kp_loss=0, healed_data_available=False)
    )
    observed_zero = service._normalise_kvk_performance(
        replace(_kvk(14), healed=0, kp_loss=0, healed_data_available=True)
    )

    assert uncaptured.healed is None
    assert uncaptured.kp_loss is None
    assert uncaptured.healed_rank is None
    assert uncaptured.tanking_score is None
    assert observed_zero.healed == 0
    assert observed_zero.tanking_score is None


def test_record_renderer_uses_consistent_footer_and_readable_alias_columns(monkeypatch) -> None:
    aliases = tuple(
        AliasRecord(
            35_711_701,
            name,
            datetime(2024, 5, 16),
            datetime(2026, 7, 21),
            577,
        )
        for name in ("TroIl", "JohnPaulV", "TrolI", "Stylebender", "TroII")
    )
    payload = replace(_payload(page="record", aliases=0, episodes=0, linked=0), aliases=aliases)
    calls: list[tuple[str, dict]] = []
    original_text = renderer._text

    def capture_text(*args, **kwargs):
        calls.append((str(args[2]), kwargs))
        return original_text(*args, **kwargs)

    monkeypatch.setattr(renderer, "_text", capture_text)
    renderer.render_leadership_player(payload)

    rendered = [text for text, _kwargs in calls]
    assert rendered.count("Governor ID 35711701") == 1
    assert all(name in rendered for name in ("TroIl", "JohnPaulV", "TrolI", "Stylebender", "TroII"))
    assert "1st 16 May 24" in rendered
    assert "last 21 Jul 26" in rendered
    assert not any(text.startswith("Latest X:Y") for text in rendered)
    assert not any(text.startswith("Stats Scans") for text in rendered)
    assert not any(text.startswith("Source freshness") for text in rendered)
    assert any(text.startswith("Data refreshed") for text in rendered)
    assert any(
        text.startswith("Generated ") and kwargs.get("right_align") is True
        for text, kwargs in calls
    )


@pytest.mark.asyncio
async def test_view_has_locked_rows_private_navigation_and_record_paging() -> None:
    payload = _payload(page="record", aliases=12, episodes=12, linked=12)
    view = LeadershipPlayerView(
        author_id=42,
        payload=payload,
        authorization=LeadershipPlayerAuthorization(True, basis="ADMIN_USER_ID"),
        correlation_id=uuid4(),
    )
    controls = {child.custom_id: child for child in view.children}

    assert [
        controls[f"leadership:player:page:{page}"].row
        for page in ("overview", "activity", "kvk", "record")
    ] == [0, 0, 0, 0]
    assert controls["leadership:player:period"].row == 1
    assert controls["leadership:player:period"].placeholder == "Timeslice"
    assert controls["leadership:player:linked"].row == 2
    assert controls["leadership:player:linked"].placeholder == "Active linked governors"
    assert controls["leadership:player:change"].row == 3
    assert "leadership:player:definitions" not in controls
    assert controls["leadership:player:record:previous"].row == 3
    assert controls["leadership:player:record:next"].row == 3
    assert controls["leadership:player:record:previous"].disabled is True
    assert controls["leadership:player:record:next"].disabled is False
    assert "leadership:player:current" not in controls
    assert callable(view.refresh)
    assert "leadership:player:refresh" not in controls
    linked_values = {option.value for option in controls["leadership:player:linked"].options}
    assert "g:123" not in linked_values
    assert all(
        "discord" not in option.description.lower()
        for option in controls["leadership:player:linked"].options
    )


@pytest.mark.asyncio
async def test_record_paging_controls_remain_visible_and_disabled_off_record_page() -> None:
    view = LeadershipPlayerView(
        author_id=42,
        payload=_payload(page="overview", aliases=12, episodes=12, linked=12),
        authorization=LeadershipPlayerAuthorization(True, basis="ADMIN_USER_ID"),
        correlation_id=uuid4(),
    )
    controls = {child.custom_id: child for child in view.children}

    assert controls["leadership:player:record:previous"].disabled is True
    assert controls["leadership:player:record:next"].disabled is True
    assert len([child for child in view.children if child.row == 3]) == 3


@pytest.mark.asyncio
async def test_ambiguity_selector_pages_without_exposing_identity_metadata() -> None:
    view = LeadershipPlayerAmbiguityView(
        author_id=42,
        candidates=tuple(_candidate(index, f"Duplicate {index}") for index in range(1, 27)),
        period_days=90,
        page="overview",
        authorization=LeadershipPlayerAuthorization(True, basis="ADMIN_USER_ID"),
        correlation_id=uuid4(),
    )

    assert len(view.selector.options) == 25
    assert view.ambiguity_previous.disabled is True
    assert view.ambiguity_next.disabled is False
    assert all(option.value.startswith("candidate:") for option in view.selector.options)
    assert all("discord" not in option.description.lower() for option in view.selector.options)

    view.selector_page = 1
    view._sync_selector_page()

    assert len(view.selector.options) == 1
    assert view.ambiguity_previous.disabled is False
    assert view.ambiguity_next.disabled is True


def test_fallback_uses_same_payload_without_discord_identity() -> None:
    embed = build_fallback_embed(_payload(page="kvk"))
    rendered = embed.to_dict()
    text = str(rendered).lower()
    assert "governor alpha" in text
    assert "power rank: 3" in text
    assert "acclaim 20,000 (rank 6)" in text
    assert "discord" not in text
    assert "account slot" not in text


def test_overview_fallback_uses_leadership_facing_inactive_shield_status() -> None:
    payload = _payload(page="overview")
    payload = replace(payload, header=replace(payload.header, shield_ends_at_utc=None))

    embed = build_fallback_embed(payload)
    location_field = next(field for field in embed.fields if field.name == "Location and shield")

    assert "Shield status: Inactive" in location_field.value
    assert "Shield ends:" not in location_field.value


def test_kvk_fallback_field_stays_within_discord_limit() -> None:
    rows = tuple(
        replace(
            _kvk(index),
            kill_points=10**80 + index,
            tanking_score=Decimal("1234567890.12345678901234567890"),
            dkp=10**80 + index,
        )
        for index in range(1, 21)
    )
    embed = build_fallback_embed(replace(_payload(page="kvk"), kvk_rows=rows))
    field = next(item for item in embed.fields if item.name == "Ended/finalized KVKs")

    assert len(field.value) <= 1024
    assert len(field.value.splitlines()) == 3


@pytest.mark.parametrize(
    ("row_count", "expected", "unexpected"),
    (
        (0, "NO ELIGIBLE FINALIZED KVK", "NO ADDITIONAL ELIGIBLE FINALIZED KVK"),
        (1, "NO ADDITIONAL ELIGIBLE FINALIZED KVK", "NO ELIGIBLE FINALIZED KVK"),
    ),
)
def test_kvk_empty_cards_distinguish_zero_from_fewer_than_three_rows(
    monkeypatch, row_count: int, expected: str, unexpected: str
) -> None:
    labels: list[str] = []

    def capture_text(_draw, _xy, value, **_kwargs):
        labels.append(value)

    monkeypatch.setattr(renderer, "_text", capture_text)
    image = Image.new("RGB", (renderer.WIDTH, renderer.HEIGHT))
    payload = replace(_payload(page="kvk"), kvk_rows=_payload().kvk_rows[:row_count])

    renderer._draw_kvk(ImageDraw.Draw(image), payload)

    assert expected in labels
    assert unexpected not in labels


@pytest.mark.asyncio
async def test_payload_identity_history_is_limited_to_selected_governor(monkeypatch) -> None:
    sample = _payload()
    captured: list[tuple[int, ...]] = []

    monkeypatch.setattr(
        service.dal,
        "fetch_review_contract",
        lambda *_args, **_kwargs: (
            sample.header,
            sample.presence,
            sample.coverage,
            sample.metrics,
            sample.activity_index,
            sample.history_depth,
        ),
    )
    monkeypatch.setattr(
        service.dal,
        "fetch_kvk_history",
        lambda *_args, **_kwargs: ((), (), service._kvk_index(())),
    )
    monkeypatch.setattr(
        service.dal,
        "fetch_last_active",
        lambda *_args, **_kwargs: sample.last_active,
    )
    monkeypatch.setattr(
        service,
        "_linked_governors",
        lambda *_args, **_kwargs: (
            LinkedGovernor(123, "Governor Alpha", current=True),
            LinkedGovernor(456, "Governor Beta"),
        ),
    )

    def identity(ids, **_kwargs):
        captured.append(tuple(ids))
        return sample.aliases, sample.alliance_episodes

    monkeypatch.setattr(service.dal, "fetch_identity_history", identity)
    service._payload_cache.clear()
    service._last_active_cache.clear()

    payload = await service.load_payload(123, 90, refresh=True)

    assert captured == [(123,)]
    assert {row.governor_id for row in payload.linked_governors} == {123, 456}


@pytest.mark.asyncio
async def test_payload_uses_sql_backed_kvk_index_rank(monkeypatch) -> None:
    sample = _payload()
    sql_index = KvkIndex(
        value=Decimal("181.20000000"),
        scored_kvks=2,
        candidate_kvks=3,
        per_kvk_scores=(),
        availability="PARTIAL",
        rank=5,
        cohort_count=308,
    )
    monkeypatch.setattr(
        service.dal,
        "fetch_review_contract",
        lambda *_args, **_kwargs: (
            sample.header,
            sample.presence,
            sample.coverage,
            sample.metrics,
            sample.activity_index,
            sample.history_depth,
        ),
    )
    monkeypatch.setattr(
        service.dal,
        "fetch_kvk_history",
        lambda *_args, **_kwargs: ((), (), sql_index),
    )
    monkeypatch.setattr(
        service.dal,
        "fetch_identity_history",
        lambda *_args, **_kwargs: (sample.aliases, sample.alliance_episodes),
    )
    monkeypatch.setattr(
        service.dal,
        "fetch_last_active",
        lambda *_args, **_kwargs: sample.last_active,
    )
    monkeypatch.setattr(service, "_linked_governors", lambda *_args, **_kwargs: ())
    service._payload_cache.clear()
    service._last_active_cache.clear()

    payload = await service.load_payload(123, 90, refresh=True)

    assert payload.kvk_index.value == Decimal("181.20000000")
    assert payload.kvk_index.rank == 5
    assert payload.kvk_index.cohort_count == 308


@pytest.mark.asyncio
async def test_payload_diagnostics_keep_kvk_resolution_separate_from_construction(
    monkeypatch,
) -> None:
    sample = _payload()

    async def immediate_to_thread(function, *args, **kwargs):
        return function(*args, **kwargs)

    monkeypatch.setattr(service.asyncio, "to_thread", immediate_to_thread)
    monkeypatch.setattr(
        service.dal,
        "fetch_review_contract",
        lambda *_args, **_kwargs: (
            sample.header,
            sample.presence,
            sample.coverage,
            sample.metrics,
            sample.activity_index,
            sample.history_depth,
        ),
    )
    monkeypatch.setattr(
        service.dal,
        "fetch_kvk_history",
        lambda *_args, **_kwargs: ((), (), service._kvk_index(())),
    )
    monkeypatch.setattr(
        service.dal,
        "fetch_identity_history",
        lambda *_args, **_kwargs: (sample.aliases, sample.alliance_episodes),
    )
    monkeypatch.setattr(
        service.dal,
        "fetch_last_active",
        lambda *_args, **_kwargs: sample.last_active,
    )
    monkeypatch.setattr(service, "_linked_governors", lambda *_args, **_kwargs: ())
    perf_values = iter((0.0, 1.0, 2.0, 3.0, 10.0, 12.0, 20.0, 23.0, 30.0))
    monkeypatch.setattr(service.time, "perf_counter", lambda: next(perf_values))
    monkeypatch.setattr(service.time, "monotonic", lambda: 0.0)
    service._payload_cache.clear()
    service._last_active_cache.clear()

    payload = await service.load_payload(123, 90, refresh=True)

    assert payload.diagnostics is not None
    stages = dict(payload.diagnostics.stage_ms)
    assert stages["kvk_resolution_ms"] == 2_000.0
    assert stages["payload_construction_ms"] == 3_000.0


@pytest.mark.asyncio
async def test_last_active_cache_is_reused_across_period_transitions(monkeypatch) -> None:
    sample = _payload()
    last_active_calls = 0

    monkeypatch.setattr(
        service.dal,
        "fetch_review_contract",
        lambda *_args, **_kwargs: (
            sample.header,
            sample.presence,
            sample.coverage,
            sample.metrics,
            sample.activity_index,
            sample.history_depth,
        ),
    )
    monkeypatch.setattr(
        service.dal,
        "fetch_kvk_history",
        lambda *_args, **_kwargs: ((), (), service._kvk_index(())),
    )
    monkeypatch.setattr(
        service.dal,
        "fetch_identity_history",
        lambda *_args, **_kwargs: (sample.aliases, sample.alliance_episodes),
    )
    monkeypatch.setattr(service, "_linked_governors", lambda *_args, **_kwargs: ())

    def fetch_last_active(*_args, **_kwargs):
        nonlocal last_active_calls
        last_active_calls += 1
        return sample.last_active

    monkeypatch.setattr(service.dal, "fetch_last_active", fetch_last_active)
    service._payload_cache.clear()
    service._last_active_cache.clear()

    first = await service.load_payload(123, 90)
    second = await service.load_payload(123, 30)

    assert last_active_calls == 1
    assert first.last_active == second.last_active
    assert first.diagnostics and first.diagnostics.cache_status == "MISS"
    assert second.diagnostics and second.diagnostics.cache_status == "MISS"


@pytest.mark.asyncio
async def test_last_active_cache_expiry_uses_monotonic_clock(monkeypatch) -> None:
    sample = _payload()
    cache_key = (sample.header.governor_id, NOW.date())
    service._last_active_cache.clear()
    service._last_active_cache[cache_key] = (50.0, sample.last_active)
    monkeypatch.setattr(service.time, "monotonic", lambda: 20.0)
    monkeypatch.setattr(service.time, "perf_counter", lambda: 1_000.0)

    def unexpected_fetch(*_args, **_kwargs):
        raise AssertionError("unexpired Last Active cache entry was not reused")

    monkeypatch.setattr(service.dal, "fetch_last_active", unexpected_fetch)
    diagnostics: dict[str, object] = {}

    result = await service._load_last_active(
        sample.header.governor_id,
        effective_now_utc=NOW,
        refresh=False,
        diagnostics=diagnostics,
    )

    assert result == sample.last_active
    assert diagnostics["cache_status"] == "HIT"


def test_dal_contract_is_bounded_static_and_audit_does_not_accept_sensitive_fields() -> None:
    source = Path(dal.__file__).read_text(encoding="utf-8")
    assert "usp_GetLeadershipPlayerReview" in source
    assert "usp_GetLeadershipPlayerLastActive" in source
    assert "usp_GetLeadershipPlayerLookupDirectory" in source
    assert "usp_GetLeadershipPlayerKvkHistory" in source
    assert "_QUERY_TIMEOUT_SECONDS = 12" in source
    audit_signature = source[source.index("def record_audit(") :]
    for forbidden in (
        "typed_lookup",
        "governor_name",
        "alliance",
        "location",
        "shield",
        "raw_error",
    ):
        assert forbidden not in audit_signature.lower()


@pytest.mark.asyncio
async def test_final_reauthorization_blocks_component_delivery(monkeypatch) -> None:
    import ui.views.leadership_player_review_views as views

    async def deny(_interaction):
        return LeadershipPlayerAuthorization(False, error_code="LEADERSHIP_ROLE_REQUIRED")

    async def no_audit(*_args, **_kwargs):
        return None

    denials: list[tuple[str, bool]] = []
    edits: list[dict] = []

    async def send_denial(message, *, ephemeral=False, **_kwargs):
        denials.append((message, ephemeral))

    async def edit_original_response(**kwargs):
        edits.append(kwargs)
        return SimpleNamespace()

    monkeypatch.setattr(views, "reauthorize_leadership_player_interaction", deny)
    monkeypatch.setattr(views, "_audit", no_audit)
    monkeypatch.setattr(views, "_card_file", lambda _payload: None)
    interaction = SimpleNamespace(
        user=SimpleNamespace(id=99),
        response=SimpleNamespace(is_done=lambda: True),
        followup=SimpleNamespace(send=send_denial),
        edit_original_response=edit_original_response,
    )
    view = LeadershipPlayerView(
        author_id=99,
        payload=_payload(),
        authorization=LeadershipPlayerAuthorization(True, basis="LEADERSHIP_ROLE_ID", role_id=10),
        correlation_id=uuid4(),
    )

    await view._replace(
        interaction,
        _payload(page="activity"),
        action="period_change",
        transition_id=0,
    )

    assert edits == []
    assert len(denials) == 1
    assert denials[0][1] is True


@pytest.mark.asyncio
async def test_component_begin_reauthorizes_before_payload_access(monkeypatch) -> None:
    import ui.views.leadership_player_review_views as views

    async def deny(_interaction):
        return LeadershipPlayerAuthorization(False, error_code="LEADERSHIP_ROLE_REQUIRED")

    async def no_audit(*_args, **_kwargs):
        return None

    denials: list[str] = []

    async def defer():
        return None

    async def send_denial(message, **_kwargs):
        denials.append(message)

    monkeypatch.setattr(views, "reauthorize_leadership_player_interaction", deny)
    monkeypatch.setattr(views, "_audit", no_audit)
    interaction = SimpleNamespace(
        user=SimpleNamespace(id=99),
        response=SimpleNamespace(is_done=lambda: True, defer=defer),
        followup=SimpleNamespace(send=send_denial),
    )
    view = LeadershipPlayerView(
        author_id=99,
        payload=_payload(),
        authorization=LeadershipPlayerAuthorization(True, basis="LEADERSHIP_ROLE_ID", role_id=10),
        correlation_id=uuid4(),
    )

    transition = await view._begin(
        interaction,
        action="period_change",
        target_id=123,
    )

    assert transition is None
    assert len(denials) == 1


@pytest.mark.asyncio
async def test_final_reauthorization_blocks_initial_attachment(monkeypatch) -> None:
    import ui.views.leadership_player_review_views as views

    allowed = LeadershipPlayerAuthorization(True, basis="LEADERSHIP_ROLE_ID", role_id=10)

    async def deny(_interaction):
        return LeadershipPlayerAuthorization(False, error_code="LEADERSHIP_ROLE_REQUIRED")

    async def no_audit(*_args, **_kwargs):
        return None

    async def no_defer(*_args, **_kwargs):
        return None

    load_calls = 0

    async def load_payload(*_args, **_kwargs):
        nonlocal load_calls
        load_calls += 1
        return _payload()

    sends: list[tuple[tuple, dict]] = []

    async def followup_send(*args, **kwargs):
        sends.append((args, kwargs))
        return SimpleNamespace()

    monkeypatch.setattr(views, "authorize_leadership_player_interaction", lambda _i: allowed)
    monkeypatch.setattr(views, "reauthorize_leadership_player_interaction", deny)
    monkeypatch.setattr(views, "_audit", no_audit)
    monkeypatch.setattr(views, "safe_defer", no_defer)
    monkeypatch.setattr(
        views.service, "governor_exists", lambda _governor_id: asyncio.sleep(0, True)
    )
    monkeypatch.setattr(views.service, "load_payload", load_payload)
    monkeypatch.setattr(views, "_card_file", lambda _payload: None)
    followup = SimpleNamespace(send=followup_send)
    interaction = SimpleNamespace(
        user=SimpleNamespace(id=99),
        response=SimpleNamespace(is_done=lambda: True),
        followup=followup,
    )
    ctx = SimpleNamespace(
        interaction=interaction,
        user=interaction.user,
        followup=followup,
    )

    await views.send_leadership_player_review(ctx, governor_id=123, name=None)

    assert len(sends) == 1
    args, kwargs = sends[0]
    assert "no longer permits" in args[0]
    assert kwargs == {"ephemeral": True}
    assert load_calls == 0


@pytest.mark.asyncio
async def test_unknown_exact_governor_id_fails_before_payload_load(monkeypatch) -> None:
    import ui.views.leadership_player_review_views as views

    allowed = LeadershipPlayerAuthorization(True, basis="LEADERSHIP_ROLE_ID", role_id=10)

    async def authorize(_interaction):
        return allowed

    async def no_audit(*_args, **_kwargs):
        return None

    async def no_defer(*_args, **_kwargs):
        return None

    async def does_not_exist(_governor_id):
        return False

    async def unexpected_load(*_args, **_kwargs):
        raise AssertionError("unknown exact ID must not start the full leadership payload")

    sends: list[tuple[tuple, dict]] = []

    async def followup_send(*args, **kwargs):
        sends.append((args, kwargs))
        return SimpleNamespace()

    monkeypatch.setattr(views, "authorize_leadership_player_interaction", lambda _i: allowed)
    monkeypatch.setattr(views, "reauthorize_leadership_player_interaction", authorize)
    monkeypatch.setattr(views, "_audit", no_audit)
    monkeypatch.setattr(views, "safe_defer", no_defer)
    monkeypatch.setattr(views.service, "governor_exists", does_not_exist)
    monkeypatch.setattr(views.service, "load_payload", unexpected_load)
    followup = SimpleNamespace(send=followup_send)
    interaction = SimpleNamespace(
        user=SimpleNamespace(id=99),
        response=SimpleNamespace(is_done=lambda: True),
        followup=followup,
    )
    ctx = SimpleNamespace(
        interaction=interaction,
        user=interaction.user,
        followup=followup,
    )

    await views.send_leadership_player_review(ctx, governor_id=999_999, name=None)

    assert sends == [
        (
            (
                "No governor with ID `999999` was found in the database. "
                "Please check the ID and try again.",
            ),
            {"ephemeral": True},
        )
    ]


@pytest.mark.asyncio
async def test_change_player_unknown_exact_id_keeps_current_dashboard(monkeypatch) -> None:
    import ui.views.leadership_player_review_views as views

    allowed = LeadershipPlayerAuthorization(True, basis="LEADERSHIP_ROLE_ID", role_id=10)

    async def reauthorize(_interaction):
        return allowed

    async def no_audit(*_args, **_kwargs):
        return None

    async def does_not_exist(_governor_id):
        return False

    async def unexpected_load(*_args, **_kwargs):
        raise AssertionError("unknown Change Player ID must not replace the current dashboard")

    sends: list[tuple[str, bool]] = []

    async def send_message(message, *, ephemeral=False, **_kwargs):
        sends.append((message, ephemeral))

    monkeypatch.setattr(views, "authorize_leadership_player_interaction", lambda _i: allowed)
    monkeypatch.setattr(views, "reauthorize_leadership_player_interaction", reauthorize)
    monkeypatch.setattr(views, "_audit", no_audit)
    monkeypatch.setattr(views.service, "governor_exists", does_not_exist)
    monkeypatch.setattr(views.service, "load_payload", unexpected_load)

    parent = LeadershipPlayerView(
        author_id=42,
        payload=_payload(),
        authorization=allowed,
        correlation_id=uuid4(),
    )
    modal = LeadershipChangePlayerModal(parent=parent)
    modal.query._input_value = "999999"
    interaction = SimpleNamespace(
        user=SimpleNamespace(id=42),
        response=SimpleNamespace(send_message=send_message),
    )

    await modal.callback(interaction)

    assert sends == [
        (
            "No governor with ID `999999` was found in the database. "
            "Please check the ID and try again.",
            True,
        )
    ]


def test_kvk_dal_maps_personal_best_from_second_result_set(monkeypatch) -> None:
    candidate = {
        "KVK_NO": 15,
        "KVK_NAME": "KVK 15",
        "FinalOutputState": "OUTPUT_COMPLETE",
    }
    performance = {
        "KVK_NO": 15,
        "GovernorID": 123,
        "GovernorName": "Governor Alpha",
        "PersonalCompletedKvkBestAcclaim": 25_000,
        "AcclaimRank": 6,
        "KillPointsRank": 4,
        "DeadsRank": 12,
        "HealedDataAvailable": 1,
        "FinalOutputState": "OUTPUT_COMPLETE",
    }
    index_summary = {
        "GovernorID": 123,
        "KvkIndexValue": Decimal("181.20000000"),
        "KvkIndexRank": 5,
        "KvkIndexCohortCount": 308,
        "ScoredKvkCount": 2,
        "CandidateKvkCount": 3,
        "Availability": "PARTIAL",
    }

    class _Cursor:
        def __init__(self) -> None:
            self._sets = [candidate, performance, index_summary]
            self._index = 0
            self.timeout = None

        @property
        def description(self):
            return [(key,) for key in self._sets[self._index]]

        def execute(self, *_args, **_kwargs) -> None:
            return None

        def fetchall(self):
            row = self._sets[self._index]
            return [tuple(row.values())]

        def nextset(self) -> bool:
            self._index += 1
            return self._index < len(self._sets)

    class _Connection:
        def __init__(self) -> None:
            self._cursor = _Cursor()

        def __enter__(self):
            return self

        def __exit__(self, *_args) -> None:
            return None

        def cursor(self):
            return self._cursor

    monkeypatch.setattr(dal, "get_conn_with_retries", _Connection)

    candidates, rows, kvk_index = dal.fetch_kvk_history(123)

    assert candidates[0].kvk_no == 15
    assert rows[0].personal_completed_kvk_best_acclaim == 25_000
    assert rows[0].acclaim_rank == 6
    assert rows[0].kill_points_rank == 4
    assert rows[0].deads_rank == 12
    assert rows[0].healed_data_available is True
    assert kvk_index == KvkIndex(
        value=Decimal("181.20000000"),
        scored_kvks=2,
        candidate_kvks=3,
        per_kvk_scores=(),
        availability="PARTIAL",
        rank=5,
        cohort_count=308,
    )


def test_review_dal_maps_latest_scan_power_rank(monkeypatch) -> None:
    header_row = {
        "GovernorID": 123,
        "GovernorName": "Governor Alpha",
        "CurrentPower": 123_456_789,
        "PowerRank": 3,
        "EffectiveNowUtc": NOW.replace(tzinfo=None),
        "PeriodDays": 90,
    }

    class _Cursor:
        timeout = None

        def execute(self, *_args, **_kwargs) -> None:
            return None

    class _Connection:
        def __enter__(self):
            return self

        def __exit__(self, *_args) -> None:
            return None

        def cursor(self):
            return _Cursor()

    monkeypatch.setattr(dal, "get_conn_with_retries", _Connection)
    monkeypatch.setattr(
        dal,
        "_result_sets",
        lambda _cursor, _count: ([header_row], [], [], [], [], []),
    )

    header, *_rest = dal.fetch_review_contract(123, 90, now_utc=NOW)

    assert header.current_power_rank == 3
