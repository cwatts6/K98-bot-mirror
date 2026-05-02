# subscription_tracker.py
from __future__ import annotations

from datetime import UTC, datetime
import json
import logging

logger = logging.getLogger(__name__)

import os

from constants import DEFAULT_REMINDER_TIMES, SUBSCRIPTION_FILE, VALID_TYPES

# In-memory cache (lazy-loaded)
subscriptions: dict[str, dict] | None = None


def _ensure_loaded() -> None:
    """Lazy-load the in-memory cache if needed."""
    global subscriptions
    if subscriptions is None:
        load_subscriptions()


def load_subscriptions() -> None:
    """Load from disk into memory (best effort, schema-normalized)."""
    global subscriptions
    try:
        if os.path.exists(SUBSCRIPTION_FILE):
            with open(SUBSCRIPTION_FILE, encoding="utf-8") as f:
                data = json.load(f) or {}
            if not isinstance(data, dict):
                logger.warning(
                    "[SUBSCRIPTIONS] Invalid file schema; resetting to empty dict: %s",
                    SUBSCRIPTION_FILE,
                )
                data = {}
            # Normalize entries
            norm: dict[str, dict] = {}
            for uid, cfg in data.items():
                if not isinstance(cfg, dict):
                    continue
                username = str(cfg.get("username", "Unknown"))
                types = cfg.get("subscriptions", [])
                times = cfg.get("reminder_times", [])
                # Defensive filtering
                if not isinstance(types, list):
                    types = []
                if not isinstance(times, list):
                    times = []
                types = sorted(
                    {t for t in (str(x).lower().strip() for x in types) if t in VALID_TYPES}
                )
                times = sorted(
                    {
                        t
                        for t in (str(x).lower().strip() for x in times)
                        if t in DEFAULT_REMINDER_TIMES
                    }
                )
                norm[str(uid)] = {
                    "username": username,
                    "subscriptions": types,
                    "reminder_times": times,
                }
            subscriptions = norm
            logger.info(
                "[SUBSCRIPTIONS] Loaded subscription file (%d user(s)): %s",
                len(subscriptions),
                SUBSCRIPTION_FILE,
            )
        else:
            subscriptions = {}
    except Exception as e:
        logger.error("[SUBSCRIPTIONS] Failed to load %s: %s", SUBSCRIPTION_FILE, e)
        subscriptions = {}


def save_subscriptions() -> None:
    """Atomic save to disk."""
    _ensure_loaded()
    tmp = SUBSCRIPTION_FILE + ".tmp"
    try:
        assert isinstance(subscriptions, dict)
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(subscriptions, f, indent=2, sort_keys=True)
        os.replace(tmp, SUBSCRIPTION_FILE)
        logger.info(
            "[SUBSCRIPTIONS] Saved subscription file (%d user(s)): %s",
            len(subscriptions),
            SUBSCRIPTION_FILE,
        )
    except Exception as e:
        logger.error("[SUBSCRIPTIONS] Failed to save %s: %s", SUBSCRIPTION_FILE, e)
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass


def get_user_config(user_id: int | str) -> dict | None:
    """Return a user's config or None."""
    _ensure_loaded()
    return subscriptions.get(str(user_id))  # type: ignore[union-attr]


def _validated_types(types: list[str] | None) -> list[str]:
    if not types:
        return []
    return sorted({t for t in (str(x).lower().strip() for x in types) if t in VALID_TYPES})


def _validated_times(times: list[str] | None) -> list[str]:
    if not times:
        return []
    return sorted(
        {t for t in (str(x).lower().strip() for x in times) if t in DEFAULT_REMINDER_TIMES}
    )


def set_user_config(
    user_id: int | str,
    username: str,
    event_types: list[str] | None = None,
    reminder_times: list[str] | None = None,
) -> None:
    """
    Create/update a user's config. If a list is None, that field is left unchanged (or initialized).
    Empty lists are allowed and will be stored as empty (caller controls defaults).
    """
    _ensure_loaded()
    uid = str(user_id)

    # Initialize record
    cfg = subscriptions.get(uid, {"username": str(username), "subscriptions": [], "reminder_times": []})  # type: ignore[union-attr]
    cfg["username"] = str(username)

    if event_types is not None:
        cfg["subscriptions"] = _validated_types(event_types)

    if reminder_times is not None:
        cfg["reminder_times"] = _validated_times(reminder_times)

    subscriptions[uid] = cfg  # type: ignore[union-attr]
    save_subscriptions()


def remove_user(user_id: int | str) -> bool:
    """Delete a user's subscription record."""
    _ensure_loaded()
    uid = str(user_id)
    if uid in subscriptions:  # type: ignore[union-attr]
        subscriptions.pop(uid)  # type: ignore[union-attr]
        save_subscriptions()
        return True
    return False


def update_user_reminder_times(user_id: int | str, times: list[str]) -> bool:
    _ensure_loaded()
    uid = str(user_id)
    if uid in subscriptions:  # type: ignore[union-attr]
        subscriptions[uid]["reminder_times"] = _validated_times(times)  # type: ignore[union-attr]
        save_subscriptions()
        return True
    return False


def update_user_event_types(user_id: int | str, event_types: list[str]) -> bool:
    _ensure_loaded()
    uid = str(user_id)
    if uid in subscriptions:  # type: ignore[union-attr]
        subscriptions[uid]["subscriptions"] = _validated_types(event_types)  # type: ignore[union-attr]
        save_subscriptions()
        return True
    return False


def get_all_subscribers() -> dict[str, dict]:
    """Return the in-memory dict (ensuring it’s loaded)."""
    _ensure_loaded()
    return subscriptions  # type: ignore[return-value]


# --- Migration utilities -------------------------------------------------------
# Canonical maps (expand as you discover legacy variants)
_TYPE_ALIASES = {
    "ruin": "ruins",
    "ruins": "ruins",
    "next ruins": "ruins",
    "altar": "altars",
    "altars": "altars",
    "next altar": "altars",
    "next altar fight": "altars",
    "fight": "fights",
    "fights": "fights",
    "major": "major",
    "major fight": "major",
    "timeline": "major",
    "all": "all",
}

_TIME_ALIASES = {
    "24h": "24h",
    "24hr": "24h",
    "24hrs": "24h",
    "12h": "12h",
    "12hr": "12h",
    "12hrs": "12h",
    "4h": "4h",
    "4hr": "4h",
    "4hrs": "4h",
    "1h": "1h",
    "1hr": "1h",
    "60m": "1h",
    "now": "now",
    "0": "now",
    "0m": "now",
    "0min": "now",
    "t0": "now",
}

# Any keys in a user record that we do NOT keep
_LEGACY_DROP_KEYS = {
    "events",
    "times",
    "notify",
    "enabled",
    "preferences",
    "created_at",
    "updated_at",
    "guild_id",
    "notes",
}


def _canon_types(types):
    out = []
    for t in types or []:
        key = str(t).strip().lower()
        can = _TYPE_ALIASES.get(key)
        if can and can in VALID_TYPES:
            out.append(can)
    # exclusivity: 'all' wins; 'fights' supersedes altars/major to avoid dupes
    out = sorted(set(out))
    if "all" in out:
        return ["all"]
    if "fights" in out:
        out = [x for x in out if x not in ("altars", "major")] + ["fights"]
    return sorted(set(out))


def _canon_times(times):
    out = []
    for t in times or []:
        key = str(t).strip().lower()
        can = _TIME_ALIASES.get(key)
        if can and can in DEFAULT_REMINDER_TIMES:
            out.append(can)
    return sorted(set(out))


def migrate_subscriptions(
    *, dry_run: bool = True, keep_empty: bool = False
) -> tuple[int, int, str]:
    """
    Migrate/clean SUBSCRIPTION_FILE and in-memory cache.
    - dry_run: when True, only returns a report; no file writes.
    - keep_empty: when False, drop users with no types AND no times.

    Returns: (users_before, users_after, report_text)
    """
    _ensure_loaded()
    global subscriptions
    before_count = len(subscriptions)

    report_lines = []
    fixed: dict[str, dict] = {}

    for raw_uid, cfg in subscriptions.items():
        changes = []
        # normalize uid → string of digits when possible
        uid = str(raw_uid).strip()
        if not uid.isdigit():
            # attempt to strip non-digits (e.g., accidental usernames)
            digits = "".join(ch for ch in uid if ch.isdigit())
            if digits:
                changes.append(f"uid:{uid}→{digits}")
                uid = digits
            else:
                report_lines.append(f"DROP user with invalid uid: {raw_uid!r}")
                continue

        # normalize record
        if not isinstance(cfg, dict):
            report_lines.append(f"DROP user {uid}: invalid cfg type {type(cfg).__name__}")
            continue

        username = str(cfg.get("username", "Unknown"))
        types = cfg.get("subscriptions", [])
        times = cfg.get("reminder_times", [])

        if not isinstance(types, list):
            changes.append("subscriptions:nonlist→list")
            types = []
        if not isinstance(times, list):
            changes.append("reminder_times:nonlist→list")
            times = []

        new_types = _canon_types(types)
        new_times = _canon_times(times)

        if new_types != types:
            changes.append(f"types:{types}→{new_types}")
        if new_times != times:
            changes.append(f"times:{times}→{new_times}")

        # drop legacy keys and unknown keys
        cleaned = {
            "username": username,
            "subscriptions": new_types,
            "reminder_times": new_times,
        }
        legacy_keys = [k for k in cfg.keys() if k not in cleaned and k in _LEGACY_DROP_KEYS]
        if legacy_keys:
            changes.append(f"drop_keys:{legacy_keys}")

        if not keep_empty and not new_types and not new_times:
            report_lines.append(f"DROP user {uid}: empty selections")
            continue

        fixed[uid] = cleaned
        if changes:
            report_lines.append(f"FIX {uid} ({username}): " + "; ".join(changes))

    after_count = len(fixed)

    if not dry_run:
        # backup
        try:
            # use timezone-aware UTC per project standard
            ts = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
            backup_path = f"{SUBSCRIPTION_FILE}.bak-{ts}.json"
            with open(backup_path, "w", encoding="utf-8") as f:
                json.dump(subscriptions, f, indent=2, sort_keys=True)
            logger.info("[SUBSCRIPTIONS] Backup written to %s", backup_path)
        except Exception as e:
            logger.warning("[SUBSCRIPTIONS] Backup failed for %s: %s", SUBSCRIPTION_FILE, e)

        # write & refresh in-memory
        subscriptions = fixed
        save_subscriptions()
        _ensure_loaded()

    summary = (
        f"MIGRATION {'(dry-run)' if dry_run else '(applied)'} — "
        f"users: {before_count} → {after_count}\n"
        + "\n".join(report_lines or ["No changes required."])
    )
    logger.info(summary)
    return before_count, after_count, summary
