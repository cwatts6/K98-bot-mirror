"""Qualified MGE presentation inputs; no Discord IO or business mutations."""

from datetime import datetime

from mge.dal import mge_event_dal
from mge.dataset_errors import MgeDatasetError

EVENT_STATUSES = {"created", "signup_open", "signup_closed", "published", "completed", "reopened"}
AWARD_STATUSES = {"pending", "awarded", "waitlist", "rejected", "removed"}
BOARD_FIELDS = {
    "signup": ("SignupEmbedChannelId", "SignupEmbedMessageId"),
    "leadership": ("LeadershipEmbedChannelId", "LeadershipEmbedMessageId"),
    "awards": ("AwardEmbedChannelId", "AwardEmbedMessageId"),
}


def _integer(value, minimum=1):
    return isinstance(value, int) and not isinstance(value, bool) and value >= minimum


def validate_event(row, event_id, *, publication=False):
    if not isinstance(row, dict) or row.get("EventId") != event_id or not _integer(event_id):
        raise MgeDatasetError("incomplete", "event_identity")
    if row.get("Status") not in EVENT_STATUSES or row.get("RuleMode") not in {"open", "fixed"}:
        raise MgeDatasetError("incomplete", "event_lifecycle")
    if not _integer(row.get("PublishVersion"), 0):
        raise MgeDatasetError("incomplete", "publication_version")
    for field in ("EventName", "VariantName"):
        if not isinstance(row.get(field), str) or not row[field].strip():
            raise MgeDatasetError("incomplete", "event_payload")
    if not publication:
        if row.get("EventMode") not in {"controlled", "open"}:
            raise MgeDatasetError("incomplete", "event_mode")
        if any(
            not isinstance(row.get(field), datetime)
            for field in ("StartUtc", "EndUtc", "SignupCloseUtc")
        ):
            raise MgeDatasetError("incomplete", "event_dates")
    for kind, (channel, message) in BOARD_FIELDS.items():
        if publication and kind != "awards":
            continue
        # SQL NULL is the sole absent identity. A partial pair is not permission to send.
        values = row.get(channel), row.get(message)
        if values != (None, None) and not all(_integer(value) for value in values):
            raise MgeDatasetError("incomplete", "board_identity")
    return row


def validate_rows(rows, event_id, *, awards=False):
    seen = {
        field: set()
        for field in (
            ("AwardId", "SignupId", "GovernorId") if awards else ("SignupId", "GovernorId")
        )
    }
    for row in rows:
        if row.get("EventId") != event_id:
            raise MgeDatasetError("incomplete", "row_event_identity")
        for field, identities in seen.items():
            value = row.get(field)
            if not _integer(value) or value in identities:
                raise MgeDatasetError("incomplete", "row_identity")
            identities.add(value)
        if awards:
            if row.get("AwardStatus") not in AWARD_STATUSES:
                raise MgeDatasetError("incomplete", "award_status")
            for field in ("AwardedRank", "WaitlistOrder", "TargetScore"):
                value = row.get(field)
                if value is not None and not _integer(value, 0 if field == "TargetScore" else 1):
                    raise MgeDatasetError("incomplete", "award_values")
    return rows


def validate_join(review_rows, award_rows, event_id):
    validate_rows(review_rows, event_id)
    validate_rows(award_rows, event_id, awards=True)
    review_by_id = {row["SignupId"]: row for row in review_rows}
    for row in award_rows:
        review = review_by_id.get(row["SignupId"])
        if review is not None and review["GovernorId"] != row["GovernorId"]:
            raise MgeDatasetError("incomplete", "join_identity")


def public_names(event_id, *, simplified):
    if simplified:
        from mge.mge_simplified_flow_service import get_public_signup_rows

        rows = get_public_signup_rows(event_id, strict=True)
    else:
        rows = mge_event_dal.fetch_public_signup_rows(event_id)
        validate_rows(rows, event_id)
    if any(not isinstance(row.get("GovernorNameSnapshot"), str) for row in rows):
        raise MgeDatasetError("incomplete", "signup_name")
    return [row["GovernorNameSnapshot"] or "Unknown" for row in rows]


def validate_destination(row, kind, channel_id):
    saved_channel, _ = BOARD_FIELDS[kind]
    if row.get(saved_channel) is not None and row[saved_channel] != channel_id:
        raise MgeDatasetError("incomplete", "destination_conflict")


def validate_payload(payload, *, has_view=False, view_required=False):
    """Validate plain rendered data; the Discord adapter owns Embed/View objects."""
    if view_required and not has_view:
        raise MgeDatasetError("incomplete", "view_construction")
    fields = payload.get("fields", [])
    text_parts = [
        payload.get("title", ""),
        payload.get("description", ""),
        payload.get("footer", {}).get("text", ""),
        payload.get("author", {}).get("name", ""),
    ]
    limits = (256, 4096, 2048, 256)
    if any(len(value) > limit for value, limit in zip(text_parts, limits, strict=True)):
        raise MgeDatasetError("incomplete", "payload_text")
    if len(fields) > 25:
        raise MgeDatasetError("incomplete", "payload_size")
    if any(
        len(field.get("name", "")) > 256 or len(field.get("value", "")) > 1024 for field in fields
    ):
        raise MgeDatasetError("incomplete", "payload_fields")
    if (
        sum(map(len, text_parts))
        + sum(len(field.get("name", "")) + len(field.get("value", "")) for field in fields)
        > 6000
    ):
        raise MgeDatasetError("incomplete", "payload_size")
