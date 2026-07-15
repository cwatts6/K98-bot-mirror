from __future__ import annotations

from datetime import UTC, datetime
from io import BytesIO
from types import SimpleNamespace

import discord
import pytest

from player_self_service.accounts_models import (
    AccountMetricTotal,
    AccountPortfolioRow,
    AccountsPortfolioPayload,
)
from ui.views import player_self_service_account_summary_views as summary_views


def _payload(count: int = 9) -> AccountsPortfolioPayload:
    now = datetime(2026, 7, 14, 8, 30, tzinfo=UTC)
    rows = tuple(
        AccountPortfolioRow(
            slot="Main" if index == 0 else f"Farm {index}",
            role="Main" if index == 0 else "Farm",
            registered_name=f"Gov {index}",
            governor_id=1000 + index,
            power=100,
            troop_power=50,
            kill_points=200,
            t4_kills=10,
            t5_kills=20,
            t4_t5_kills=30,
            deads=10,
            healed_troops=5,
            helps=7,
            rss_gathered=300,
            rss_assistance=200,
            rss_total=400,
            conduct=98.5,
            data_state="CURRENT",
            last_governor_scan=now,
            inventory_as_of=now,
        )
        for index in range(count)
    )
    metric = AccountMetricTotal(100 * count, count, count)
    return AccountsPortfolioPayload(
        discord_user_id=42,
        state="READY",
        rows=rows,
        linked_count=count,
        main_row=rows[0] if rows else None,
        role_counts=(("Main", 1), ("Alt", 0), ("Farm", max(0, count - 1))),
        power=metric,
        troop_power=metric,
        t4_t5_kills=metric,
        rss_total=metric,
        insight="All current.",
        refreshed_at_utc=now,
    )


class _Response:
    def __init__(self) -> None:
        self.sent = []
        self.deferred = []
        self._done = False

    def is_done(self):
        return self._done

    async def defer(self, **kwargs):
        self.deferred.append(kwargs)
        self._done = True

    async def send_message(self, *args, **kwargs):
        self.sent.append((args, kwargs))
        self._done = True


class _Followup:
    def __init__(self) -> None:
        self.sent = []

    async def send(self, *args, **kwargs):
        self.sent.append((args, kwargs))
        return SimpleNamespace()


class _Interaction:
    def __init__(self, user_id: int = 42) -> None:
        self.user = SimpleNamespace(id=user_id)
        self.response = _Response()
        self.followup = _Followup()
        self.original_edits = []

    async def edit_original_response(self, **kwargs):
        self.original_edits.append(kwargs)
        return SimpleNamespace()


def _layout(view) -> list[tuple[str, int, bool]]:
    return [
        (
            str(getattr(child, "label", "")),
            int(getattr(child, "row", 0) or 0),
            bool(getattr(child, "disabled", False)),
        )
        for child in view.children
    ]


def test_overview_fallback_includes_vip_and_last_scan_datetime() -> None:
    page = summary_views.accounts_service.build_account_summary_page(
        _payload(), section="overview", page=1
    )

    embed = summary_views.build_account_summary_fallback(page)

    assert "VIP" in embed.fields[0].value
    assert "Last scan 14 Jul 2026 08:30 UTC" in embed.fields[0].value


def test_combat_fallback_uses_short_title_percentage_and_helpful_footer() -> None:
    page = summary_views.accounts_service.build_account_summary_page(
        _payload(), section="combat", page=1
    )

    embed = summary_views.build_account_summary_fallback(page)

    assert embed.title == "Account Summary • Combat"
    assert "Tanking 181.8%" in embed.fields[0].value
    assert "Conduct" not in embed.fields[0].value
    assert embed.footer.text.startswith("Combat all linked governors (Tanking: Higher = Better)")


def test_economy_fallback_includes_conduct() -> None:
    page = summary_views.accounts_service.build_account_summary_page(
        _payload(), section="economy", page=1
    )

    embed = summary_views.build_account_summary_fallback(page)

    assert "Conduct 99" in embed.fields[0].value


@pytest.mark.asyncio
async def test_account_summary_controls_match_locked_rows_and_boundaries() -> None:
    view = summary_views.AccountSummaryView(
        author_id=42,
        display_name="Tester",
        payload=_payload(),
    )

    assert _layout(view) == [
        ("Accounts", 0, True),
        ("Reminders", 0, False),
        ("Preferences", 0, False),
        ("Dashboard", 1, False),
        ("Exports", 1, False),
        ("Overview", 2, True),
        ("Combat", 2, False),
        ("Economy", 2, False),
        ("Previous", 3, True),
        ("Next", 3, False),
        ("Download CSV", 3, False),
        ("Back to Accounts", 3, False),
    ]


@pytest.mark.asyncio
async def test_account_summary_disables_csv_for_empty_payload() -> None:
    view = summary_views.AccountSummaryView(
        author_id=42,
        display_name="Tester",
        payload=_payload(0),
    )

    csv_button = next(child for child in view.children if child.label == "Download CSV")
    assert csv_button.disabled is True


@pytest.mark.asyncio
async def test_account_summary_timeout_disables_controls_and_preserves_report() -> None:
    interaction = _Interaction()
    view = summary_views.AccountSummaryView(
        author_id=42,
        display_name="Tester",
        payload=_payload(),
    )
    view.set_timeout_target(interaction)

    await view.on_timeout()

    assert all(child.disabled for child in view.children)
    assert "expired" in interaction.original_edits[-1]["content"]
    assert "attachments" not in interaction.original_edits[-1]
    assert "files" not in interaction.original_edits[-1]

    click = _Interaction()
    assert await view.interaction_check(click) is False
    assert click.response.sent[-1][1]["ephemeral"] is True


@pytest.mark.asyncio
async def test_section_change_resets_page_without_refetch(monkeypatch) -> None:
    calls = []

    async def loader(_user_id):
        calls.append("load")
        return _payload()

    async def render(_page, _display_name, avatar_bytes):
        assert avatar_bytes is None
        return discord.File(BytesIO(b"png"), filename="me_account_summary_42.png")

    monkeypatch.setattr(summary_views, "_render_summary", render)
    view = summary_views.AccountSummaryView(
        author_id=42,
        display_name="Tester",
        payload=_payload(17),
        section="overview",
        page=2,
        accounts_loader=loader,
    )
    interaction = _Interaction()
    button = next(child for child in view.children if child.label == "Combat")

    await button.callback(interaction)

    assert calls == []
    edited_view = interaction.original_edits[-1]["view"]
    assert edited_view.summary_page.section == "combat"
    assert edited_view.summary_page.page == 1
    assert interaction.original_edits[-1]["attachments"] == []


@pytest.mark.asyncio
async def test_account_summary_entry_refetches_once_and_delivery_is_standalone(monkeypatch) -> None:
    calls = []

    async def loader(user_id):
        calls.append(user_id)
        return _payload()

    async def render(_page, _display_name, avatar_bytes):
        assert avatar_bytes == b"avatar"
        return discord.File(BytesIO(b"png"), filename="me_account_summary_42.png")

    monkeypatch.setattr(summary_views, "_render_summary", render)
    interaction = _Interaction()

    await summary_views.show_account_summary_for_interaction(
        interaction,
        author_id=42,
        display_name="Tester",
        accounts_loader=loader,
        avatar_bytes=b"avatar",
    )

    assert calls == [42]
    assert interaction.original_edits[-1]["embed"] is None
    assert interaction.original_edits[-1]["attachments"] == []
    assert [file.filename for file in interaction.original_edits[-1]["files"]] == [
        "me_account_summary_42.png"
    ]


@pytest.mark.asyncio
async def test_render_failure_uses_same_payload_without_second_fetch(monkeypatch) -> None:
    calls = []

    async def loader(user_id):
        calls.append(user_id)
        return _payload()

    async def failing_render(_page, _display_name, _avatar_bytes):
        raise RuntimeError("pillow failed")

    monkeypatch.setattr(summary_views, "_render_summary", failing_render)
    interaction = _Interaction()

    await summary_views.show_account_summary_for_interaction(
        interaction,
        author_id=42,
        display_name="Tester",
        accounts_loader=loader,
    )

    assert calls == [42]
    assert interaction.original_edits[-1]["embed"].title.startswith("Account Summary")
    assert interaction.original_edits[-1]["attachments"] == []


@pytest.mark.asyncio
async def test_csv_is_private_followup_and_visual_state_is_unchanged() -> None:
    view = summary_views.AccountSummaryView(
        author_id=42,
        display_name="Tester",
        payload=_payload(),
    )
    interaction = _Interaction()
    button = next(child for child in view.children if child.label == "Download CSV")

    await button.callback(interaction)

    _args, kwargs = interaction.followup.sent[-1]
    assert kwargs["ephemeral"] is True
    assert kwargs["file"].filename.startswith("me_account_summary_42_")
    assert getattr(kwargs["file"].fp, "closed", True) is True
    assert interaction.original_edits == []


@pytest.mark.asyncio
async def test_account_summary_rejects_non_owner() -> None:
    view = summary_views.AccountSummaryView(
        author_id=42,
        display_name="Tester",
        payload=_payload(),
    )
    interaction = _Interaction(user_id=99)

    assert await view.interaction_check(interaction) is False
    assert interaction.response.sent[-1][1]["ephemeral"] is True
