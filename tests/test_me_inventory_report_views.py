from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from io import BytesIO
from types import SimpleNamespace

import discord
import pytest

from inventory.models import (
    InventoryExportFormat,
    InventoryReportPayload,
    InventoryReportRange,
    InventoryReportView,
    InventoryResourcePoint,
)
from player_self_service.governor_dashboard_models import (
    GovernorDashboardAccessDecision,
    GovernorDashboardContext,
    GovernorDashboardOption,
    GovernorDashboardResolution,
)
from ui.views import player_self_service_inventory_report_views as views


class _Response:
    def __init__(self) -> None:
        self.deferred = []
        self.sent = []
        self.edited = []
        self._done = False

    def is_done(self):
        return self._done

    async def defer(self, **kwargs):
        self.deferred.append(kwargs)
        self._done = True

    async def send_message(self, *args, **kwargs):
        self.sent.append((args, kwargs))
        self._done = True

    async def edit_message(self, **kwargs):
        self.edited.append(kwargs)
        self._done = True
        return SimpleNamespace(id=777)


@pytest.mark.asyncio
async def test_component_defer_omits_ephemeral_flag() -> None:
    interaction = _Interaction(component=True)

    await views._defer_private(interaction)

    assert interaction.response.deferred == [{}]


@pytest.mark.asyncio
async def test_private_error_propagates_cancellation() -> None:
    interaction = _Interaction(component=True)

    async def cancelled_send(*_args, **_kwargs):
        raise asyncio.CancelledError

    interaction.response.send_message = cancelled_send

    with pytest.raises(asyncio.CancelledError):
        await views._private_error(interaction, "cancelled")


class _Followup:
    def __init__(self) -> None:
        self.sent = []

    async def send(self, *args, **kwargs):
        message = SimpleNamespace(id=888)
        self.sent.append((args, kwargs, message))
        return message


class _Interaction:
    def __init__(self, user_id: int = 42, *, component: bool = True) -> None:
        self.user = SimpleNamespace(id=user_id, display_name="Tester", name="tester")
        self.response = _Response()
        self.followup = _Followup()
        self.message = SimpleNamespace(id=123) if component else None
        self.original_edits = []

    async def edit_original_response(self, **kwargs):
        self.original_edits.append(kwargs)
        return SimpleNamespace(id=456)


def _option(governor_id: int, *, default: bool = False) -> GovernorDashboardOption:
    return GovernorDashboardOption(
        governor_id=governor_id,
        governor_id_str=str(governor_id),
        governor_name=f"Gov {governor_id}",
        account_type="Main" if default else "Farm",
        is_default=default,
    )


def _context(option: GovernorDashboardOption) -> GovernorDashboardContext:
    return GovernorDashboardContext(
        viewer_discord_id=42,
        viewer_mode="self",
        selected_governor_id=option.governor_id,
        selected_governor_name=option.governor_name,
        is_linked_to_viewer=True,
        account_type_for_self_view=option.account_type,
        access_decision=GovernorDashboardAccessDecision(True, "linked"),
        privacy_profile="self_view",
    )


def _selected(
    option: GovernorDashboardOption,
    *,
    options: tuple[GovernorDashboardOption, ...] | None = None,
) -> GovernorDashboardResolution:
    return GovernorDashboardResolution(
        state="selected",
        options=options or (option,),
        context=_context(option),
        default_option=(options or (option,))[0],
    )


def _payload(
    *,
    governor_id: int = 111,
    view: InventoryReportView = InventoryReportView.RESOURCES,
    range_key: InventoryReportRange = InventoryReportRange.ONE_MONTH,
    with_data: bool = True,
) -> InventoryReportPayload:
    return InventoryReportPayload(
        governor_id=governor_id,
        governor_name=f"Gov {governor_id}",
        view=view,
        range_key=range_key,
        resources=(
            [
                InventoryResourcePoint(
                    scan_utc=datetime(2026, 7, 11, tzinfo=UTC),
                    food=1,
                    wood=2,
                    stone=3,
                    gold=4,
                )
            ]
            if with_data and view == InventoryReportView.RESOURCES
            else []
        ),
    )


def _ids(view: discord.ui.View) -> set[str]:
    return {str(child.custom_id) for child in view.children if child.custom_id}


@pytest.mark.asyncio
async def test_render_files_accepts_existing_renderer_bytesio_contract() -> None:
    files = await views._render_files(_payload())

    assert [file.filename for file in files] == ["inventory_resources_111_1M.png"]
    assert files[0].fp.closed is False
    views._close_files(files)
    assert files[0].fp.closed is True


@pytest.mark.asyncio
async def test_multiple_governors_show_dropdown_only_before_payload_fetch() -> None:
    options = (_option(111, default=True), _option(222))
    interaction = _Interaction(component=False)

    async def resolver(*_args, **_kwargs):
        return GovernorDashboardResolution(
            state="requires_selection",
            options=options,
            default_option=options[0],
        )

    async def payload_loader(**_kwargs):
        raise AssertionError("payload must not load before governor selection")

    await views.show_player_inventory_report_for_interaction(
        interaction,
        author_id=42,
        display_name="Tester",
        report_view=InventoryReportView.RESOURCES,
        context_resolver=resolver,
        payload_loader=payload_loader,
    )

    edit = interaction.original_edits[-1]
    assert edit["embed"].title == "Choose a Governor"
    assert len(edit["view"].children) == 1
    assert isinstance(edit["view"].children[0], discord.ui.Select)


@pytest.mark.asyncio
async def test_no_governors_show_private_setup_without_payload_fetch() -> None:
    interaction = _Interaction(component=False)

    async def resolver(*_args, **_kwargs):
        return GovernorDashboardResolution(state="requires_setup", options=())

    async def payload_loader(**_kwargs):
        raise AssertionError("setup state must not fetch payload")

    await views.show_player_inventory_report_for_interaction(
        interaction,
        author_id=42,
        display_name="Tester",
        report_view=InventoryReportView.MATERIALS,
        context_resolver=resolver,
        payload_loader=payload_loader,
    )

    edit = interaction.original_edits[-1]
    assert edit["embed"].title == "Set up Inventory"
    assert "/me accounts" in edit["embed"].description
    assert edit["attachments"] == []


@pytest.mark.asyncio
async def test_selected_report_is_private_standalone_and_has_approved_rows(monkeypatch) -> None:
    option = _option(111, default=True)
    interaction = _Interaction(component=False)

    async def resolver(*_args, **_kwargs):
        return _selected(option)

    async def payload_loader(**kwargs):
        assert kwargs == {
            "discord_user_id": 42,
            "governor_id": 111,
            "view": InventoryReportView.RESOURCES,
            "range_key": InventoryReportRange.ONE_MONTH,
        }
        return _payload()

    monkeypatch.setattr(
        views,
        "render_inventory_reports",
        lambda payload, *, avatar_bytes=None: [
            SimpleNamespace(
                filename="inventory_resources_111_1m.png",
                image_bytes=BytesIO(b"png"),
            )
        ],
    )

    await views.show_player_inventory_report_for_interaction(
        interaction,
        author_id=42,
        display_name="Tester",
        report_view=InventoryReportView.RESOURCES,
        context_resolver=resolver,
        payload_loader=payload_loader,
    )

    edit = interaction.original_edits[-1]
    assert interaction.response.deferred == [{"ephemeral": True}]
    assert edit["embed"] is None
    assert edit["attachments"] == []
    assert edit["files"][0].filename == "inventory_resources_111_1m.png"
    assert edit["files"][0].fp.closed is True
    report_view = edit["view"]
    assert [(child.label, child.row) for child in report_view.children] == [
        ("Resources", 0),
        ("Speedups", 0),
        ("Materials", 0),
        ("1M", 1),
        ("3M", 1),
        ("6M", 1),
        ("12M", 1),
        ("Export Excel", 2),
        ("Export CSV", 2),
        ("Export Sheets", 2),
        ("Dashboard", 3),
    ]


@pytest.mark.asyncio
async def test_no_data_renders_private_standalone_empty_state_from_same_payload(
    monkeypatch,
) -> None:
    option = _option(111, default=True)
    interaction = _Interaction(component=False)
    calls = 0

    async def resolver(*_args, **_kwargs):
        return _selected(option)

    async def payload_loader(**_kwargs):
        nonlocal calls
        calls += 1
        return _payload(with_data=False)

    rendered_payloads = []

    def render(payload, *, avatar_bytes=None):
        rendered_payloads.append((payload, avatar_bytes))
        return [
            SimpleNamespace(
                filename="inventory_resources_111_1M.png",
                image_bytes=BytesIO(b"empty-state-png"),
            )
        ]

    monkeypatch.setattr(views, "render_inventory_reports", render)

    await views.show_player_inventory_report_for_interaction(
        interaction,
        author_id=42,
        display_name="Tester",
        report_view=InventoryReportView.RESOURCES,
        context_resolver=resolver,
        payload_loader=payload_loader,
    )

    edit = interaction.original_edits[-1]
    assert calls == 1
    assert rendered_payloads[0][0].resources == []
    assert rendered_payloads[0][1] is None
    assert "/inventory import" in edit["content"]
    assert edit["embed"] is None
    assert edit["files"][0].filename == "inventory_resources_111_1M.png"
    assert edit["files"][0].fp.closed is True


@pytest.mark.asyncio
async def test_component_no_data_replaces_dashboard_instead_of_sending_followup(
    monkeypatch,
) -> None:
    option = _option(111, default=True)
    interaction = _Interaction(component=True)

    class EditableMessage:
        def __init__(self) -> None:
            self.edits = []

        async def edit(self, **kwargs):
            self.edits.append(kwargs)
            return self

    message = EditableMessage()
    interaction.message = message

    async def failed_original_edit(**_kwargs):
        raise RuntimeError("component original response unavailable")

    async def resolver(*_args, **_kwargs):
        return _selected(option)

    async def payload_loader(**_kwargs):
        return _payload(with_data=False)

    interaction.edit_original_response = failed_original_edit
    monkeypatch.setattr(
        views,
        "render_inventory_reports",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("no-data must not render")),
    )

    await views.show_player_inventory_report_for_interaction(
        interaction,
        author_id=42,
        display_name="Tester",
        report_view=InventoryReportView.RESOURCES,
        context_resolver=resolver,
        payload_loader=payload_loader,
    )

    assert len(message.edits) == 1
    assert message.edits[0]["attachments"] == []
    assert message.edits[0]["embed"].fields[0].name == "Upload Inventory"
    assert interaction.followup.sent == []


@pytest.mark.asyncio
async def test_component_no_data_replaces_attached_dashboard_with_empty_state_png(
    monkeypatch,
) -> None:
    option = _option(111, default=True)
    interaction = _Interaction(component=True)

    class AttachedMessage:
        def __init__(self) -> None:
            self.attachments = [SimpleNamespace(id=999)]

        async def delete(self):
            raise AssertionError("the attached dashboard must not be deleted")

    message = AttachedMessage()
    interaction.message = message

    async def resolver(*_args, **_kwargs):
        return _selected(option)

    async def payload_loader(**_kwargs):
        return _payload(with_data=False)

    monkeypatch.setattr(
        views,
        "render_inventory_reports",
        lambda *_args, **_kwargs: [
            SimpleNamespace(
                filename="inventory_resources_111_1M.png",
                image_bytes=BytesIO(b"empty-state-png"),
            )
        ],
    )

    await views.show_player_inventory_report_for_interaction(
        interaction,
        author_id=42,
        display_name="Tester",
        report_view=InventoryReportView.RESOURCES,
        context_resolver=resolver,
        payload_loader=payload_loader,
    )

    assert len(interaction.original_edits) == 1
    edit = interaction.original_edits[0]
    assert edit["embed"] is None
    assert edit["attachments"] == []
    assert edit["files"][0].filename == "inventory_resources_111_1M.png"
    assert interaction.followup.sent == []


@pytest.mark.asyncio
async def test_range_change_rechecks_access_before_payload_and_preserves_type(monkeypatch) -> None:
    option = _option(111, default=True)
    initial = _selected(option)
    calls = []

    async def resolver(user_id, governor_id, **kwargs):
        calls.append(("access", user_id, governor_id, kwargs))
        return initial

    async def payload_loader(**kwargs):
        calls.append(("payload", kwargs))
        return _payload(range_key=kwargs["range_key"])

    monkeypatch.setattr(
        views,
        "render_inventory_reports",
        lambda payload, *, avatar_bytes=None: [
            SimpleNamespace(filename="report.png", image_bytes=BytesIO(b"png"))
        ],
    )
    view = views.PlayerInventoryReportView(
        author_id=42,
        display_name="Tester",
        resolution=initial,
        report_view=InventoryReportView.RESOURCES,
        context_resolver=resolver,
        payload_loader=payload_loader,
    )
    interaction = _Interaction()

    await view.change_report(interaction, range_key=InventoryReportRange.THREE_MONTHS)

    assert calls[0] == ("access", 42, 111, {"viewer_mode": "self"})
    assert calls[1][1]["view"] == InventoryReportView.RESOURCES
    assert calls[1][1]["range_key"] == InventoryReportRange.THREE_MONTHS


@pytest.mark.asyncio
async def test_change_governor_preserves_report_type_and_range(monkeypatch) -> None:
    main = _option(111, default=True)
    alt = _option(222)
    options = (main, alt)
    initial = _selected(main, options=options)
    replacement = _selected(alt, options=options)
    calls = []

    async def resolver(_user_id, governor_id, **_kwargs):
        assert governor_id == "222"
        return replacement

    async def payload_loader(**kwargs):
        calls.append(kwargs)
        return _payload(
            governor_id=222,
            view=kwargs["view"],
            range_key=kwargs["range_key"],
        )

    monkeypatch.setattr(
        views,
        "render_inventory_reports",
        lambda payload, *, avatar_bytes=None: [
            SimpleNamespace(filename="report.png", image_bytes=BytesIO(b"png"))
        ],
    )
    view = views.PlayerInventoryReportView(
        author_id=42,
        display_name="Tester",
        resolution=initial,
        report_view=InventoryReportView.MATERIALS,
        range_key=InventoryReportRange.SIX_MONTHS,
        context_resolver=resolver,
        payload_loader=payload_loader,
    )
    interaction = _Interaction()

    await view.select_governor(interaction, "222")

    assert calls[0]["governor_id"] == 222
    assert calls[0]["view"] == InventoryReportView.MATERIALS
    assert calls[0]["range_key"] == InventoryReportRange.SIX_MONTHS


@pytest.mark.asyncio
async def test_denied_recheck_does_not_fetch_payload() -> None:
    option = _option(111, default=True)
    initial = _selected(option)

    async def resolver(*_args, **_kwargs):
        return GovernorDashboardResolution(state="denied", options=(option,), reason="removed")

    async def payload_loader(**_kwargs):
        raise AssertionError("denied action must not fetch payload")

    view = views.PlayerInventoryReportView(
        author_id=42,
        display_name="Tester",
        resolution=initial,
        report_view=InventoryReportView.RESOURCES,
        context_resolver=resolver,
        payload_loader=payload_loader,
    )
    interaction = _Interaction()

    await view.change_report(interaction, range_key=InventoryReportRange.THREE_MONTHS)

    assert interaction.original_edits[-1]["embed"].title == "Inventory access denied"


@pytest.mark.asyncio
async def test_render_failure_uses_same_payload_fallback(monkeypatch) -> None:
    option = _option(111, default=True)
    interaction = _Interaction(component=False)
    calls = 0

    async def resolver(*_args, **_kwargs):
        return _selected(option)

    async def payload_loader(**_kwargs):
        nonlocal calls
        calls += 1
        return _payload()

    monkeypatch.setattr(
        views,
        "render_inventory_reports",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("render failed")),
    )

    await views.show_player_inventory_report_for_interaction(
        interaction,
        author_id=42,
        display_name="Tester",
        report_view=InventoryReportView.RESOURCES,
        context_resolver=resolver,
        payload_loader=payload_loader,
    )

    assert calls == 1
    assert interaction.original_edits[-1]["embed"].title == "Resources Inventory"


@pytest.mark.asyncio
async def test_image_delivery_failure_retries_same_payload_fallback_and_closes_stream(
    monkeypatch,
) -> None:
    option = _option(111, default=True)
    interaction = _Interaction(component=False)
    calls = 0
    edits = []

    async def resolver(*_args, **_kwargs):
        return _selected(option)

    async def payload_loader(**_kwargs):
        nonlocal calls
        calls += 1
        return _payload()

    monkeypatch.setattr(
        views,
        "render_inventory_reports",
        lambda payload, *, avatar_bytes=None: [
            SimpleNamespace(filename="report.png", image_bytes=BytesIO(b"png"))
        ],
    )

    async def flaky_edit(**kwargs):
        edits.append(kwargs)
        if kwargs.get("files"):
            raise RuntimeError("attachment rejected")
        return SimpleNamespace(id=456)

    interaction.edit_original_response = flaky_edit
    await views.show_player_inventory_report_for_interaction(
        interaction,
        author_id=42,
        display_name="Tester",
        report_view=InventoryReportView.RESOURCES,
        context_resolver=resolver,
        payload_loader=payload_loader,
    )

    assert calls == 1
    assert len(edits) == 2
    assert edits[0]["files"][0].fp.closed is True
    assert edits[1]["embed"].title == "Resources Inventory"
    assert edits[1]["attachments"] == []


@pytest.mark.asyncio
async def test_image_delivery_timeout_is_terminal_and_closes_stream() -> None:
    option = _option(111, default=True)
    interaction = _Interaction(component=True)
    view = views.PlayerInventoryReportView(
        author_id=42,
        display_name="Tester",
        resolution=_selected(option),
        report_view=InventoryReportView.RESOURCES,
    )
    edits = []
    report_file = discord.File(BytesIO(b"png"), filename="report.png")

    async def timed_out_edit(**kwargs):
        edits.append(kwargs)
        raise TimeoutError

    interaction.edit_original_response = timed_out_edit

    rendered = await views._edit_report_response(
        interaction,
        content=None,
        embed=None,
        fallback_embed=discord.Embed(title="Fallback"),
        view=view,
        files=[report_file],
        timeout_remaining=lambda: 1.0,
    )

    assert rendered is False
    assert len(edits) == 1
    assert interaction.followup.sent == []
    assert report_file.fp.closed is True


@pytest.mark.asyncio
async def test_fallback_delivery_timeout_does_not_attempt_followup() -> None:
    option = _option(111, default=True)
    interaction = _Interaction(component=True)
    view = views.PlayerInventoryReportView(
        author_id=42,
        display_name="Tester",
        resolution=_selected(option),
        report_view=InventoryReportView.RESOURCES,
    )
    edits = []

    async def failing_edits(**kwargs):
        edits.append(kwargs)
        if len(edits) == 1:
            raise RuntimeError("attachment rejected")
        raise TimeoutError

    interaction.edit_original_response = failing_edits

    rendered = await views._edit_report_response(
        interaction,
        content=None,
        embed=None,
        fallback_embed=discord.Embed(title="Fallback"),
        view=view,
        timeout_remaining=lambda: 1.0,
    )

    assert rendered is False
    assert len(edits) == 2
    assert interaction.followup.sent == []


@pytest.mark.asyncio
async def test_selected_paging_preserves_attachment_and_keeps_change_governor_last() -> None:
    options = tuple(_option(100 + index, default=index == 0) for index in range(26))
    resolution = _selected(options[25], options=options)
    view = views.PlayerInventoryReportView(
        author_id=42,
        display_name="Tester",
        resolution=resolution,
        report_view=InventoryReportView.RESOURCES,
    )
    assert view.selector_page == 1
    change = next(child for child in view.children if isinstance(child, discord.ui.Select))
    assert change.row == 4
    assert {child.label for child in view.children if child.row == 3} == {
        "Dashboard",
        "Previous",
        "Next",
    }

    interaction = _Interaction()
    await view.page_governors(interaction, -1)

    assert set(interaction.response.edited[-1]) == {"view"}


@pytest.mark.asyncio
async def test_foreign_timeout_and_concurrent_actions_fail_privately() -> None:
    option = _option(111, default=True)
    view = views.PlayerInventoryReportView(
        author_id=42,
        display_name="Tester",
        resolution=_selected(option),
        report_view=InventoryReportView.RESOURCES,
    )
    foreign = _Interaction(99)
    assert await view.interaction_check(foreign) is False
    assert foreign.response.sent[-1][1]["ephemeral"] is True

    first = _Interaction()
    second = _Interaction()
    assert await view._claim(first) is True
    assert await view._claim(second) is False
    assert "already" in second.response.sent[-1][0][0]
    view._release(first)

    timeout_target = _Interaction()
    view.set_timeout_target(timeout_target)
    await view.on_timeout()
    assert timeout_target.original_edits[-1]["attachments"] == []
    assert all(child.disabled for child in view.children)


@pytest.mark.asyncio
async def test_failed_component_defer_does_not_leave_report_busy(monkeypatch) -> None:
    option = _option(111, default=True)

    async def resolver(*_args, **_kwargs):
        return _selected(option)

    async def render_resolution(*_args, **_kwargs):
        return True

    view = views.PlayerInventoryReportView(
        author_id=42,
        display_name="Tester",
        resolution=_selected(option),
        report_view=InventoryReportView.RESOURCES,
        context_resolver=resolver,
    )
    interaction = _Interaction()

    async def rejected_defer(**_kwargs):
        raise discord.HTTPException(SimpleNamespace(status=404, reason="expired"), "expired")

    interaction.response.defer = rejected_defer
    monkeypatch.setattr(views, "_render_resolution", render_resolution)

    await view.change_report(interaction, range_key=InventoryReportRange.THREE_MONTHS)

    assert view._busy is False
    assert view._active_transition_id is None


@pytest.mark.asyncio
async def test_cancelled_component_defer_releases_report_claim() -> None:
    option = _option(111, default=True)
    view = views.PlayerInventoryReportView(
        author_id=42,
        display_name="Tester",
        resolution=_selected(option),
        report_view=InventoryReportView.RESOURCES,
    )
    interaction = _Interaction()

    async def cancelled_defer(**_kwargs):
        raise asyncio.CancelledError

    interaction.response.defer = cancelled_defer

    with pytest.raises(asyncio.CancelledError):
        await view.change_report(interaction, range_key=InventoryReportRange.THREE_MONTHS)

    assert view._busy is False
    assert view._active_transition_id is None


@pytest.mark.asyncio
async def test_export_is_strict_private_and_cleans_temp_file(monkeypatch) -> None:
    option = _option(111, default=True)
    resolution = _selected(option)
    captured = {}
    cleaned = []
    fake_export = SimpleNamespace(
        path="C:/tmp/report.xlsx",
        filename="report.xlsx",
        row_count=3,
        governor_ids=(111,),
    )

    async def resolver(*_args, **_kwargs):
        return resolution

    async def build_export(**kwargs):
        captured.update(kwargs)
        return fake_export

    class FakeFile:
        def __init__(self, path, *, filename):
            self.path = path
            self.filename = filename
            self.closed = False

        def close(self):
            self.closed = True

    monkeypatch.setattr(views.export_service, "build_inventory_export_file", build_export)
    monkeypatch.setattr(views.export_service, "cleanup_export_file", cleaned.append)
    monkeypatch.setattr(views.discord, "File", FakeFile)
    view = views.PlayerInventoryReportView(
        author_id=42,
        display_name="Tester",
        resolution=resolution,
        report_view=InventoryReportView.RESOURCES,
        context_resolver=resolver,
    )
    interaction = _Interaction()

    await view.export_report(interaction, InventoryExportFormat.EXCEL)

    assert captured["governor_id"] == 111
    assert captured["is_admin"] is False
    assert captured["discord_user"] is None
    assert interaction.followup.sent[-1][1]["ephemeral"] is True
    assert interaction.followup.sent[-1][1]["file"].closed is True
    assert cleaned == [fake_export]
