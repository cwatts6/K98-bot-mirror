"""Account-centre service logic for the /me player command centre."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import logging
from typing import Literal

from registry import registry_service
from services.governor_account_service import (
    AccountResolutionSummary,
    ResolvedAccount,
    get_account_summary_for_user,
)
from services.governor_lookup_service import (
    GovernorLookupResult,
    resolve_governor_query,
)

logger = logging.getLogger(__name__)

AccountAction = Literal["register", "replace", "remove"]

AccountLoader = Callable[[int], Awaitable[AccountResolutionSummary]]
GovernorResolver = Callable[[str], Awaitable[GovernorLookupResult]]
ClaimChecker = Callable[[str | int, int], bool]
RegisterWriter = Callable[..., tuple[bool, str | None]]
ModifyWriter = Callable[..., tuple[bool, str | None]]
RemoveWriter = Callable[..., tuple[bool, str | None]]


@dataclass(frozen=True, slots=True)
class AccountSlot:
    slot: str
    governor_id: str
    governor_name: str

    @property
    def label(self) -> str:
        if self.governor_name and self.governor_id:
            return f"{self.slot}: {self.governor_name}"
        return self.slot

    @property
    def description(self) -> str:
        return f"Governor ID {self.governor_id}" if self.governor_id else "Empty slot"


@dataclass(frozen=True, slots=True)
class AccountCentreState:
    ok: bool
    linked_count: int
    main_label: str
    registered_slots: tuple[AccountSlot, ...]
    free_slots: tuple[str, ...]
    error: str | None = None

    @property
    def can_register(self) -> bool:
        return self.ok and bool(self.free_slots)

    @property
    def can_modify(self) -> bool:
        return self.ok and bool(self.registered_slots)

    @property
    def can_remove(self) -> bool:
        return self.can_modify


@dataclass(frozen=True, slots=True)
class AccountLookupOutcome:
    status: Literal["found", "matches", "not_found"]
    query: str
    governor_id: str | None = None
    governor_name: str | None = None
    matches: tuple[dict[str, str], ...] = ()
    message: str = "No matches found."


@dataclass(frozen=True, slots=True)
class AccountConfirmation:
    action: AccountAction
    account_type: str
    governor_id: str | None = None
    governor_name: str | None = None
    current_governor_id: str | None = None
    current_governor_name: str | None = None

    @property
    def title(self) -> str:
        if self.action == "remove":
            return f"Remove {self.account_type}?"
        if self.action == "replace":
            return f"Replace {self.account_type}?"
        return f"Register {self.account_type}?"

    @property
    def body(self) -> str:
        if self.action == "remove":
            current = _format_governor(self.current_governor_name, self.current_governor_id)
            return f"Remove {self.account_type} currently linked to {current}?"
        target = _format_governor(self.governor_name, self.governor_id)
        if self.action == "replace":
            current = _format_governor(self.current_governor_name, self.current_governor_id)
            return f"Replace {self.account_type} ({current}) with {target}?"
        return f"Register {target} in {self.account_type}?"


@dataclass(frozen=True, slots=True)
class AccountMutationResult:
    ok: bool
    message: str


def _format_governor(name: str | None, governor_id: str | None) -> str:
    clean_name = (name or "Unknown").strip() or "Unknown"
    clean_id = (governor_id or "").strip()
    return f"{clean_name} ({clean_id})" if clean_id else clean_name


def _slot_from_resolved(account: ResolvedAccount) -> AccountSlot:
    return AccountSlot(
        slot=account.slot,
        governor_id=account.governor_id_str,
        governor_name=account.governor_name,
    )


def build_state_from_summary(summary: AccountResolutionSummary) -> AccountCentreState:
    if not summary.ok:
        return AccountCentreState(
            ok=False,
            linked_count=0,
            main_label="unknown",
            registered_slots=(),
            free_slots=(),
            error=summary.error or "account source unavailable",
        )

    main = summary.ordered_accounts.get("Main") or {}
    main_id = str(main.get("GovernorID") or main.get("GovernorId") or "").strip()
    main_name = str(main.get("GovernorName") or main.get("governor_name") or "").strip()
    main_label = _format_governor(main_name or "Main account", main_id) if main_id else "not set"
    return AccountCentreState(
        ok=True,
        linked_count=len(summary.resolved_accounts),
        main_label=main_label,
        registered_slots=tuple(
            _slot_from_resolved(account) for account in summary.resolved_accounts
        ),
        free_slots=tuple(summary.free_slots()),
    )


async def build_account_centre_state(
    discord_user_id: int,
    *,
    account_loader: AccountLoader = get_account_summary_for_user,
) -> AccountCentreState:
    summary = await account_loader(int(discord_user_id))
    return build_state_from_summary(summary)


def _invalid_account_type(account_type: str) -> str | None:
    if account_type in registry_service.VALID_ACCOUNT_TYPES:
        return None
    return f"`{account_type}` is not a valid account slot."


async def lookup_governor(
    raw_query: str,
    *,
    resolver: GovernorResolver = resolve_governor_query,
) -> AccountLookupOutcome:
    result = await resolver((raw_query or "").strip())
    return AccountLookupOutcome(
        status=result.status,
        query=result.query,
        governor_id=result.governor_id,
        governor_name=result.governor_name,
        matches=result.matches,
        message=result.message,
    )


async def _resolve_exact_governor(
    raw_query: str,
    *,
    resolver: GovernorResolver,
) -> tuple[str | None, str | None, str | None]:
    query = (raw_query or "").strip()
    if not query:
        return None, None, "Governor ID or name is required."

    result = await lookup_governor(query, resolver=resolver)
    if result.status == "found" and result.governor_id:
        return result.governor_id, result.governor_name or "Unknown", None
    if result.status == "matches":
        return (
            None,
            None,
            "Multiple possible governors matched. Use Find Governor ID first, then enter the exact ID.",
        )
    return None, None, result.message or "Governor not found."


async def prepare_register_confirmation(
    discord_user_id: int,
    account_type: str,
    governor_query: str,
    *,
    account_loader: AccountLoader = get_account_summary_for_user,
    resolver: GovernorResolver = resolve_governor_query,
    claim_checker: ClaimChecker = registry_service.check_governor_claimed_by_other,
) -> tuple[AccountConfirmation | None, str | None]:
    slot_error = _invalid_account_type(account_type)
    if slot_error:
        return None, slot_error

    summary = await account_loader(int(discord_user_id))
    if not summary.ok:
        return None, "Account data is temporarily unavailable. Please try again in a moment."
    if account_type not in summary.free_slots():
        return None, f"`{account_type}` is already registered. Use Replace account instead."

    governor_id, governor_name, lookup_error = await _resolve_exact_governor(
        governor_query,
        resolver=resolver,
    )
    if lookup_error:
        return None, lookup_error
    if summary.contains_governor_id(governor_id or ""):
        return None, "That Governor ID is already linked to your account centre."

    claimed = await asyncio.to_thread(claim_checker, governor_id, int(discord_user_id))
    if claimed:
        return None, "That Governor ID is already registered to another Discord user."

    return (
        AccountConfirmation(
            action="register",
            account_type=account_type,
            governor_id=governor_id,
            governor_name=governor_name,
        ),
        None,
    )


async def prepare_replace_confirmation(
    discord_user_id: int,
    account_type: str,
    governor_query: str,
    *,
    account_loader: AccountLoader = get_account_summary_for_user,
    resolver: GovernorResolver = resolve_governor_query,
    claim_checker: ClaimChecker = registry_service.check_governor_claimed_by_other,
) -> tuple[AccountConfirmation | None, str | None]:
    slot_error = _invalid_account_type(account_type)
    if slot_error:
        return None, slot_error

    summary = await account_loader(int(discord_user_id))
    if not summary.ok:
        return None, "Account data is temporarily unavailable. Please try again in a moment."
    current = summary.ordered_accounts.get(account_type)
    if not current:
        return None, f"`{account_type}` is not currently registered."

    governor_id, governor_name, lookup_error = await _resolve_exact_governor(
        governor_query,
        resolver=resolver,
    )
    if lookup_error:
        return None, lookup_error

    current_gid = str(current.get("GovernorID") or "").strip()
    if current_gid == str(governor_id or "").strip():
        return None, f"`{account_type}` is already linked to that Governor ID."
    if summary.contains_governor_id(governor_id or ""):
        return None, "That Governor ID is already linked to another slot in your account centre."

    claimed = await asyncio.to_thread(claim_checker, governor_id, int(discord_user_id))
    if claimed:
        return None, "That Governor ID is already registered to another Discord user."

    return (
        AccountConfirmation(
            action="replace",
            account_type=account_type,
            governor_id=governor_id,
            governor_name=governor_name,
            current_governor_id=current_gid,
            current_governor_name=str(current.get("GovernorName") or ""),
        ),
        None,
    )


async def prepare_remove_confirmation(
    discord_user_id: int,
    account_type: str,
    *,
    account_loader: AccountLoader = get_account_summary_for_user,
) -> tuple[AccountConfirmation | None, str | None]:
    slot_error = _invalid_account_type(account_type)
    if slot_error:
        return None, slot_error

    summary = await account_loader(int(discord_user_id))
    if not summary.ok:
        return None, "Account data is temporarily unavailable. Please try again in a moment."
    current = summary.ordered_accounts.get(account_type)
    if not current:
        return None, f"`{account_type}` is not currently registered."

    return (
        AccountConfirmation(
            action="remove",
            account_type=account_type,
            current_governor_id=str(current.get("GovernorID") or ""),
            current_governor_name=str(current.get("GovernorName") or ""),
        ),
        None,
    )


async def confirm_register(
    discord_user_id: int,
    discord_name: str,
    confirmation: AccountConfirmation,
    *,
    writer: RegisterWriter = registry_service.register_governor,
) -> AccountMutationResult:
    if confirmation.action != "register" or not confirmation.governor_id:
        return AccountMutationResult(ok=False, message="Invalid registration confirmation.")
    ok, err = await asyncio.to_thread(
        writer,
        int(discord_user_id),
        discord_name,
        confirmation.account_type,
        confirmation.governor_id,
        confirmation.governor_name or "Unknown",
        created_by=int(discord_user_id),
        provenance="bot_command",
    )
    if ok:
        logger.info(
            "player_self_service_account_registered user_id=%s slot=%s governor_id=%s",
            discord_user_id,
            confirmation.account_type,
            confirmation.governor_id,
        )
        return AccountMutationResult(
            ok=True,
            message=(
                f"Registered {confirmation.account_type} as "
                f"{_format_governor(confirmation.governor_name, confirmation.governor_id)}."
            ),
        )
    return AccountMutationResult(ok=False, message=err or "Registration failed.")


async def confirm_replace(
    discord_user_id: int,
    discord_name: str,
    confirmation: AccountConfirmation,
    *,
    account_loader: AccountLoader = get_account_summary_for_user,
    writer: ModifyWriter = registry_service.modify_governor,
) -> AccountMutationResult:
    if (
        confirmation.action != "replace"
        or not confirmation.governor_id
        or not confirmation.current_governor_id
    ):
        return AccountMutationResult(ok=False, message="Invalid replacement confirmation.")
    summary = await account_loader(int(discord_user_id))
    if not summary.ok:
        return AccountMutationResult(
            ok=False,
            message="Account data is temporarily unavailable. Please try again in a moment.",
        )
    current = summary.ordered_accounts.get(confirmation.account_type)
    if not current:
        return AccountMutationResult(
            ok=False,
            message=f"`{confirmation.account_type}` is no longer registered.",
        )
    current_gid = str(current.get("GovernorID") or current.get("GovernorId") or "").strip()
    if current_gid != str(confirmation.current_governor_id or "").strip():
        return AccountMutationResult(
            ok=False,
            message="This replacement confirmation is stale. Reopen Account Centre and try again.",
        )
    ok, err = await asyncio.to_thread(
        writer,
        int(discord_user_id),
        discord_name,
        confirmation.account_type,
        confirmation.governor_id,
        confirmation.governor_name or "Unknown",
        updated_by=int(discord_user_id),
    )
    if ok:
        logger.info(
            "player_self_service_account_replaced user_id=%s slot=%s governor_id=%s",
            discord_user_id,
            confirmation.account_type,
            confirmation.governor_id,
        )
        return AccountMutationResult(
            ok=True,
            message=(
                f"Replaced {confirmation.account_type} with "
                f"{_format_governor(confirmation.governor_name, confirmation.governor_id)}."
            ),
        )
    return AccountMutationResult(ok=False, message=err or "Replacement failed.")


async def confirm_remove(
    discord_user_id: int,
    confirmation: AccountConfirmation,
    *,
    account_loader: AccountLoader = get_account_summary_for_user,
    writer: RemoveWriter = registry_service.remove_governor,
) -> AccountMutationResult:
    if confirmation.action != "remove" or not confirmation.current_governor_id:
        return AccountMutationResult(ok=False, message="Invalid removal confirmation.")
    summary = await account_loader(int(discord_user_id))
    if not summary.ok:
        return AccountMutationResult(
            ok=False,
            message="Account data is temporarily unavailable. Please try again in a moment.",
        )
    current = summary.ordered_accounts.get(confirmation.account_type)
    if not current:
        return AccountMutationResult(
            ok=False,
            message=f"`{confirmation.account_type}` is no longer registered.",
        )
    current_gid = str(current.get("GovernorID") or current.get("GovernorId") or "").strip()
    if current_gid != str(confirmation.current_governor_id or "").strip():
        return AccountMutationResult(
            ok=False,
            message="This removal confirmation is stale. Reopen Account Centre and try again.",
        )
    ok, err = await asyncio.to_thread(
        writer,
        int(discord_user_id),
        confirmation.account_type,
        removed_by=int(discord_user_id),
    )
    if ok:
        logger.info(
            "player_self_service_account_removed user_id=%s slot=%s",
            discord_user_id,
            confirmation.account_type,
        )
        return AccountMutationResult(
            ok=True,
            message=f"Removed {confirmation.account_type} from your account centre.",
        )
    return AccountMutationResult(ok=False, message=err or "Removal failed.")
