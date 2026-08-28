from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from io import BytesIO
from types import SimpleNamespace

import pytest

from player_self_service.preferences_renderer import RenderedPreferencesCard
from player_self_service.preferences_summary import (
    PreferencesSummaryPayload,
    PreferenceValueSummary,
    RegionalProfileSummary,
    TimeReferenceSummary,
)
from ui.views import player_self_service_views as views


def _payload() -> PreferencesSummaryPayload:
    value = PreferenceValueSummary(False, True, "Not set")
    return PreferencesSummaryPayload(
        discord_user_id=42,
        display_name="Tester",
        kingdom_id=1198,
        generated_at_utc=datetime(2026, 7, 15, 12, 0, tzinfo=UTC),
        regional_profile=RegionalProfileSummary(value, value, value),
        time_reference=TimeReferenceSummary(
            mode="UTC_FALLBACK",
            heading="UTC REFERENCE",
            display_time="12:00",
            timezone_label=None,
            utc_offset_label="UTC",
            supporting_line="Set a timezone to show your local-time reference.",
            regional_context=None,
        ),
        profile_details_set=0,
        profile_details_total=3,
        profile_supporting_text="0 of 3 profile details set",
        settings_insight="Set a timezone to add a local-time reference to Personal Settings.",
    )


@pytest.mark.asyncio
async def test_preferences_render_runs_off_loop_and_returns_standalone_attachment(
    monkeypatch,
) -> None:
    calls = []

    def render(payload, *, avatar_bytes=None):
        calls.append((payload, avatar_bytes))
        return RenderedPreferencesCard("me_preferences_42.png", b"png-bytes")

    async def to_thread(function, *args, **kwargs):
        calls.append(("to_thread", function))
        return function(*args, **kwargs)

    monkeypatch.setattr(views.preferences_renderer, "render_preferences_card", render)
    monkeypatch.setattr(views.asyncio, "to_thread", to_thread)

    embed, files = await views._build_page_response(
        views.PAGE_PREFERENCES,
        None,
        display_name="Tester",
        preferences_payload=_payload(),
        avatar_bytes=b"avatar",
    )
    try:
        assert embed is None
        assert [file.filename for file in files] == ["me_preferences_42.png"]
        assert calls[0][0] == "to_thread"
        assert calls[1] == (_payload(), b"avatar")
    finally:
        views._close_files(files)
    assert files[0].fp.closed is True


@pytest.mark.asyncio
async def test_preferences_render_failure_uses_same_payload_fallback(monkeypatch) -> None:
    payload = _payload()

    def fail(*_args, **_kwargs):
        raise RuntimeError("render failed")

    monkeypatch.setattr(views.preferences_renderer, "render_preferences_card", fail)

    embed, files = await views._build_page_response(
        views.PAGE_PREFERENCES,
        None,
        display_name="Tester",
        preferences_payload=payload,
    )

    assert files == []
    assert embed is not None
    assert embed.title == "Personal Settings"
    assert embed.footer.text == "Generated 15 Jul 2026, 12:00 UTC"


@pytest.mark.asyncio
async def test_preferences_file_creation_failure_closes_rendered_stream(monkeypatch) -> None:
    payload = _payload()
    stream = BytesIO(b"rendered preferences")

    monkeypatch.setattr(
        views.preferences_renderer,
        "render_preferences_card",
        lambda *_args, **_kwargs: SimpleNamespace(
            image_bytes=stream,
            filename="me_preferences_42.png",
        ),
    )
    monkeypatch.setattr(
        views.discord,
        "File",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("file rejected")),
    )

    embed, files = await views._build_page_response(
        views.PAGE_PREFERENCES,
        None,
        display_name="Tester",
        preferences_payload=payload,
    )

    assert embed is not None
    assert embed.title == "Personal Settings"
    assert files == []
    assert stream.closed is True


@pytest.mark.asyncio
async def test_preferences_send_failure_reuses_payload_without_refetch() -> None:
    payload = _payload()

    class Target:
        def __init__(self) -> None:
            self.calls = []

        async def edit_original_response(self, **kwargs):
            self.calls.append(kwargs)
            if len(self.calls) == 1:
                raise RuntimeError("attachment rejected")
            return SimpleNamespace(id=123)

    target = Target()
    stream = BytesIO(b"png")
    file = SimpleNamespace(
        fp=stream,
        filename="me_preferences_42.png",
        close=stream.close,
    )
    view = views.PlayerSelfServiceView(
        author_id=42,
        display_name="Tester",
        page=views.PAGE_PREFERENCES,
        preferences_payload=payload,
    )
    try:
        await views._edit_original_with_image_fallback(
            target,
            page=views.PAGE_PREFERENCES,
            summary=None,
            preferences_payload=payload,
            display_name="Tester",
            view=view,
            embed=None,
            files=[file],
        )
    finally:
        views._close_files([file])

    assert len(target.calls) == 2
    assert target.calls[1]["embed"].title == "Personal Settings"
    assert target.calls[1]["attachments"] == []


@pytest.mark.asyncio
async def test_preferences_loader_is_not_given_dashboard_governor_context(monkeypatch) -> None:
    calls = []

    async def loader(user_id: int, *, display_name: str):
        calls.append((user_id, display_name))
        return _payload()

    async def response(*_args, **_kwargs):
        return views.build_preferences_embed(_payload()), []

    monkeypatch.setattr(views, "_build_page_response", response)
    interaction = SimpleNamespace(
        user=SimpleNamespace(id=42),
        message=SimpleNamespace(id=123),
        response=SimpleNamespace(defer=lambda **_kwargs: _async_none()),
        followup=SimpleNamespace(send=lambda *args, **kwargs: _async_message()),
        edit_original_response=lambda **kwargs: _async_message(),
    )
    source = views.PlayerSelfServiceView(
        author_id=42,
        display_name="Tester",
        dashboard_governor_id=999999,
        preferences_loader=loader,
    )

    assert await source._show_page(interaction, views.PAGE_PREFERENCES) is True
    assert calls == [(42, "Tester")]


async def _async_none():
    return None


async def _async_message():
    return SimpleNamespace(id=456)


@pytest.mark.asyncio
async def test_preferences_timeout_preserves_last_attachment() -> None:
    payload = _payload()
    edits = []

    async def editor(**kwargs):
        edits.append(kwargs)

    view = views.PlayerSelfServiceView(
        author_id=42,
        display_name="Tester",
        page=views.PAGE_PREFERENCES,
        preferences_payload=payload,
    )
    view._timeout_editor = editor

    await view.on_timeout()

    assert all(item.disabled for item in view.children)
    assert set(edits[-1]) == {"content", "view"}
    assert "expired" in edits[-1]["content"]
    assert view.preferences_journey.expired is True


@pytest.mark.asyncio
async def test_concurrent_navigation_suppresses_superseded_preferences_result(
    monkeypatch,
) -> None:
    first_started = asyncio.Event()
    release_first = asyncio.Event()
    call_count = 0

    async def loader(_user_id: int, *, display_name: str):
        nonlocal call_count
        assert display_name == "Tester"
        call_count += 1
        if call_count == 1:
            first_started.set()
            await release_first.wait()
        return _payload()

    async def response(*_args, **_kwargs):
        return views.build_preferences_embed(_payload()), []

    monkeypatch.setattr(views, "_build_page_response", response)

    def interaction(edits: list[dict[str, object]]):
        async def edit(**kwargs):
            edits.append(kwargs)
            return SimpleNamespace(id=456)

        return SimpleNamespace(
            user=SimpleNamespace(id=42),
            message=SimpleNamespace(id=123),
            response=SimpleNamespace(defer=lambda **_kwargs: _async_none()),
            followup=SimpleNamespace(send=lambda *args, **kwargs: _async_message()),
            edit_original_response=edit,
        )

    source = views.PlayerSelfServiceView(
        author_id=42,
        display_name="Tester",
        preferences_loader=loader,
    )
    first_edits: list[dict[str, object]] = []
    second_edits: list[dict[str, object]] = []
    first = asyncio.create_task(source._show_page(interaction(first_edits), views.PAGE_PREFERENCES))
    await first_started.wait()
    second_result = await source._show_page(
        interaction(second_edits),
        views.PAGE_PREFERENCES,
    )
    release_first.set()
    first_result = await first

    assert second_result is True
    assert first_result is False
    assert len(second_edits) == 1
    assert first_edits == []
