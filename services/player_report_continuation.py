"""Guided fresh report followed by separately verified local cache publication."""

from copy import deepcopy
import json

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.export_coordination_dal import identity
from services.producer_recovery_intent import report_retry_intent


class PlayerReportContinuation:
    kind = "player_report_continuation"
    observe_healthy = False

    def __init__(self, dal, producer, *, runner=None, cache_runner=None):
        self.dal, self.producer = dal, producer
        self.runner = runner or self._run
        self.cache_runner = cache_runner or self._cache

    def pending_recovery(self, *, after=None):
        return self.dal.pending(after)

    def inspect(self, source_id):
        state = self.dal.snapshot(source_id)
        marker, child = state["marker"], state["child"]
        evidence = dict(
            title="Fresh player report and cache",
            outcome="choose_report_refresh",
            explanation="The failed cache-only report was closed without committing. Imported scans remain intact. Choose a fresh report from the currently stored scans and settings, or explicitly retain the prior report and cache.",
            actions={},
            recovery_links=[],
        )
        original = json.loads(state["root"]["RequestJson"])["request"]["config"]
        registration = "matches" if original == state["current"]["scan_data"] else "differs from"
        evidence["failure_context"] = dict(
            summary=(
                "Original attempt (UTC): "
                + str(state["root"].get("CreatedUTC", "not recorded"))
                + ". Input: existing imported scans; no new file. Registered output configuration "
                + registration
                + " the current registration. Original SQL calculation settings and the precise "
                "failure cause were not retained; a difference is not proof of the cause."
            )
        )
        resolved = False
        if marker and marker.get("choice") == "keep_prior":
            evidence.update(
                outcome="prior_report_retained",
                explanation="The admin retained the prior report and cache. Their freshness is not certified; no report, import or spreadsheet write was replayed.",
            )
            resolved = True
        elif marker and marker.get("cache_receipt"):
            evidence.update(
                outcome="report_and_cache_verified",
                explanation="The separate report has a verified atomic checkpoint. The local cache was built from a validated SQL snapshot, written and read back before this receipt was saved. Its source scan timestamp may be older than the rebuild. This does not certify spreadsheet delivery or later changes.",
                cache_receipt=deepcopy(marker["cache_receipt"]),
            )
            resolved = True
        elif child:
            result, _, child_resolved = self.producer.inspect(child["PreparationID"])
            if result["outcome"] == "report_cancelled":
                child = None
            else:
                evidence["recovery_links"].append(
                    dict(
                        label="Review fresh report result",
                        kind=self.producer.kind,
                        source_id=child["PreparationID"],
                    )
                )
                evidence.update(
                    outcome="report_recovery_pending",
                    explanation="The fresh report has its own retained result. Finish its evidence/capture checks before refreshing the local cache; do not run the report again.",
                )
                if child_resolved and result["outcome"] == "cache_only_completed":
                    evidence.update(
                        outcome="cache_refresh_pending",
                        explanation="The fresh report and its no-export disposition are verified. Refresh the local cache from the currently stored SQL report next. This step does not rerun the report procedure or an import.",
                    )
                    evidence["actions"]["refresh_cache"] = dict(
                        label="Refresh local player cache",
                        check="Confirm the local cache should use the currently stored player report. No new scan is imported; the source scan time is retained.",
                        effect="Read and validate the SQL report, preserve the existing cache on validation failure, atomically replace the local cache and verify its bytes. Save its source time, season, row count and hash.",
                    )
        elif marker:
            evidence.update(
                outcome="checking_report_attempt",
                explanation="The confirmed report attempt is being reconciled. Its SQL procedure cannot be replayed while the outcome is unknown.",
            )
        if not resolved and (not marker or (state["child"] and child is None)):
            evidence["actions"] = dict(
                refresh_report=dict(
                    label="Build fresh player report",
                    check="Confirm a new report should be calculated from existing imported scans and current SQL settings. This does not import a new file or retry the old failed transaction.",
                    effect="Save an exact approval, run one separately identified atomic report, retain its output and verify its result. Local cache publication is a separate next step; no spreadsheet export is queued.",
                ),
                keep_prior=dict(
                    label="Keep prior report and cache",
                    check="Confirm the existing report and cache should remain in use without a freshness claim.",
                    effect="Save this decision against the closed attempt. No SQL, cache or provider change is made.",
                ),
            )
        if state["blocker"] and not resolved:
            evidence["actions"].pop("refresh_report", None)
            evidence["actions"].pop("refresh_cache", None)
            evidence.update(
                outcome="waiting_for_access",
                explanation="Another operation owns the required access. Review it, then Recheck after it settles; no reservation is taken from that operation.",
            )
            owner = state["blocker"].get("owner")
            if owner:
                evidence["recovery_links"].append(dict(label="Review blocking operation", **owner))
        return evidence, digest(state).hex(), resolved

    def execute(self, source_id, action, token, actor, reason):
        if not actor.startswith("recovery:"):
            raise SourceConflict("Confirmed admin action required.")
        action_id = identity(actor.removeprefix("recovery:"))
        with self.dal.serialized(source_id):
            evidence, current, resolved = self.inspect(source_id)
            if resolved or token != current or action not in evidence["actions"]:
                raise SourceConflict("Report/cache evidence changed; reopen the incident.")
            state = self.dal.snapshot(source_id)
            if action == "refresh_cache":
                marker = deepcopy(state["marker"])
                receipt = self.cache_runner()
                marker["cache_receipt"] = dict(receipt, action=action_id, token=token)
                self.dal.record(source_id, token, marker)
                return
            marker = dict(
                action=action_id,
                token=token,
                reason=reason,
                choice="keep_prior" if action == "keep_prior" else "retry",
                configuration=state["current"],
            )
            self.dal.record(source_id, token, marker)
            if action == "refresh_report":
                from services.legacy_export_snapshot_service import use_runtime

                with use_runtime(self.dal.runtime), report_retry_intent(action_id, source_id):
                    self.runner()

    def reconcile(self, source_id, action):
        kind = action["ActionKind"]
        if kind not in {"refresh_report", "refresh_cache", "keep_prior"}:
            raise SourceConflict("Unsupported report/cache action.")
        with self.dal.serialized(source_id):
            state = self.dal.snapshot(source_id)
            marker = state["marker"]
            if kind == "refresh_cache":
                receipt = (marker or {}).get("cache_receipt") or {}
                if (
                    receipt.get("action") == identity(action["ActionID"])
                    and receipt.get("token") == action["EvidenceHash"]
                ):
                    return "verified"
                if marker and digest(state).hex() == action["EvidenceHash"]:
                    marker = deepcopy(marker)
                    marker["cache_unacknowledged"] = identity(action["ActionID"])
                    self.dal.record(source_id, action["EvidenceHash"], marker)
                return "not_applied"
            choice = "keep_prior" if kind == "keep_prior" else "retry"
            if not marker or marker.get("action") != identity(action["ActionID"]):
                if digest(state).hex() != action["EvidenceHash"]:
                    return "not_applied"
                marker = dict(
                    action=identity(action["ActionID"]),
                    token=action["EvidenceHash"],
                    reason="Dispatch not acknowledged; never replay automatically",
                    choice=choice,
                    configuration=state["current"],
                )
                self.dal.record(source_id, action["EvidenceHash"], marker)
            if marker.get("token") != action["EvidenceHash"] or marker.get("choice") != choice:
                raise SourceConflict("Report action differs from its saved approval.")
            if choice == "keep_prior":
                return "verified"
            identifier = self.dal.reserve_for_reconciliation(source_id, marker)
            if self.dal.close_uncommitted(identifier, marker):
                return "not_applied"
            self.producer.inspect(identifier)
            return "verified"

    @staticmethod
    def _run():
        from file_utils import get_conn_with_retries
        from player_stats_cache import _execute_sp_with_retries

        with get_conn_with_retries(meta={"operation": "guided_player_report"}) as connection:
            _execute_sp_with_retries(connection, retries=1)

    @staticmethod
    def _cache():
        from player_stats_cache import rebuild_validated_cache_only

        return rebuild_validated_cache_only()
