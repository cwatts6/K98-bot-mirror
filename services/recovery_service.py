"""Evidence-bound recovery orchestration. No Discord objects or SQL here."""

from dataclasses import dataclass
import logging

from kvk.dal.new_source_import_dal import SourceConflict

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RecoveryActor:
    user_id: int
    guild_id: int
    channel_id: int


class RecoveryService:
    def __init__(self, store, adapters, *, admin_id, guild_id, channel_id):
        self.store, self.adapters = store, adapters
        self.admin_id, self.guild_id, self.channel_id = map(int, (admin_id, guild_id, channel_id))

    def authorize(self, actor):
        if (actor.user_id, actor.guild_id, actor.channel_id) != (
            self.admin_id,
            self.guild_id,
            self.channel_id,
        ):
            raise SourceConflict(
                "Recovery is available only to the configured admin in the admin notification channel."
            )

    def refresh(self, incident_id):
        row = self.store.get(incident_id)
        adapter = self.adapters[row["SourceKind"]]
        for action in self.store.pending_actions(incident_id):
            outcome = adapter.reconcile(row["SourceID"], action)
            if outcome:
                self.store.finish(
                    incident_id, action["ActionID"], outcome, {"verification": outcome}
                )
        evidence, token, resolved = adapter.inspect(row["SourceID"])
        return self.store.observe(
            row["SourceKind"], row["SourceID"], evidence, token, resolved=resolved
        )

    def review(self, actor, incident_id):
        self.authorize(actor)
        return self.refresh(incident_id)

    def list_open(self, actor, after=None):
        self.authorize(actor)
        return self.store.list_open(after=after)

    def review_source(self, actor, kind, source_id):
        self.authorize(actor)
        evidence, token, resolved = self.adapters[kind].inspect(source_id)
        row = self.store.observe(kind, source_id, evidence, token, resolved=resolved)
        return self.refresh(row["IncidentID"])

    def execute(self, actor, incident_id, revision, token, action, reason):
        self.authorize(actor)
        row = self.refresh(incident_id)
        if row["State"] == "resolved":
            return row
        if (row["Revision"], row["EvidenceHash"]) != (revision, token):
            raise SourceConflict(
                "The evidence changed. Reopen this incident to review the current recovery choices."
            )
        adapter = self.adapters[row["SourceKind"]]
        if action not in row["evidence"]["actions"]:
            raise SourceConflict("This action is not permitted by the current evidence.")
        action_id, acquired = self.store.claim(
            incident_id, revision, token, action, f"discord:{actor.user_id}", reason
        )
        if not acquired:
            # No redispatch, even if another process died between intent and call.
            return self.refresh(incident_id)
        try:
            adapter.execute(row["SourceID"], action, token, f"recovery:{action_id}", reason)
        except Exception as exc:
            logger.warning(
                "recovery_action_uncertain incident=%s action=%s error_type=%s",
                incident_id,
                action_id,
                type(exc).__name__,
            )
            self.store.finish(incident_id, action_id, "unknown", {"error_type": type(exc).__name__})
        return self.refresh(incident_id)
