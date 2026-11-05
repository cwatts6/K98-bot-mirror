"""One transaction for signup, required audit and withdrawal award cleanup.

Event lock precedes signup and award locks. Commit acknowledgement loss stays
unknown even if a later rollback call returns. No write is automatically replayed.
Existing audit JSON holds the operation receipt; no new schema is required.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
import logging
from time import perf_counter
from uuid import uuid4

from core.operation_outcome import MutationOutcome
from file_utils import get_conn_with_retries
from mge.dal import mge_roster_dal as roster, mge_signup_dal as signup
from stats_alerts.db import run_query

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SignupMutationResult:
    outcome: MutationOutcome
    operation_id: str
    signup_id: int | None = None
    reason: str = ""


class _Rejected(Exception):
    pass


def _row(cur):
    row = cur.fetchone()
    return dict(zip((col[0] for col in cur.description), row, strict=True)) if row else None


SQL_RECEIPT = """
SELECT SignupId, GovernorId, ActionType, DetailsJson
FROM dbo.MGE_SignupAudit
WHERE EventId = ? AND ActorDiscordId = ?
  AND JSON_VALUE(DetailsJson, '$.operation_id') = ?;
"""


def read_operation_receipt(*, event_id, actor_discord_id, operation_id):
    """Exact positive evidence only. An absent receipt does not authorize retry."""
    return run_query(SQL_RECEIPT, (event_id, actor_discord_id, operation_id))


def mutate_signup(
    *,
    action,
    event_id,
    governor_id,
    actor_discord_id,
    is_admin,
    values=None,
    signup_id=None,
    expected_signup=None,
    operation_id=None,
    now_utc=None,
    validate_event,
):
    operation_id = str(operation_id or uuid4())
    if len(operation_id) > 100 or action not in {"create", "edit", "withdraw"}:
        return SignupMutationResult(
            MutationOutcome.NOT_ENTERED, operation_id[:100], reason="Invalid operation."
        )
    values = dict(values or {})
    fingerprint = hashlib.sha256(
        json.dumps(
            {
                "action": action,
                "event": event_id,
                "governor": governor_id,
                "signup": signup_id,
                "values": values,
                "expected": expected_signup,
            },
            sort_keys=True,
            default=str,
        ).encode()
    ).hexdigest()
    conn = cur = None
    commit_entered = False
    outcome = MutationOutcome.NOT_ENTERED
    reason = ""
    started = perf_counter()
    try:
        conn = get_conn_with_retries()
        if conn.autocommit:
            raise _Rejected("Signup writer requires a transaction.")
        cur = conn.cursor()
        cur.execute(
            """
            SELECT e.EventId, e.EventMode, e.Status, e.SignupCloseUtc, v.VariantName
            FROM dbo.MGE_Events e WITH (UPDLOCK, HOLDLOCK)
            JOIN dbo.MGE_Variants v ON e.VariantId = v.VariantId
            WHERE e.EventId = ?;
        """,
            (event_id,),
        )
        event = _row(cur)
        if not event:
            raise _Rejected("Event not found.")
        cur.execute(SQL_RECEIPT, (event_id, actor_discord_id, operation_id))
        receipt = _row(cur)
        if receipt:
            if json.loads(receipt["DetailsJson"]).get("fingerprint") != fingerprint:
                raise _Rejected("Operation identity does not match this request.")
            signup_id = int(receipt["SignupId"])
            conn.rollback()  # read-only reconciliation; release event ownership
            outcome = MutationOutcome.COMMITTED
            return SignupMutationResult(outcome, operation_id, signup_id, "reconciled")
        now = now_utc or datetime.now(UTC)
        rejection = validate_event(event, now)
        if rejection:
            raise _Rejected(rejection)
        before = None
        if action != "create":
            cur.execute(
                signup.SQL_SELECT_SIGNUP_BY_ID.replace(
                    "FROM dbo.MGE_Signups", "FROM dbo.MGE_Signups WITH (UPDLOCK, HOLDLOCK)"
                ),
                (signup_id,),
            )
            before = _row(cur)
            if (
                not before
                or int(before["EventId"]) != event_id
                or int(before["GovernorId"]) != governor_id
                or not before["IsActive"]
            ):
                raise _Rejected(
                    "Signup has changed or is no longer active. Refresh before trying again."
                )
            if expected_signup is not None and any(
                before.get(k) != v for k, v in expected_signup.items()
            ):
                raise _Rejected("Signup changed after this form opened. Refresh before editing.")
        source = "admin" if is_admin else "discord"
        if action == "create":
            signup_id = signup.insert_signup(
                cursor=cur,
                event_id=event_id,
                governor_id=governor_id,
                source=source,
                now_utc=now,
                **values,
            )
            if signup_id is None:
                raise _Rejected("Signup could not be created.")
        elif action == "edit":
            if not signup.update_signup(cursor=cur, signup_id=signup_id, now_utc=now, **values):
                raise _Rejected("Signup could not be updated.")
        else:
            if not signup.withdraw_signup(cursor=cur, signup_id=signup_id, now_utc=now):
                raise _Rejected("Signup could not be withdrawn.")
            roster.delete_award_by_event_governor_with_audit_atomic(
                cursor=cur,
                event_id=event_id,
                governor_id=governor_id,
                actor_discord_id=actor_discord_id,
                action_type="withdraw_cleanup",
                details={
                    "signup_id": signup_id,
                    "source": "signup_withdraw",
                    "operation_id": operation_id,
                },
                now_utc=now,
            )
        action_type = (
            {"create": "admin_add", "edit": "admin_edit", "withdraw": "admin_remove"}[action]
            if is_admin
            else action
        )
        if not signup.insert_signup_audit(
            cursor=cur,
            signup_id=signup_id,
            event_id=event_id,
            governor_id=governor_id,
            action_type=action_type,
            actor_discord_id=actor_discord_id,
            details={
                "source": source,
                "operation_id": operation_id,
                "fingerprint": fingerprint,
                "before": before,
            },
            now_utc=now,
        ):
            raise RuntimeError("Required audit was not written")
        commit_entered = True
        conn.commit()
        outcome = MutationOutcome.COMMITTED
    except Exception as exc:
        outcome = MutationOutcome.UNKNOWN if commit_entered else MutationOutcome.NOT_ENTERED
        if conn is not None:
            try:
                conn.rollback()
                if not commit_entered:
                    outcome = MutationOutcome.ROLLED_BACK
            except Exception:
                outcome = MutationOutcome.UNKNOWN
        reason = str(exc) if isinstance(exc, _Rejected) else ""
        logger.warning(
            "mge_mutation_exception action=%s operation_id=%s outcome=%s error_type=%s",
            action,
            operation_id,
            outcome,
            type(exc).__name__,
        )
    finally:
        for resource in (cur, conn):
            if resource is not None:
                try:
                    resource.close()
                except Exception as exc:
                    logger.warning("mge_mutation_close_failed error_type=%s", type(exc).__name__)
        logger.info(
            "mge_mutation action=%s event_id=%s operation_id=%s outcome=%s elapsed_ms=%.3f",
            action,
            event_id,
            operation_id,
            outcome,
            (perf_counter() - started) * 1000,
        )
    return SignupMutationResult(outcome, operation_id, signup_id, reason)
