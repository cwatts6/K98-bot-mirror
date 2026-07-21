from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from PIL import Image
import pytest

from core.leadership_player_permissions import LeadershipPlayerAuthorization
from leadership_player_review import dal, renderer, service
from leadership_player_review.models import (
    ActivityIndex,
    ActivityMetric,
    AliasRecord,
    AllianceEpisode,
    HistoryDepth,
    KvkPerformance,
    LeadershipPlayerPayload,
    LinkedGovernor,
    LookupCandidate,
    ReviewHeader,
    ScanPresence,
    SourceCoverage,
)
from ui.views.leadership_player_review_views import (
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
    )


def _payload(*, page="overview", aliases=1, episodes=1, linked=2) -> LeadershipPlayerPayload:
    header = ReviewHeader(
        governor_id=123,
        governor_name="Governor Alpha",
        current_alliance="K98",
        current_power=123_456_789,
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
        prompts=("Strength: visible rank evidence.", "Review: visible trend evidence?"),
        warnings=(),
        generated_at_utc=NOW,
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

    averages = [text for text in rendered_text if text.startswith("AVG ")]
    assert len(averages) == 6
    assert all(text.endswith("/day") for text in averages)


@pytest.mark.parametrize("page", ["overview", "activity"])
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


@pytest.mark.parametrize("page", ["overview", "activity"])
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
    assert controls["leadership:player:change"].row == 2
    assert controls["leadership:player:linked"].row == 3
    assert controls["leadership:player:record:previous"].disabled is True
    assert controls["leadership:player:record:next"].disabled is False
    assert controls["leadership:player:current"].disabled is True
    assert controls["leadership:player:current"].style.name == "primary"
    assert callable(view.refresh)
    assert controls["leadership:player:refresh"].callback is not None
    linked_values = {option.value for option in controls["leadership:player:linked"].options}
    assert "g:123" not in linked_values
    assert all(
        "discord" not in option.description.lower()
        for option in controls["leadership:player:linked"].options
    )


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
    assert "discord" not in text
    assert "account slot" not in text


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
    assert field.value.endswith("...")


@pytest.mark.asyncio
async def test_payload_identity_history_covers_all_active_linked_governors(monkeypatch) -> None:
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
        lambda *_args, **_kwargs: ((), ()),
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

    payload = await service.load_payload(123, 90, refresh=True)

    assert captured == [(123, 456)]
    assert {row.governor_id for row in payload.linked_governors} == {123, 456}


def test_dal_contract_is_bounded_static_and_audit_does_not_accept_sensitive_fields() -> None:
    source = Path(dal.__file__).read_text(encoding="utf-8")
    assert "usp_GetLeadershipPlayerReview" in source
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
async def test_final_reauthorization_blocks_initial_attachment(monkeypatch) -> None:
    import ui.views.leadership_player_review_views as views

    allowed = LeadershipPlayerAuthorization(True, basis="LEADERSHIP_ROLE_ID", role_id=10)

    async def deny(_interaction):
        return LeadershipPlayerAuthorization(False, error_code="LEADERSHIP_ROLE_REQUIRED")

    async def no_audit(*_args, **_kwargs):
        return None

    async def no_defer(*_args, **_kwargs):
        return None

    async def load_payload(*_args, **_kwargs):
        return _payload()

    sends: list[tuple[tuple, dict]] = []

    async def followup_send(*args, **kwargs):
        sends.append((args, kwargs))
        return SimpleNamespace()

    monkeypatch.setattr(views, "authorize_leadership_player_interaction", lambda _i: allowed)
    monkeypatch.setattr(views, "reauthorize_leadership_player_interaction", deny)
    monkeypatch.setattr(views, "_audit", no_audit)
    monkeypatch.setattr(views, "safe_defer", no_defer)
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
        "FinalOutputState": "OUTPUT_COMPLETE",
    }

    class _Cursor:
        def __init__(self) -> None:
            self._sets = [candidate, performance]
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

    candidates, rows = dal.fetch_kvk_history(123)

    assert candidates[0].kvk_no == 15
    assert rows[0].personal_completed_kvk_best_acclaim == 25_000
