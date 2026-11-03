"""Version-qualified final edits; never creates or replaces Discord identities."""

from mge.dal.qualified_read import qualified_read
from stats_alerts.db import exec_with_cursor

FIELDS = (
    "EventId",
    "BoardKind",
    "FinalisationId",
    "PublishVersion",
    "ChannelId",
    "MessageId",
    "DeliveryState",
    "PayloadJson",
    "Reason",
    "Revision",
)


def targets(event_id):
    return qualified_read(
        "SELECT " + ", ".join(FIELDS) + " FROM dbo.MGE_BoardFinalisation WHERE EventId = ?;",
        (event_id,),
        columns=FIELDS,
        stage="finalisation_targets",
    )


def pending_events(after=0, size=50):
    if not 1 <= size <= 50:
        raise ValueError("Invalid finalisation page size")
    return qualified_read(
        "SELECT DISTINCT TOP (?) EventId FROM dbo.MGE_BoardFinalisation "
        "WHERE EventId > ? AND DeliveryState IN ('pending', 'failed', 'unknown') ORDER BY EventId;",
        (size, after),
        columns=("EventId",),
        stage="finalisation_inventory",
    )


def transition(target, state, *, payload=None, reason=None, actor_id=None):
    if state not in {"pending", "confirmed", "failed", "unknown", "held", "retired"}:
        raise ValueError("Invalid finalisation state")
    if state == "retired" and (not isinstance(actor_id, int) or actor_id <= 0):
        raise ValueError("Retirement requires an actor")

    def write(cur):
        cur.execute(
            "UPDATE F SET DeliveryState = ?, PayloadJson = COALESCE(PayloadJson, ?), "
            "Reason = ?, RetiredByDiscordId = ?, UpdatedUtc = SYSUTCDATETIME() "
            "FROM dbo.MGE_BoardFinalisation F JOIN dbo.MGE_Events E ON E.EventId = F.EventId "
            "WHERE F.EventId = ? AND BoardKind = ? AND FinalisationId = ? AND Revision = ? "
            "AND F.ChannelId = ? AND F.MessageId = ? AND F.PublishVersion = ? "
            "AND E.Status = 'completed' AND E.PublishVersion = F.PublishVersion "
            "AND F.DeliveryState NOT IN ('confirmed', 'retired');",
            (
                state,
                payload,
                reason,
                actor_id,
                target["EventId"],
                target["BoardKind"],
                target["FinalisationId"],
                target["Revision"],
                target["ChannelId"],
                target["MessageId"],
                target["PublishVersion"],
            ),
        )
        return cur.rowcount == 1

    return exec_with_cursor(write) is True


def counts():
    return qualified_read(
        "SELECT DeliveryState, COUNT_BIG(*) AS TargetCount FROM dbo.MGE_BoardFinalisation GROUP BY DeliveryState;",
        (),
        columns=("DeliveryState", "TargetCount"),
        stage="finalisation_counts",
    )


def event_counts():
    return qualified_read(
        "SELECT SUM(CASE WHEN Status <> 'completed' THEN CAST(1 AS bigint) ELSE 0 END) AS ActiveEvents, "
        "SUM(CASE WHEN Status = 'completed' THEN CAST(1 AS bigint) ELSE 0 END) AS FrozenEvents "
        "FROM dbo.MGE_Events;",
        (),
        columns=("ActiveEvents", "FrozenEvents"),
        stage="finalisation_event_counts",
    )
