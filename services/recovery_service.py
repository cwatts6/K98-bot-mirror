"""Evidence-bound recovery orchestration. No Discord objects or SQL here."""

from dataclasses import dataclass
import logging

from kvk.dal.new_source_import_dal import SourceConflict
from services.recovery_execution_guard import execution_progress, recovery_execution

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RecoveryActor:
    user_id: int
    guild_id: int
    channel_id: int


class RecoveryService:
    def __init__(
        self, store, adapters, *, admin_id, guild_id, channel_id, presentation_policy=None
    ):
        self.store, self.adapters = store, adapters
        self.admin_id, self.guild_id, self.channel_id = map(int, (admin_id, guild_id, channel_id))
        self.presentation_policy = presentation_policy

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
        if row["SourceKind"] not in self.adapters:
            raise SourceConflict(
                "Repair the private-evidence incident in the recovery centre first. "
                "Normal recovery checks will resume after registration verifies."
            )
        adapter = self.adapters[row["SourceKind"]]
        with recovery_execution(incident_id) as acquired:
            if acquired:
                for action in self.store.pending_actions(incident_id):
                    outcome = adapter.reconcile(row["SourceID"], action)
                    if outcome:
                        self.store.finish(
                            incident_id, action["ActionID"], outcome, {"verification": outcome}
                        )
        evidence, token, resolved = adapter.inspect(row["SourceID"])
        current = self.store.observe(
            row["SourceKind"], row["SourceID"], evidence, token, resolved=resolved
        )
        return self.present(current)

    def present(self, row):
        pending = self.store.pending_actions(row["IncidentID"])
        row["pending_action"] = (
            {"state": pending[0]["State"], "kind": pending[0]["ActionKind"]} if pending else None
        )
        row["execution_progress"] = execution_progress(row["IncidentID"]) if pending else None
        return self.presentation_policy(row) if self.presentation_policy else row

    def review(self, actor, incident_id):
        self.authorize(actor)
        return self.refresh(incident_id)

    def list_open(self, actor, after=None):
        self.authorize(actor)
        return self.store.list_open(after=after)

    def list_priority(self, actor, after=None):
        self.authorize(actor)
        return self.store.list_open(after=after, non_evidence=True)

    def centre_page(self, actor, after=None, individual=False, queues_only=False):
        self.authorize(actor)
        return dict(
            rows=self.store.list_open(
                after=after,
                non_evidence=not individual,
                **(dict(queues_only=True) if queues_only else {}),
            ),
            open_count=self.store.count_open(),
        )

    def published_outputs(self, actor, after=None):
        self.authorize(actor)
        adapter = self.adapters.get("export_job")
        if adapter is None:
            raise SourceConflict(
                "Restore the private registration evidence before checking outputs."
            )
        return adapter.published_outputs(after=after)

    def download_report(self, actor, after=None, through=None, part=1, max_bytes=8388608):
        from services.recovery_report import build_report

        return build_report(self, actor, after, through, part, max_bytes)

    def review_evidence_group(self, actor):
        from services.recovery_backlog_service import review_group

        return review_group(self, actor)

    def approve_evidence_group(self, actor, preview):
        from services.recovery_backlog_service import approve_group

        return approve_group(self, actor, preview)

    def review_historical_groups(self, actor, after=None):
        from services.historical_retirement_group_service import review_groups

        return review_groups(self, actor, after)

    def review_historical_group(self, actor, group, selected=None):
        from services.historical_retirement_group_service import review_group

        return review_group(self, actor, group, selected)

    def approve_historical_group(self, actor, group, selected):
        from services.historical_retirement_group_service import approve_group

        return approve_group(self, actor, group, selected)

    def download_complete_report(self, actor, max_bytes=8388608):
        from services.recovery_complete_report import build_complete_report

        return build_complete_report(self, actor, max_bytes)

    def backlog_summary(self, actor):
        from services.recovery_backlog_dal import RecoveryBacklogDAL

        self.authorize(actor)
        return RecoveryBacklogDAL(self.store).summary()

    def _review_action(self, actor, incident_id, action, revision, token):
        self.authorize(actor)
        row = self.refresh(incident_id)
        if (
            (row["Revision"], row["EvidenceHash"]) != (revision, token)
            or row["State"] != "open"
            or row["pending_action"]
            or row["evidence"].get("check_unavailable")
            or row["evidence"]["actions"].get(action, {}).get("review_details") is not True
        ):
            raise SourceConflict("Recovery details changed. Reopen the incident before confirming.")
        return row

    def review_decision_summary(self, actor, incident_id, action, revision, token):
        row = self._review_action(actor, incident_id, action, revision, token)
        if row["evidence"]["actions"][action].get("review_summary") is not True:
            raise SourceConflict("This repair requires its full guided checks.")
        fields = self.adapters[row["SourceKind"]].review_summary(row["SourceID"], action, token)
        return dict(row=row, action=action, fields=fields)

    def review_details_page(self, actor, incident_id, action, revision, token, page=0):
        row = self._review_action(actor, incident_id, action, revision, token)
        fields = self.adapters[row["SourceKind"]].review_details(row["SourceID"], action, token)
        pages = max(1, (len(fields) + 4) // 5)
        if type(page) is not int or not 0 <= page < pages:
            raise SourceConflict("Choose a current recovery review page.")
        return dict(
            row=row, action=action, page=page, pages=pages, fields=fields[page * 5 : (page + 1) * 5]
        )

    def review_source(self, actor, kind, source_id):
        self.authorize(actor)
        evidence, token, resolved = self.adapters[kind].inspect(source_id)
        row = self.store.observe(kind, source_id, evidence, token, resolved=resolved)
        return self.refresh(row["IncidentID"])

    def execute(self, actor, incident_id, revision, token, action, reason):
        self.authorize(actor)
        return self._execute(
            incident_id, revision, token, action, reason, f"discord:{actor.user_id}"
        )

    def recover_automatic(self, incident_id):
        """Only named evidence-bound read release and original cache-only intent."""
        row = self.refresh(incident_id)
        action = getattr(self.adapters[row["SourceKind"]], "automatic_action", None)
        if (
            (row["SourceKind"], action)
            not in {
                ("configuration_read", "release_read"),
                ("player_report", "complete_cache_only"),
                ("configuration_producer", "complete_configuration_only"),
            }
            or row["State"] == "resolved"
            or action not in row["evidence"]["actions"]
        ):
            return row
        return self._execute(
            incident_id,
            row["Revision"],
            row["EvidenceHash"],
            action,
            getattr(
                self.adapters[row["SourceKind"]],
                "automatic_reason",
                "Authority verified closed read-only execution and exact reservations",
            ),
            "system:guided_recovery",
        )

    def input_page(self, actor, incident_id, action, page=0):
        self.authorize(actor)
        row = self.refresh(incident_id)
        fields = self._input_fields(row, action)
        if type(page) is not int or not 0 <= page < (len(fields) + 4) // 5:
            raise SourceConflict("Choose a current guided recovery page.")
        draft = self.store.input_draft(incident_id, action)
        return dict(
            row=row,
            action=action,
            page=page,
            pages=(len(fields) + 4) // 5,
            fields=[
                dict(field, value=draft["input"].get(field["key"], ""))
                for field in fields[page * 5 : (page + 1) * 5]
            ],
            draft_version=draft["version"],
            completed=sum(bool(draft["input"].get(f["key"])) for f in fields),
            total=len(fields),
        )

    def _input_fields(self, row, action):
        if (
            row["pending_action"]
            or row["State"] != "open"
            or row["evidence"]["actions"].get(action, {}).get("input") is not True
        ):
            raise SourceConflict("This guided input is no longer available; recheck the incident.")
        return self.adapters[row["SourceKind"]].input_fields(
            row["SourceID"], action, row["EvidenceHash"]
        )

    def save_input(self, actor, incident_id, revision, token, action, page, draft_version, values):
        self.authorize(actor)
        current = self.input_page(actor, incident_id, action, page)
        if (current["row"]["Revision"], current["row"]["EvidenceHash"]) != (revision, token):
            raise SourceConflict("Recovery evidence changed. Reopen the guided form.")
        fields = {f["key"]: f for f in current["fields"]}
        if (
            not isinstance(values, dict)
            or set(values) != set(fields)
            or any(
                not isinstance(v, str) or not 1 <= len(v.strip()) <= fields[k]["max_length"]
                for k, v in values.items()
            )
        ):
            raise SourceConflict("Complete the displayed recovery fields within their limits.")
        self.store.save_input(
            incident_id,
            revision,
            token,
            action,
            draft_version,
            {k: v.strip() for k, v in values.items()},
            f"discord:{actor.user_id}",
        )
        return self.input_page(actor, incident_id, action, page)

    def input_confirmation(self, actor, incident_id, action):
        self.authorize(actor)
        row = self.refresh(incident_id)
        fields = self._input_fields(row, action)
        draft = self.store.input_draft(incident_id, action)
        if set(draft["input"]) != {f["key"] for f in fields}:
            raise SourceConflict("Complete every guided page before confirming.")
        preview = self.adapters[row["SourceKind"]].validate_input(
            row["SourceID"], action, row["EvidenceHash"], draft["input"]
        )
        return dict(row=row, action=action, draft_version=draft["version"], preview=preview)

    def execute_input(self, actor, incident_id, revision, token, action, draft_version):
        self.authorize(actor)
        preview = self.input_confirmation(actor, incident_id, action)
        if preview["draft_version"] != draft_version:
            raise SourceConflict("Saved choices changed; review the confirmation again.")
        draft = self.store.input_draft(incident_id, action)
        return self._execute(
            incident_id,
            revision,
            token,
            action,
            "Admin confirmed the displayed replacement choices and checks",
            f"discord:{actor.user_id}",
            payload=draft["input"],
            draft_version=draft_version,
        )

    def _execute(
        self,
        incident_id,
        revision,
        token,
        action,
        reason,
        actor_identity,
        *,
        payload=None,
        draft_version=None,
    ):
        with recovery_execution(incident_id) as acquired:
            if not acquired:
                return self.present(self.store.get(incident_id))
            self._dispatch(
                incident_id,
                revision,
                token,
                action,
                reason,
                actor_identity,
                payload=payload,
                draft_version=draft_version,
            )
        # The original call has returned. Reconcile its durable receipt only now.
        return self.refresh(incident_id)

    def _dispatch(
        self,
        incident_id,
        revision,
        token,
        action,
        reason,
        actor_identity,
        *,
        payload=None,
        draft_version=None,
    ):
        row = self.refresh(incident_id)
        if row["State"] == "resolved" and not (
            row["SourceKind"] == "export_job"
            and action == "verify_publication"
            and action in row["evidence"]["actions"]
        ):
            return row
        if (row["Revision"], row["EvidenceHash"]) != (revision, token):
            raise SourceConflict(
                "The evidence changed. Reopen this incident to review the current recovery choices."
            )
        adapter = self.adapters[row["SourceKind"]]
        if action not in row["evidence"]["actions"]:
            if row.get("release_notice"):
                raise SourceConflict(row["release_notice"])
            raise SourceConflict("This action is not permitted by the current evidence.")
        if row["evidence"]["actions"][action].get("input") is True and payload is None:
            raise SourceConflict("Complete the guided recovery form before confirming.")
        if payload is not None:
            adapter.validate_input(row["SourceID"], action, token, payload)
        action_id, acquired = self.store.claim(
            incident_id,
            revision,
            token,
            action,
            actor_identity,
            reason,
            **(dict(payload=payload, draft_version=draft_version) if payload is not None else {}),
        )
        if not acquired:
            # No redispatch, even if another process died between intent and call.
            return self.refresh(incident_id)
        try:
            adapter.execute(
                row["SourceID"],
                action,
                token,
                f"recovery:{action_id}",
                reason,
                **(dict(payload=payload) if payload is not None else {}),
            )
        except Exception as exc:
            logger.warning(
                "recovery_action_uncertain incident=%s action=%s error_type=%s",
                incident_id,
                action_id,
                type(exc).__name__,
            )
            self.store.finish(incident_id, action_id, "unknown", {"error_type": type(exc).__name__})
        return self.present(self.store.get(incident_id))
