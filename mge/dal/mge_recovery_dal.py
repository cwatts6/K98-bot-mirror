"""Finite keyset inventory of persisted MGE presentation identities."""

from mge.dal.qualified_read import qualified_read

FIELDS = (
    "EventId",
    "Status",
    "SignupEmbedChannelId",
    "SignupEmbedMessageId",
    "LeadershipEmbedChannelId",
    "LeadershipEmbedMessageId",
    "AwardEmbedChannelId",
    "AwardEmbedMessageId",
)


def recovery_high_water():
    rows = qualified_read(
        "SELECT COALESCE(MAX(EventId), 0) AS HighWater FROM dbo.MGE_Events;",
        (),
        columns=("HighWater",),
        stage="recovery_high_water",
    )
    return int(rows[0]["HighWater"])


def recovery_page(after, high_water, *, include_completed, size=50):
    if not 1 <= size <= 50:
        raise ValueError("Invalid MGE recovery page size")
    return qualified_read(
        "SELECT TOP (?) " + ", ".join(FIELDS) + " FROM dbo.MGE_Events "
        "WHERE EventId > ? AND EventId <= ? AND (? = 1 OR Status <> 'completed') "
        "AND (SignupEmbedMessageId IS NOT NULL OR LeadershipEmbedMessageId IS NOT NULL "
        "OR AwardEmbedMessageId IS NOT NULL) ORDER BY EventId;",
        (size, after, high_water, int(include_completed)),
        columns=FIELDS,
        stage="recovery_page",
    )
