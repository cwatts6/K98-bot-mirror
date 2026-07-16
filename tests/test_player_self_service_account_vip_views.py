from __future__ import annotations

import asyncio
import logging
from types import SimpleNamespace

import pytest

from inventory.models import InventoryGovernorProfile, RegisteredGovernor
from inventory.vip_levels import InventoryVipLevel
from player_self_service.account_service import AccountCentreState
from ui.views import (
    player_self_service_account_views as account_views,
    player_self_service_account_vip_views as vip_views,
)


class _Response:
    def __init__(self) -> None:
        self.sent = []
        self.edited = []
        self.deferred = []
        self._done = True

    def is_done(self):
        return self._done

    async def send_message(self, *args, **kwargs):
        self.sent.append((args, kwargs))

    async def edit_message(self, **kwargs):
        self.edited.append(kwargs)

    async def defer(self, **kwargs):
        self.deferred.append(kwargs)
        self._done = True


class _FailingDeferResponse(_Response):
    def __init__(self, failures: tuple[BaseException, ...]) -> None:
        super().__init__()
        self._done = False
        self.failures = list(failures)

    async def defer(self, **kwargs):
        self.deferred.append(kwargs)
        raise self.failures.pop(0)


class _Followup:
    def __init__(self) -> None:
        self.sent = []

    async def send(self, *args, **kwargs):
        self.sent.append((args, kwargs))


class _Interaction:
    def __init__(self, user_id: int = 42) -> None:
        self.user = SimpleNamespace(id=user_id)
        self.response = _Response()
        self.followup = _Followup()
        self.message = SimpleNamespace(id=123)
        self.original_edits = []

    async def edit_original_response(self, **kwargs):
        self.original_edits.append(kwargs)
        return self.message


async def _summary_loader(_user_id: int):
    return None


async def _profile_loader(governor_id: int) -> InventoryGovernorProfile:
    return InventoryGovernorProfile.default(governor_id)


def _governors(count: int) -> tuple[RegisteredGovernor, ...]:
    return tuple(
        RegisteredGovernor(1000 + index, f"Governor {index}", "Main" if index == 0 else "Alt")
        for index in range(count)
    )


def _common(governors: tuple[RegisteredGovernor, ...]):
    state = vip_views._VipJourneyState()
    return {
        "author_id": 42,
        "display_name": "Tester",
        "governors": governors,
        "host_message": SimpleNamespace(id=999),
        "summary_loader": _summary_loader,
        "profile_loader": _profile_loader,
        "state": state,
        "generation": state.advance(),
        "timeout": 120,
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "failures",
    [
        (RuntimeError("primary defer failed"),),
        (TypeError("ephemeral unsupported"), RuntimeError("fallback defer failed")),
    ],
)
async def test_private_defer_logs_and_suppresses_api_failures(failures, caplog) -> None:
    interaction = _Interaction()
    interaction.response = _FailingDeferResponse(failures)

    with caplog.at_level(logging.DEBUG, logger=vip_views.logger.name):
        await vip_views._defer_private(interaction)

    assert "player_self_service_account_vip_defer_failed" in caplog.text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "failures",
    [
        (asyncio.CancelledError(),),
        (TypeError("ephemeral unsupported"), asyncio.CancelledError()),
    ],
)
async def test_private_defer_propagates_cancellation(failures) -> None:
    interaction = _Interaction()
    interaction.response = _FailingDeferResponse(failures)

    with pytest.raises(asyncio.CancelledError):
        await vip_views._defer_private(interaction)


@pytest.mark.asyncio
async def test_zero_governors_returns_register_guidance(monkeypatch) -> None:
    async def load(_user_id: int):
        return []

    async def centre(_user_id: int):
        return AccountCentreState(
            ok=True,
            linked_count=0,
            main_label="not set",
            registered_slots=(),
            free_slots=("Main",),
        )

    monkeypatch.setattr(vip_views.account_service, "build_account_centre_state", centre)
    interaction = _Interaction()

    await vip_views.show_account_vip_update(
        interaction,
        author_id=42,
        display_name="Tester",
        host_message=None,
        governor_loader=load,
    )

    edit = interaction.original_edits[-1]
    assert "Use Register account first" in edit["content"]
    assert isinstance(edit["view"], account_views.AccountManageView)


@pytest.mark.asyncio
async def test_one_governor_is_identified_and_preselected_without_dashboard_context() -> None:
    governors = _governors(1)
    profile_calls = []

    async def load_governors(_user_id: int):
        return list(governors)

    async def load_profile(governor_id: int):
        profile_calls.append(governor_id)
        return InventoryGovernorProfile(
            governor_id=governor_id,
            vip_level_code=InventoryVipLevel.VIP_18.value,
            vip_level_label="VIP 18",
        )

    interaction = _Interaction()
    await vip_views.show_account_vip_update(
        interaction,
        author_id=42,
        display_name="Tester",
        host_message=None,
        governor_loader=load_governors,
        profile_loader=load_profile,
    )

    edit = interaction.original_edits[-1]
    assert isinstance(edit["view"], vip_views.AccountVipEditView)
    assert "Governor 0 (`1000`)" in edit["content"]
    assert "VIP 18" in edit["content"]
    assert profile_calls == [1000]


@pytest.mark.asyncio
async def test_multiple_governors_require_explicit_selection_and_do_not_fetch_profiles() -> None:
    profile_calls = []

    async def load_governors(_user_id: int):
        return list(_governors(3))

    async def load_profile(governor_id: int):
        profile_calls.append(governor_id)
        return InventoryGovernorProfile.default(governor_id)

    interaction = _Interaction()
    await vip_views.show_account_vip_update(
        interaction,
        author_id=42,
        display_name="Tester",
        host_message=None,
        governor_loader=load_governors,
        profile_loader=load_profile,
    )

    view = interaction.original_edits[-1]["view"]
    assert isinstance(view, vip_views.AccountVipGovernorView)
    assert profile_calls == []
    selector = next(item for item in view.children if isinstance(item, vip_views._GovernorSelect))
    assert len(selector.options) == 3


@pytest.mark.asyncio
async def test_more_than_25_governors_are_paged_without_dropping_options() -> None:
    governors = _governors(26)
    common = _common(governors)
    view = vip_views.AccountVipGovernorView(page=0, **common)
    first = next(item for item in view.children if isinstance(item, vip_views._GovernorSelect))
    assert len(first.options) == 25
    assert view.total_pages == 2

    interaction = _Interaction()
    await view.next_button.callback(interaction)
    next_view = interaction.original_edits[-1]["view"]
    assert isinstance(next_view, vip_views.AccountVipGovernorView)
    second = next(
        item for item in next_view.children if isinstance(item, vip_views._GovernorSelect)
    )
    assert [option.value for option in second.options] == [str(governors[-1].governor_id)]
    assert next_view.profile_loader is _profile_loader


@pytest.mark.asyncio
async def test_vip_editor_rejects_foreign_stale_and_forged_governor_selection() -> None:
    common = _common(_governors(2))
    view = vip_views.AccountVipGovernorView(page=0, **common)
    foreign = _Interaction(user_id=99)
    assert await view.interaction_check(foreign) is False

    view.state.advance()
    stale = _Interaction()
    assert await view.interaction_check(stale) is False
    assert "superseded" in stale.response.sent[-1][0][0]

    fresh_common = _common(_governors(2))
    fresh = vip_views.AccountVipGovernorView(page=0, **fresh_common)
    interaction = _Interaction()
    selector = next(item for item in fresh.children if isinstance(item, vip_views._GovernorSelect))
    selector._selected_values = ["999999"]
    selector._interaction = SimpleNamespace(data={})
    await selector.callback(interaction)
    assert interaction.original_edits == []
    assert "not available" in interaction.response.sent[-1][0][0]


@pytest.mark.asyncio
@pytest.mark.parametrize("selected_values", [["not-a-governor"], []])
async def test_vip_editor_rejects_malformed_governor_selection(selected_values) -> None:
    common = _common(_governors(2))
    view = vip_views.AccountVipGovernorView(page=0, **common)
    interaction = _Interaction()
    selector = next(item for item in view.children if isinstance(item, vip_views._GovernorSelect))
    selector._selected_values = selected_values
    selector._interaction = SimpleNamespace(data={})

    await selector.callback(interaction)

    assert interaction.original_edits == []
    assert "not available" in interaction.response.sent[-1][0][0]


@pytest.mark.asyncio
async def test_save_rechecks_access_refreshes_accounts_and_preserves_not_set(monkeypatch) -> None:
    governor = _governors(1)[0]
    calls = []

    async def update(**kwargs):
        calls.append(kwargs)
        return InventoryGovernorProfile(
            governor_id=governor.governor_id,
            vip_level_code=None,
            vip_level_label="Unknown / not set",
            updated_by_discord_user_id=42,
        )

    async def refresh(**kwargs):
        calls.append(("refresh", kwargs))
        return True

    async def centre(_user_id: int):
        return AccountCentreState(
            ok=True,
            linked_count=1,
            main_label="Governor 0",
            registered_slots=("Main",),
            free_slots=(),
        )

    monkeypatch.setattr(vip_views.profile_service, "update_inventory_vip", update)
    monkeypatch.setattr(account_views, "_refresh_host_page", refresh)
    monkeypatch.setattr(vip_views.account_service, "build_account_centre_state", centre)
    view = vip_views.AccountVipEditView(
        governor=governor,
        profile=InventoryGovernorProfile.default(governor.governor_id),
        **_common((governor,)),
    )
    view.selected_level = InventoryVipLevel.UNKNOWN
    interaction = _Interaction()

    await view.save_button.callback(interaction)

    assert calls[0]["discord_user_id"] == 42
    assert calls[0]["governor_id"] == governor.governor_id
    assert calls[0]["vip_level_code"] == InventoryVipLevel.UNKNOWN.value
    assert calls[0]["discord_user"] is interaction.user
    assert calls[1][0] == "refresh"
    assert "Unknown / not set" in interaction.original_edits[-1]["content"]
    assert "Accounts card has been refreshed" in interaction.original_edits[-1]["content"]
    assert isinstance(interaction.original_edits[-1]["view"], account_views.AccountManageView)


@pytest.mark.asyncio
async def test_save_permission_failure_does_not_refresh_or_complete(monkeypatch) -> None:
    async def update(**_kwargs):
        raise PermissionError("You can only update VIP for governors registered to you.")

    async def forbidden_refresh(**_kwargs):
        raise AssertionError("failed save must not refresh host")

    monkeypatch.setattr(vip_views.profile_service, "update_inventory_vip", update)
    monkeypatch.setattr(account_views, "_refresh_host_page", forbidden_refresh)
    governor = _governors(1)[0]
    view = vip_views.AccountVipEditView(
        governor=governor,
        profile=InventoryGovernorProfile.default(governor.governor_id),
        **_common((governor,)),
    )
    view.selected_level = InventoryVipLevel.VIP_19
    interaction = _Interaction()

    await view.save_button.callback(interaction)

    assert "registered to you" in interaction.followup.sent[-1][0][0]
    assert view.completed is False
    assert interaction.original_edits == []


@pytest.mark.asyncio
async def test_vip_save_cancellation_releases_completed_state(monkeypatch) -> None:
    async def update(**_kwargs):
        raise asyncio.CancelledError()

    monkeypatch.setattr(vip_views.profile_service, "update_inventory_vip", update)
    governor = _governors(1)[0]
    view = vip_views.AccountVipEditView(
        governor=governor,
        profile=InventoryGovernorProfile.default(governor.governor_id),
        **_common((governor,)),
    )
    view.selected_level = InventoryVipLevel.VIP_19

    with pytest.raises(asyncio.CancelledError):
        await view.save_button.callback(_Interaction())

    assert view.completed is False
    assert view.state.lock.locked() is False
