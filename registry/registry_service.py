# registry_service.py
"""
Service layer for the governor registry.

Responsibilities:
  - Input validation (GovernorID format, AccountType validity)
  - Ownership and duplicate rules
  - Orchestrating DAL calls for composite operations (e.g. modify = delete + insert)
  - Shaping DAL rows into formats expected by commands, views, and import/export
  - load_registry_as_dict() — backward-compat dict for registry_io audit/export

Not responsible for:
  - SQL (→ registry_dal.py)
  - Discord command handling (→ commands/registry_cmds.py)
  - Import/export file I/O (→ registry_io.py)
"""

from __future__ import annotations

import logging
from typing import Any

from registry.dal import registry_dal

logger = logging.getLogger(__name__)

# Result code constants — match stored procedure contracts
RC_OK = 0
RC_DUPE_SLOT = 1
RC_DUPE_GOV = 2
RC_NOT_FOUND = 3
RC_SKIPPED = 4
RC_OVERWRITTEN = 5
RC_ERROR = 9


VALID_ACCOUNT_TYPES: frozenset[str] = frozenset(
    {
        "Main",
        *[f"Alt {i}" for i in range(1, 6)],
        *[f"Farm {i}" for i in range(1, 21)],
    }
)


# ---------------------------------------------------------------------------
# Write operations
# ---------------------------------------------------------------------------


def register_governor(
    discord_user_id: int,
    discord_name: str,
    account_type: str,
    governor_id: str | int,
    governor_name: str,
    *,
    created_by: int | None = None,
    provenance: str = "bot_command",
) -> tuple[bool, str | None]:
    try:
        gid = int(str(governor_id).strip())
    except (ValueError, TypeError):
        return False, f"Invalid Governor ID: {governor_id!r}"

    if account_type not in VALID_ACCOUNT_TYPES:
        return False, f"Invalid account type: {account_type!r}"

    code, msg = registry_dal.insert(
        discord_user_id=int(discord_user_id),
        discord_name=(str(discord_name) or None),
        governor_id=gid,
        governor_name=(str(governor_name) or None),
        account_type=account_type,
        created_by=created_by,
        provenance=provenance,
    )

    if code == RC_OK:
        logger.info(
            "[REGISTRY] registered GovernorID=%s (%s) as %s for DiscordUserID=%s provenance=%s actor=%s",
            gid,
            governor_name,
            account_type,
            discord_user_id,
            provenance,
            created_by or "self",
        )
        return True, None

    if code == RC_DUPE_SLOT:
        return False, (
            f"You already have an active registration in slot `{account_type}`. "
            "Use `/modify_registration` to change it."
        )

    if code == RC_DUPE_GOV:
        return False, "This Governor ID is already registered to another Discord user."

    logger.error("[REGISTRY] insert failed code=%s msg=%s", code, msg)
    return False, f"Registration failed: {msg}"


def modify_governor(
    discord_user_id: int,
    discord_name: str,
    account_type: str,
    new_governor_id: str | int,
    new_governor_name: str,
    *,
    updated_by: int | None = None,
) -> tuple[bool, str | None]:
    """
    Replace the governor in an existing active slot.

    Soft-deletes the current active row (status → Superseded), then inserts
    the replacement.  If the insert fails after the delete, both outcomes are
    logged clearly so an admin can manually correct.

    Returns (success, error_message_or_None).
    """
    try:
        new_gid = int(str(new_governor_id).strip())
    except (ValueError, TypeError):
        return False, f"Invalid Governor ID: {new_governor_id!r}"

    uid = int(discord_user_id)

    # Confirm the slot is currently active for this user
    rows = registry_dal.get_by_discord_id(uid)
    existing = next((r for r in rows if r.get("AccountType") == account_type), None)
    if not existing:
        return False, f"No active registration found for slot `{account_type}`."

    # Guard against cross-user GovernorID conflict before touching anything
    claimed = registry_dal.get_by_governor_id(new_gid)
    if claimed and int(claimed["DiscordUserID"]) != uid:
        return False, "This Governor ID is already registered to another Discord user."

    # Soft-delete the current slot
    del_code, del_msg = registry_dal.soft_delete(
        discord_user_id=uid,
        account_type=account_type,
        updated_by=updated_by,
        new_status="Superseded",
    )
    if del_code != RC_OK:
        logger.error(
            "[REGISTRY] modify soft_delete failed DiscordUserID=%s slot=%s code=%s msg=%s",
            uid,
            account_type,
            del_code,
            del_msg,
        )
        return False, f"Failed to update registration: {del_msg}"

    # Insert replacement
    ins_code, ins_msg = registry_dal.insert(
        discord_user_id=uid,
        discord_name=(str(discord_name) or None),
        governor_id=new_gid,
        governor_name=(str(new_governor_name) or None),
        account_type=account_type,
        created_by=updated_by,
        provenance="bot_command",
    )

    if ins_code == RC_OK:
        logger.info(
            "[REGISTRY] modified slot %s for DiscordUserID=%s → GovernorID=%s (%s) actor=%s",
            account_type,
            uid,
            new_gid,
            new_governor_name,
            updated_by or "self",
        )
        return True, None

    # Partial failure: old row superseded but new row not created.
    # Log at ERROR level so an admin can detect and correct via /admin_register_governor.
    logger.error(
        "[REGISTRY] PARTIAL FAILURE — slot %s for DiscordUserID=%s was superseded "
        "but replacement insert FAILED. GovernorID=%s code=%s msg=%s — "
        "manual correction required via /admin_register_governor.",
        account_type,
        uid,
        new_gid,
        ins_code,
        ins_msg,
    )
    return False, (
        f"Partial failure: old registration removed but new one could not be saved: {ins_msg}. "
        "Please contact an admin."
    )


def remove_governor(
    discord_user_id: int,
    account_type: str,
    *,
    removed_by: int | None = None,
) -> tuple[bool, str | None]:
    """
    Remove (soft-delete) a governor account slot.

    Returns (success, error_message_or_None).
    """
    code, msg = registry_dal.soft_delete(
        discord_user_id=int(discord_user_id),
        account_type=account_type,
        updated_by=removed_by,
        new_status="Removed",
    )

    if code == RC_OK:
        logger.info(
            "[REGISTRY] removed slot %s for DiscordUserID=%s actor=%s",
            account_type,
            discord_user_id,
            removed_by or "self",
        )
        return True, None

    if code == RC_NOT_FOUND:
        return False, f"`{account_type}` is not currently registered."

    logger.error("[REGISTRY] soft_delete failed code=%s msg=%s", code, msg)
    return False, f"Failed to remove registration: {msg}"


def admin_register_or_replace(
    target_discord_user_id: int,
    target_discord_name: str,
    account_type: str,
    governor_id: str | int,
    governor_name: str,
    *,
    admin_discord_id: int,
) -> tuple[bool, str | None]:
    """
    Admin upsert: register a governor slot for any user, overwriting the
    existing slot if one is already active (Supersede + Insert).

    Differs from register_governor() in that:
      - It targets a user other than the actor.
      - It always overwrites an existing slot rather than rejecting with RC_DUPE_SLOT.
      - Provenance is always 'admin_command'.
      - actor = admin_discord_id recorded on both the superseded and new rows.

    Returns (success, error_message_or_None).
    """
    try:
        gid = int(str(governor_id).strip())
    except (ValueError, TypeError):
        return False, f"Invalid Governor ID: {governor_id!r}"

    if account_type not in VALID_ACCOUNT_TYPES:
        return False, f"Invalid account type: {account_type!r}"

    uid = int(target_discord_user_id)

    # Guard: GovernorID must not be actively claimed by a DIFFERENT user
    claimed = registry_dal.get_by_governor_id(gid)
    if claimed and int(claimed["DiscordUserID"]) != uid:
        existing_name = claimed.get("DiscordName") or f"<@{claimed['DiscordUserID']}>"
        existing_slot = claimed.get("AccountType", "?")
        return False, (
            f"GovernorID `{gid}` is already registered to "
            f"**{existing_name}** ({existing_slot})."
        )

    # Check whether the target slot is already active for this user
    rows = registry_dal.get_by_discord_id(uid)
    slot_exists = any(r.get("AccountType") == account_type for r in rows)

    if slot_exists:
        # Supersede the existing slot then insert the replacement
        del_code, del_msg = registry_dal.soft_delete(
            discord_user_id=uid,
            account_type=account_type,
            updated_by=admin_discord_id,
            new_status="Superseded",
        )
        if del_code != RC_OK:
            logger.error(
                "[REGISTRY] admin_register_or_replace soft_delete failed "
                "DiscordUserID=%s slot=%s code=%s msg=%s",
                uid,
                account_type,
                del_code,
                del_msg,
            )
            return False, f"Failed to supersede existing registration: {del_msg}"

    ins_code, ins_msg = registry_dal.insert(
        discord_user_id=uid,
        discord_name=(str(target_discord_name) or None),
        governor_id=gid,
        governor_name=(str(governor_name) or None),
        account_type=account_type,
        created_by=admin_discord_id,
        provenance="admin_command",
    )

    if ins_code == RC_OK:
        action = "replaced" if slot_exists else "registered"
        logger.info(
            "[REGISTRY] admin %s %s GovernorID=%s (%s) as %s for DiscordUserID=%s",
            admin_discord_id,
            action,
            gid,
            governor_name,
            account_type,
            uid,
        )
        return True, None

    if slot_exists:
        logger.error(
            "[REGISTRY] PARTIAL FAILURE — slot %s for DiscordUserID=%s was superseded "
            "but replacement insert FAILED. GovernorID=%s code=%s msg=%s — "
            "manual correction required.",
            account_type,
            uid,
            gid,
            ins_code,
            ins_msg,
        )
        return False, (
            f"Partial failure: old registration removed but new one could not be saved: {ins_msg}. "
            "Manual correction required."
        )

    return False, f"Registration failed: {ins_msg}"


# ---------------------------------------------------------------------------
# Read operations
# ---------------------------------------------------------------------------


def get_user_accounts(discord_user_id: int) -> dict[str, dict[str, str]]:
    """
    Return all active account slots for a Discord user.

    Raises on SQL failure — callers must handle explicitly.
    """
    rows = registry_dal.get_by_discord_id(int(discord_user_id))
    return {
        r["AccountType"]: {
            "GovernorID": str(r["GovernorID"]),
            "GovernorName": str(r.get("GovernorName") or ""),
        }
        for r in rows
    }


def get_discord_user_for_governor(governor_id: str | int) -> dict[str, Any] | None:
    """
    Return Discord user info for the active owner of a GovernorID, or None.

    Shape: {"DiscordUserID": int, "DiscordName": str | None, "AccountType": str}
    """
    try:
        gid = int(str(governor_id).strip())
    except (ValueError, TypeError):
        return None
    row = registry_dal.get_by_governor_id(gid)
    if not row:
        return None
    return {
        "DiscordUserID": int(row["DiscordUserID"]),
        "DiscordName": row.get("DiscordName"),
        "AccountType": row.get("AccountType"),
    }


def get_user_main_governor_id(discord_user_id: int) -> str | None:
    """Return the GovernorID string for the user's Main slot, or None."""
    rows = registry_dal.get_by_discord_id(int(discord_user_id))
    main = next((r for r in rows if r.get("AccountType") == "Main"), None)
    gid = (main or {}).get("GovernorID")
    return str(gid) if gid else None


def get_user_main_governor_name(discord_user_id: int) -> str | None:
    """Return the GovernorName string for the user's Main slot, or None."""
    rows = registry_dal.get_by_discord_id(int(discord_user_id))
    main = next((r for r in rows if r.get("AccountType") == "Main"), None)
    name = (main or {}).get("GovernorName")
    return str(name) if name else None


def check_governor_claimed_by_other(governor_id: str | int, owner_discord_id: int) -> bool:
    """
    Return True if governor_id is actively registered to a DIFFERENT Discord user.
    """
    try:
        gid = int(str(governor_id).strip())
    except (ValueError, TypeError):
        return False
    row = registry_dal.get_by_governor_id(gid)
    if not row:
        return False
    return int(row["DiscordUserID"]) != int(owner_discord_id)


# ---------------------------------------------------------------------------
# Backward-compat dict format
# Used by registry_io export/audit functions that accept the legacy registry dict.
# ---------------------------------------------------------------------------


def load_registry_as_dict() -> dict[str, Any]:
    """
    Return all Active registrations in the legacy dict shape:

      {
        "<discord_user_id_str>": {
          "discord_id":   "<str>",
          "discord_name": "<str>",
          "accounts": {
            "Main":  {"GovernorID": "<str>", "GovernorName": "<str>"},
            "Alt 1": {"GovernorID": "<str>", "GovernorName": "<str>"},
            ...
          }
        }
      }

    This is the SQL-backed replacement for the old governor_registry.load_registry().
    Called by governor_registry.load_registry() and registry_io audit/export paths.
    """
    rows = registry_dal.get_all_active()
    result: dict[str, Any] = {}
    for row in rows:
        uid_str = str(row["DiscordUserID"])
        if uid_str not in result:
            result[uid_str] = {
                "discord_id": uid_str,
                "discord_name": row.get("DiscordName") or uid_str,
                "accounts": {},
            }
        result[uid_str]["accounts"][row["AccountType"]] = {
            "GovernorID": str(row["GovernorID"]),
            "GovernorName": str(row.get("GovernorName") or ""),
        }
    return result
