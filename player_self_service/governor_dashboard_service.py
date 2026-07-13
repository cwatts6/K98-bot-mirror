"""Service foundation for the future governor-first /me dashboard."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import replace
import logging
from typing import Any

from inventory import profile_service, reporting_service
from inventory.models import RegisteredGovernor
from player_self_service import governor_dashboard_dal
from player_self_service.governor_dashboard_models import (
    GovernorDashboardAccessDecision,
    GovernorDashboardActivityHonours,
    GovernorDashboardContext,
    GovernorDashboardDataRow,
    GovernorDashboardFreshness,
    GovernorDashboardHistoricalHighlights,
    GovernorDashboardIdentity,
    GovernorDashboardInventoryHighlights,
    GovernorDashboardLatestMetrics,
    GovernorDashboardOption,
    GovernorDashboardPayload,
    GovernorDashboardProfileStatus,
    GovernorDashboardResolution,
    GovernorDashboardSelfView,
    GovernorDashboardViewerMode,
)
from services.governor_account_service import (
    AccountResolutionSummary,
    ResolvedAccount,
    get_account_summary_for_user,
)

logger = logging.getLogger(__name__)

AccountLoader = Callable[[int], Awaitable[AccountResolutionSummary]]
DashboardDataLoader = Callable[[int], Awaitable[GovernorDashboardDataRow | None]]
VipProfileLoader = Callable[[int], Awaitable[Any]]
InventoryHighlightsLoader = Callable[[int, str], Awaitable[GovernorDashboardInventoryHighlights]]

SELF_VIEW_ACTIONS = (
    "accounts",
    "reminders",
    "preferences",
    "exports",
    "resources",
    "materials",
    "speedups",
)
INSPECT_VIEW_ACTIONS: tuple[str, ...] = ()


class GovernorDashboardAccessDenied(PermissionError):
    """Raised when a self-service dashboard request targets an unlinked governor."""


def _normalize_governor_id(value: Any) -> int | None:
    try:
        gid = int(str(value).strip())
    except (TypeError, ValueError):
        return None
    return gid if gid > 0 else None


def _option_from_account(
    account: ResolvedAccount,
    *,
    default_governor_id: int | None,
) -> GovernorDashboardOption:
    return GovernorDashboardOption(
        governor_id=int(account.governor_id),
        governor_id_str=account.governor_id_str,
        governor_name=account.governor_name or account.governor_id_str,
        account_type=str(account.slot),
        is_default=bool(default_governor_id and int(account.governor_id) == default_governor_id),
    )


def _default_governor_id_from_summary(summary: AccountResolutionSummary) -> int | None:
    main = summary.ordered_accounts.get("Main") or {}
    main_gid = _normalize_governor_id(
        main.get("GovernorID") or main.get("GovernorId") or main.get("governor_id")
    )
    if main_gid:
        return main_gid
    first = summary.first_account
    return int(first.governor_id) if first else None


def _options_from_summary(
    summary: AccountResolutionSummary,
) -> tuple[GovernorDashboardOption, ...]:
    default_governor_id = _default_governor_id_from_summary(summary)
    return tuple(
        _option_from_account(account, default_governor_id=default_governor_id)
        for account in summary.resolved_accounts
    )


def _find_option(
    options: tuple[GovernorDashboardOption, ...],
    governor_id: int,
) -> GovernorDashboardOption | None:
    return next((option for option in options if option.governor_id == int(governor_id)), None)


def _context_for_option(
    *,
    discord_user_id: int,
    option: GovernorDashboardOption | None,
    governor_id: int | None = None,
    viewer_mode: GovernorDashboardViewerMode,
    allowed: bool,
    reason: str,
) -> GovernorDashboardContext:
    selected_governor_id = option.governor_id if option else governor_id
    selected_governor_name = option.governor_name if option else None
    is_self = viewer_mode == "self"
    return GovernorDashboardContext(
        viewer_discord_id=int(discord_user_id),
        viewer_mode=viewer_mode,
        selected_governor_id=selected_governor_id,
        selected_governor_name=selected_governor_name,
        is_linked_to_viewer=option is not None,
        account_type_for_self_view=option.account_type if is_self and option else None,
        access_decision=GovernorDashboardAccessDecision(allowed=allowed, reason=reason),
        privacy_profile="self_view" if is_self else "inspect_safe",
    )


async def get_dashboard_governor_options(
    discord_user_id: int,
    *,
    account_loader: AccountLoader = get_account_summary_for_user,
) -> tuple[GovernorDashboardOption, ...]:
    summary = await account_loader(int(discord_user_id))
    if not summary.ok:
        logger.warning(
            "governor_dashboard_options_unavailable discord_user_id=%s error=%s",
            discord_user_id,
            summary.error,
        )
        return ()
    return _options_from_summary(summary)


async def resolve_default_dashboard_governor(
    discord_user_id: int,
    *,
    account_loader: AccountLoader = get_account_summary_for_user,
) -> GovernorDashboardOption | None:
    options = await get_dashboard_governor_options(
        int(discord_user_id),
        account_loader=account_loader,
    )
    return next(
        (option for option in options if option.is_default), options[0] if options else None
    )


async def resolve_dashboard_context(
    discord_user_id: int,
    governor_id: int | str | None = None,
    *,
    viewer_mode: GovernorDashboardViewerMode = "self",
    allow_unlinked_inspect: bool = False,
    account_loader: AccountLoader = get_account_summary_for_user,
) -> GovernorDashboardResolution:
    if viewer_mode not in ("self", "inspect"):
        raise ValueError(f"Unsupported dashboard viewer mode: {viewer_mode!r}")

    requested_gid = _normalize_governor_id(governor_id)
    if viewer_mode == "inspect" and governor_id is not None:
        if requested_gid is None:
            return GovernorDashboardResolution(
                state="denied",
                options=(),
                reason="invalid governor id",
            )
        try:
            summary = await account_loader(int(discord_user_id))
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception(
                "governor_dashboard_inspect_options_unavailable discord_user_id=%s",
                discord_user_id,
            )
            summary = None
        options = _options_from_summary(summary) if summary and summary.ok else ()
        default_option = next(
            (option for option in options if option.is_default),
            options[0] if options else None,
        )
        linked_option = _find_option(options, requested_gid)
        if linked_option is None and not allow_unlinked_inspect:
            context = _context_for_option(
                discord_user_id=int(discord_user_id),
                option=None,
                governor_id=requested_gid,
                viewer_mode=viewer_mode,
                allowed=False,
                reason=("inspect mode requires an explicit unlinked-governor permission gate"),
            )
            return GovernorDashboardResolution(
                state="denied",
                options=options,
                default_option=default_option,
                context=context,
                reason=context.access_decision.reason,
            )
        context = _context_for_option(
            discord_user_id=int(discord_user_id),
            option=linked_option,
            governor_id=requested_gid,
            viewer_mode=viewer_mode,
            allowed=True,
            reason=(
                "inspect mode"
                if linked_option is not None
                else "inspect mode unlinked access explicitly allowed"
            ),
        )
        return GovernorDashboardResolution(
            state="selected",
            options=options,
            default_option=default_option,
            context=context,
        )

    summary = await account_loader(int(discord_user_id))
    if not summary.ok:
        return GovernorDashboardResolution(
            state="unavailable",
            options=(),
            reason=summary.error or "account source unavailable",
        )

    options = _options_from_summary(summary)
    default_option = next(
        (option for option in options if option.is_default),
        options[0] if options else None,
    )

    if governor_id is not None and requested_gid is None:
        return GovernorDashboardResolution(
            state="denied",
            options=options,
            default_option=default_option,
            reason="invalid governor id",
        )

    if requested_gid is None:
        if not options:
            return GovernorDashboardResolution(
                state="requires_setup",
                options=options,
                reason="no linked governors",
            )
        if len(options) == 1:
            option = options[0]
            return GovernorDashboardResolution(
                state="selected",
                options=options,
                default_option=option,
                context=_context_for_option(
                    discord_user_id=int(discord_user_id),
                    option=option,
                    viewer_mode=viewer_mode,
                    allowed=True,
                    reason="linked governor selected",
                ),
            )
        return GovernorDashboardResolution(
            state="requires_selection",
            options=options,
            default_option=default_option,
            reason="multiple linked governors",
        )

    linked_option = _find_option(options, requested_gid)
    if viewer_mode == "self" and linked_option is None:
        context = _context_for_option(
            discord_user_id=int(discord_user_id),
            option=None,
            governor_id=requested_gid,
            viewer_mode=viewer_mode,
            allowed=False,
            reason="governor is not linked to the invoking Discord user",
        )
        return GovernorDashboardResolution(
            state="denied",
            options=options,
            default_option=default_option,
            context=context,
            reason=context.access_decision.reason,
        )

    if viewer_mode == "inspect" and linked_option is None and not allow_unlinked_inspect:
        context = _context_for_option(
            discord_user_id=int(discord_user_id),
            option=None,
            governor_id=requested_gid,
            viewer_mode=viewer_mode,
            allowed=False,
            reason="inspect mode requires an explicit unlinked-governor permission gate",
        )
        return GovernorDashboardResolution(
            state="denied",
            options=options,
            default_option=default_option,
            context=context,
            reason=context.access_decision.reason,
        )

    context = _context_for_option(
        discord_user_id=int(discord_user_id),
        option=linked_option,
        governor_id=requested_gid,
        viewer_mode=viewer_mode,
        allowed=True,
        reason=(
            "inspect mode unlinked access explicitly allowed"
            if viewer_mode == "inspect" and linked_option is None
            else "inspect mode" if viewer_mode == "inspect" else "linked governor selected"
        ),
    )
    return GovernorDashboardResolution(
        state="selected",
        options=options,
        default_option=default_option,
        context=context,
    )


async def assert_dashboard_governor_access(
    discord_user_id: int,
    governor_id: int | str,
    *,
    account_loader: AccountLoader = get_account_summary_for_user,
) -> GovernorDashboardContext:
    resolution = await resolve_dashboard_context(
        int(discord_user_id),
        governor_id,
        viewer_mode="self",
        account_loader=account_loader,
    )
    if not resolution.context or not resolution.context.access_allowed:
        raise GovernorDashboardAccessDenied(resolution.reason or "dashboard access denied")
    return resolution.context


async def _fetch_dashboard_data(governor_id: int) -> GovernorDashboardDataRow:
    try:
        return await asyncio.to_thread(
            governor_dashboard_dal.fetch_governor_dashboard_data,
            int(governor_id),
        )
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception(
            "governor_dashboard_data_fetch_failed governor_id=%s using_empty_payload=True",
            governor_id,
        )
        return GovernorDashboardDataRow(governor_id=int(governor_id))


async def _fetch_inventory_highlights(
    governor_id: int,
    governor_name: str,
) -> GovernorDashboardInventoryHighlights:
    """Load selected-governor Inventory totals without changing Inventory contracts."""
    governor = RegisteredGovernor(
        governor_id=int(governor_id),
        governor_name=str(governor_name),
        account_type="Self",
    )
    try:
        snapshot = await reporting_service.build_latest_inventory_snapshot([governor])
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception(
            "governor_dashboard_inventory_fetch_failed governor_id=%s using_empty_highlights=True",
            governor_id,
        )
        return GovernorDashboardInventoryHighlights()

    resources = snapshot.resources[0] if snapshot.resources else None
    speedups = snapshot.speedups[0] if snapshot.speedups else None
    materials = snapshot.materials[0] if snapshot.materials else None
    speedup_days = None
    if speedups is not None:
        speedup_days = sum(
            (
                float(speedups.building_days),
                float(speedups.research_days),
                float(speedups.training_days),
                float(speedups.healing_days),
                float(speedups.universal_days),
            )
        )
    return GovernorDashboardInventoryHighlights(
        total_resources=resources.total if resources is not None else None,
        total_speedup_days=speedup_days,
        total_legendary_materials=(
            float(materials.total_legendary) if materials is not None else None
        ),
    )


def _missing_label(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    return False


def _ark_ratio(joined: int | None, won: int | None) -> tuple[float | None, str]:
    if not joined or joined <= 0:
        return None, "N/A"
    ratio = float(won or 0) / float(joined)
    return ratio, f"{ratio:.0%}"


def _vip_label(value: Any) -> str | None:
    label = str(value or "").strip()
    if not label or label.casefold() == "unknown / not set":
        return None
    return label


def _missing_fields(
    *,
    identity: GovernorDashboardIdentity,
    latest_metrics: GovernorDashboardLatestMetrics,
    historical_highlights: GovernorDashboardHistoricalHighlights,
    activity_honours: GovernorDashboardActivityHonours,
    profile_status: GovernorDashboardProfileStatus,
    freshness: GovernorDashboardFreshness,
    self_view: GovernorDashboardSelfView | None,
) -> tuple[str, ...]:
    values = {
        "alliance": identity.alliance,
        "civilisation": identity.civilisation,
        "power": latest_metrics.power,
        "kill_points": latest_metrics.kill_points,
        "dead": latest_metrics.dead,
        "helps": latest_metrics.helps,
        "healed": latest_metrics.healed,
        "highest_acclaim": historical_highlights.highest_acclaim,
        "times_named_autarch": historical_highlights.times_named_autarch,
        "times_autarch_participated": historical_highlights.times_autarch_participated,
        "ark_joined": activity_honours.ark_joined,
        "ark_won": activity_honours.ark_won,
        "conduct_score": profile_status.conduct_score,
        "updated_at_utc": freshness.updated_at_utc,
        "location": (
            identity.location_x
            if identity.location_x is not None and identity.location_y is not None
            else None
        ),
    }
    if self_view is not None:
        values["vip_level_label"] = self_view.vip_level_label
    return tuple(key for key, value in values.items() if _missing_label(value))


async def build_governor_dashboard_payload(
    context: GovernorDashboardContext,
    *,
    data_loader: DashboardDataLoader = _fetch_dashboard_data,
    vip_profile_loader: VipProfileLoader = profile_service.fetch_inventory_profile,
    inventory_loader: InventoryHighlightsLoader = _fetch_inventory_highlights,
) -> GovernorDashboardPayload:
    if not context.access_allowed or context.selected_governor_id is None:
        raise GovernorDashboardAccessDenied(context.access_decision.reason)

    selected_governor_name = context.selected_governor_name or str(context.selected_governor_id)
    data_task = data_loader(int(context.selected_governor_id))
    vip_task = None
    inventory_task = None
    if context.viewer_mode == "self":
        vip_task = vip_profile_loader(int(context.selected_governor_id))
        inventory_task = inventory_loader(
            int(context.selected_governor_id),
            selected_governor_name,
        )

    if vip_task is None:
        data = await data_task
        inventory = GovernorDashboardInventoryHighlights()
        vip_label = None
    else:
        assert inventory_task is not None
        data, vip_profile, inventory = await asyncio.gather(
            data_task,
            vip_task,
            inventory_task,
        )
        vip_label = _vip_label(getattr(vip_profile, "vip_level_label", None))

    if data is None:
        data = GovernorDashboardDataRow(governor_id=int(context.selected_governor_id))

    governor_name = (
        data.governor_name
        or context.selected_governor_name
        or f"Governor {int(context.selected_governor_id)}"
    )
    identity = GovernorDashboardIdentity(
        governor_name=governor_name,
        governor_id=int(context.selected_governor_id),
        alliance=data.alliance,
        civilisation=data.civilization,
        location_x=data.location_x,
        location_y=data.location_y,
    )
    latest_metrics = GovernorDashboardLatestMetrics(
        power=data.power,
        kill_points=data.kill_points,
        dead=data.dead,
        helps=data.helps,
        healed=data.healed,
    )
    historical_highlights = GovernorDashboardHistoricalHighlights(
        highest_acclaim=data.highest_acclaim,
        times_named_autarch=data.times_named_autarch,
        times_autarch_participated=data.kvk_played,
    )
    ark_ratio, ark_ratio_label = _ark_ratio(data.ark_joined, data.ark_won)
    activity_honours = GovernorDashboardActivityHonours(
        ark_joined=data.ark_joined,
        ark_won=data.ark_won,
        ark_win_ratio=ark_ratio,
        ark_win_ratio_label=ark_ratio_label,
    )
    profile_status = GovernorDashboardProfileStatus(conduct_score=data.conduct)
    freshness = GovernorDashboardFreshness(
        updated_at_utc=data.updated_at_utc,
        scan_order=data.scan_order,
        source="KingdomScanData4" if data.updated_at_utc is not None else None,
    )
    self_view = (
        GovernorDashboardSelfView(
            account_type=context.account_type_for_self_view,
            vip_level_label=vip_label,
        )
        if context.viewer_mode == "self"
        else None
    )
    payload = GovernorDashboardPayload(
        context=context,
        identity=identity,
        latest_metrics=latest_metrics,
        historical_highlights=historical_highlights,
        activity_honours=activity_honours,
        profile_status=profile_status,
        freshness=freshness,
        inventory=inventory,
        available_actions=(
            SELF_VIEW_ACTIONS if context.viewer_mode == "self" else INSPECT_VIEW_ACTIONS
        ),
        missing_fields=(),
        self_view=self_view,
    )
    return replace(
        payload,
        missing_fields=_missing_fields(
            identity=identity,
            latest_metrics=latest_metrics,
            historical_highlights=historical_highlights,
            activity_honours=activity_honours,
            profile_status=profile_status,
            freshness=freshness,
            self_view=self_view,
        ),
    )
