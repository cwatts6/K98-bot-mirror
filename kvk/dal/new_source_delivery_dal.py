"""SourceDelivery claims, selection fences and pinned export reads.

Connections must be explicitly injected. No default database, timers or automatic retries.
Session application locks serialize a destination across all publications/periods/seasons.
Claimed/uncertain receipts are never reclaimed on age alone.
"""

from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import json
import re
from uuid import uuid4

from kvk.dal.kvk_admin_dal import fetch_source_report_metadata
from kvk.dal.new_source_config_dal import desired_config, locked_period
from kvk.dal.new_source_import_dal import SourceConflict, one, rows, transaction
from kvk.dal.new_source_reporting_dal import load_snapshot
from kvk.schemas.new_source_schema import SOURCE_KEY


@dataclass(frozen=True)
class Destination:
    kind: str
    destination_id: str

    def __post_init__(self):
        if self.kind not in ("sheets", "file", "discord"):
            raise ValueError("Unsupported destination kind.")
        if (
            not isinstance(self.destination_id, str)
            or not self.destination_id.strip()
            or self.destination_id != self.destination_id.strip()
            or len(self.destination_id.encode("utf-16-le")) > 256
            or any(ord(c) < 32 for c in self.destination_id)
        ):
            raise ValueError("An explicit bounded destination identity is required.")


@dataclass(frozen=True)
class DeliveryClaim:
    selection: object
    destination: Destination
    owner_id: str
    fence: int
    state: str
    receipt: str | None


def load_export_snapshot(*, connect, selection):
    envelope = load_snapshot(connect, kvk_no=selection.kvk_no, period_id=selection.period_id)
    pub = envelope.get("publication")
    if (
        not pub
        or str(pub["PublicationID"]) != selection.publication_id
        or envelope["selection"]["SelectionVersion"] != selection.selection_version
    ):
        raise SourceConflict("Export publication changed; request a new explicit selection.")
    meta = fetch_source_report_metadata(connect, envelope)
    with transaction(connect) as cursor:
        cursor.execute(
            "SELECT WeightT4XSource,WeightT5YSource,WeightDeadsZSource,EffectiveFromUTC FROM KVK.SourceWeightConfig WHERE ConfigVersionID=? AND SourceKey=? AND KVK_NO=?",
            pub["ConfigVersionID"],
            SOURCE_KEY,
            selection.kvk_no,
        )
        weights = one(cursor)
    return {"envelope": envelope, "metadata": meta, "weights": weights}


def _selected(cursor, selection):
    _, selected, requests = locked_period(cursor, selection.kvk_no, selection.period_id)
    if (
        not selected
        or str(selected["PublicationID"]) != selection.publication_id
        or selected["SelectionVersion"] != selection.selection_version
    ):
        raise SourceConflict("Stale destination generation.")
    desired = desired_config(cursor, selected, requests)
    cursor.execute(
        "SELECT ConfigVersionID,BuildState FROM KVK.SourcePublication WHERE PublicationID=?",
        selection.publication_id,
    )
    pub = one(cursor)
    if not pub or pub["BuildState"] != "complete" or str(pub["ConfigVersionID"]) != desired:
        raise SourceConflict("Pending desired configuration cannot be exported as current.")


class DeliveryRepository:
    def __init__(self, connect):
        self.connect = connect

    @staticmethod
    def _receipt_json(data):
        for field in ("attempt_slots", "quarantined_slots"):
            if field in data and (
                not isinstance(data[field], list)
                or len(data[field]) > 16
                or len(set(data[field])) != len(data[field])
                or any(
                    not isinstance(v, str) or not re.fullmatch(r"[A-Za-z0-9_-]{3,128}", v)
                    for v in data[field]
                )
            ):
                raise ValueError("Bounded exact workbook identities required.")
        result = json.dumps(data, separators=(",", ":"))
        if len(result.encode("utf-16-le")) > 2048:
            raise ValueError("Delivery evidence exceeds durable receipt capacity.")
        return result

    def checkpoint(self, claim, **updates):
        with transaction(self.connect) as cursor:
            row = self._check_claim(cursor, claim)
            data = json.loads(row["Receipt"])
            if set(updates) - {"phase", "export_complete", "attempt_slots", "audience"}:
                raise ValueError("Checkpoint cannot change delivery identity or quarantine.")
            data.update(updates)
            receipt = self._receipt_json(data)
            cursor.execute(
                "UPDATE KVK.SourceDelivery SET Receipt=?,UpdatedUTC=SYSUTCDATETIME() "
                "WHERE PublicationID=? AND DestinationKind=? AND DestinationID=? AND OwnerID=? AND Fence=?",
                receipt,
                claim.selection.publication_id,
                claim.destination.kind,
                claim.destination.destination_id,
                claim.owner_id,
                claim.fence,
            )
        return DeliveryClaim(
            claim.selection, claim.destination, claim.owner_id, claim.fence, claim.state, receipt
        )

    def quarantined_files(self, destination):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT Receipt FROM KVK.SourceDelivery WHERE DestinationKind=? AND DestinationID=?",
                destination.kind,
                destination.destination_id,
            )
            return frozenset(
                v
                for r in rows(cursor)
                if r["Receipt"]
                for v in json.loads(r["Receipt"]).get("quarantined_slots", [])
            )

    def recover_private_claim(self, selection, destination, key, prior_slots, new_slots):
        """Fence the stopped private attempt and quarantine every possible old target.

        Called under the destination lock. Never reclaims publication/permission uncertainty.
        Legacy private_incomplete receipts require the operator's exact prior registration.
        Delayed private writes can affect only quarantined files, never the new slot set.
        """
        with transaction(self.connect) as cursor:
            _selected(cursor, selection)
            cursor.execute(
                "SELECT * FROM KVK.SourceDelivery WITH (UPDLOCK,HOLDLOCK) WHERE DestinationKind=? AND DestinationID=?",
                destination.kind,
                destination.destination_id,
            )
            existing = rows(cursor)
            row = next(
                (r for r in existing if str(r["PublicationID"]) == selection.publication_id), None
            )
            data = json.loads(row["Receipt"]) if row and row["Receipt"] else {}
            phases = {"private_started", "private_recovery"}
            if row and row["DeliveryState"] == "uncertain":
                phases.add("private_incomplete")
            if (
                not row
                or row["DeliveryState"] not in ("claimed", "uncertain")
                or data.get("phase") not in phases
                or data.get("export_complete") is not False
                or data.get("export_key") != key
                or data.get("selection_version") != selection.selection_version
                or any(
                    r is not row and r["DeliveryState"] in ("claimed", "uncertain")
                    for r in existing
                )
            ):
                raise SourceConflict(
                    "Only a durably private, unexposed attempt can recover in fresh slots."
                )
            if not prior_slots or set(data.get("attempt_slots", prior_slots)) != set(prior_slots):
                raise SourceConflict(
                    "Prior registration does not cover the original attempt targets."
                )
            quarantine = set(prior_slots)
            for r in existing:
                quarantine.update(
                    json.loads(r["Receipt"]).get("quarantined_slots", [])
                    if r.get("Receipt")
                    else []
                )
            if (
                not new_slots
                or quarantine.intersection(new_slots)
                or destination.destination_id in quarantine
            ):
                raise SourceConflict("Recovery requires disjoint fresh workbook slots.")
            data.update(
                phase="private_recovery",
                quarantined_slots=sorted(quarantine),
                attempt_slots=list(new_slots),
            )
            receipt = self._receipt_json(data)
            owner, fence = str(uuid4()), max(r["Fence"] for r in existing) + 1
            cursor.execute(
                "UPDATE KVK.SourceDelivery SET DeliveryState='claimed',AttemptCount=AttemptCount+1,OwnerID=?,Fence=?,Receipt=?,"
                "ClaimedUTC=SYSUTCDATETIME(),UpdatedUTC=SYSUTCDATETIME() WHERE PublicationID=? AND DestinationKind=? AND DestinationID=?",
                owner,
                fence,
                receipt,
                selection.publication_id,
                destination.kind,
                destination.destination_id,
            )
        return DeliveryClaim(selection, destination, owner, fence, "claimed", receipt)

    @contextmanager
    def serialize(self, destination):
        # Session-owned, not a transaction held across private bulk export writes.
        connection = self.connect()
        acquired = False
        resource = (
            "kvk-source-destination:"
            + hashlib.sha256(
                (destination.kind + ":" + destination.destination_id).encode()
            ).hexdigest()
        )
        try:
            cursor = connection.cursor()
            cursor.execute(
                "DECLARE @r int; EXEC @r=sys.sp_getapplock @Resource=?,@LockMode='Exclusive',@LockOwner='Session',@LockTimeout=0; SELECT @r",
                resource,
            )
            if cursor.fetchone()[0] < 0:
                raise SourceConflict("Destination worker already owns the destination.")
            acquired = True
            # End any implicit transaction; the session lock survives this commit.
            connection.commit()
            yield
        finally:
            try:
                if acquired:
                    connection.cursor().execute(
                        "EXEC sys.sp_releaseapplock @Resource=?,@LockOwner='Session'", resource
                    )
                    connection.commit()
            finally:
                connection.close()

    def slot_reusable(self, destination, export_key):
        """Called under the destination session lock; default-deny retained/active receipts.

        In-flight claims for the old generation block reuse. A selected or final
        publication and any non-failed Discord receipt referencing this generation
        retain it. No receipt/history deletion or TTL-based retirement is performed.
        """
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT * FROM KVK.SourceDelivery WHERE DestinationKind=? AND DestinationID=?",
                destination.kind,
                destination.destination_id,
            )
            deliveries = rows(cursor)
            matching = [
                r
                for r in deliveries
                if r["Receipt"] and json.loads(r["Receipt"]).get("export_key") == export_key
            ]
            if not matching or any(
                r["DeliveryState"] in ("claimed", "uncertain") for r in matching
            ):
                return False
            for item in matching:
                cursor.execute(
                    "SELECT p.PeriodState,s.PublicationID AS SelectedID FROM KVK.SourcePublication p "
                    "LEFT JOIN KVK.SourceSelection s ON s.PublicationID=p.PublicationID "
                    "WHERE p.PublicationID=?",
                    item["PublicationID"],
                )
                publication = one(cursor)
                if (
                    not publication
                    or publication["SelectedID"] is not None
                    or publication["PeriodState"] != "live"
                ):
                    return False
            cursor.execute(
                "SELECT PublicationID,Receipt FROM KVK.SourceDelivery WHERE DestinationKind='discord' "
                "AND DeliveryState<>'failed'"
            )
            publication_ids = {str(r["PublicationID"]) for r in matching}
            if any(
                str(r["PublicationID"]) in publication_ids
                or (r["Receipt"] and json.loads(r["Receipt"]).get("export_key") == export_key)
                for r in rows(cursor)
            ):
                return False
        return True

    def check_selections(self, selections):
        with transaction(self.connect) as cursor:
            for selection in sorted(selections, key=lambda s: (s.kvk_no, s.period_id)):
                _selected(cursor, selection)

    def claim(self, selection, destination, export_key):
        with transaction(self.connect) as cursor:
            _selected(cursor, selection)
            cursor.execute(
                "SELECT * FROM KVK.SourceDelivery WITH (UPDLOCK,HOLDLOCK) WHERE DestinationKind=? AND DestinationID=?",
                destination.kind,
                destination.destination_id,
            )
            existing = rows(cursor)
            row = next(
                (r for r in existing if str(r["PublicationID"]) == selection.publication_id),
                None,
            )
            if any(r["DeliveryState"] in ("claimed", "uncertain") for r in existing):
                raise SourceConflict(
                    "Destination requires receipt reconciliation before more writes."
                )
            if row and row["DeliveryState"] == "confirmed":
                receipt = json.loads(row["Receipt"])
                prior_version = receipt.get("selection_version")
                if (
                    receipt.get("export_key") == export_key
                    and prior_version == selection.selection_version
                ):
                    return DeliveryClaim(
                        selection,
                        destination,
                        str(row["OwnerID"]),
                        row["Fence"],
                        "confirmed",
                        row["Receipt"],
                    )
                if type(prior_version) is not int or prior_version >= selection.selection_version:
                    raise SourceConflict("Confirmed delivery has another generation manifest.")
            if row and row["Receipt"]:
                prior = json.loads(row["Receipt"])
                prior_version = prior.get("selection_version")
                if prior.get("export_key") != export_key and (
                    type(prior_version) is not int or prior_version >= selection.selection_version
                ):
                    raise SourceConflict("Retry cannot change its generation manifest.")
            owner = str(uuid4())
            fence = max((r["Fence"] for r in existing), default=0) + 1
            receipt = json.dumps(
                {
                    "export_key": export_key,
                    "publication_id": selection.publication_id,
                    "selection_version": selection.selection_version,
                },
                separators=(",", ":"),
            )
            evidence = json.loads(receipt)
            quarantined = sorted(
                {
                    v
                    for r in existing
                    if r.get("Receipt")
                    for v in json.loads(r["Receipt"]).get("quarantined_slots", [])
                }
            )
            if quarantined:
                evidence["quarantined_slots"] = quarantined
            receipt = self._receipt_json(evidence)
            if not row:
                cursor.execute(
                    "INSERT KVK.SourceDelivery (PublicationID,SourceKey,KVK_NO,PeriodID,DestinationKind,DestinationID,DeliveryState,AttemptCount,Fence,CreatedUTC,UpdatedUTC) VALUES (?,?,?,?,?,?,'pending',0,0,SYSUTCDATETIME(),SYSUTCDATETIME())",
                    selection.publication_id,
                    SOURCE_KEY,
                    selection.kvk_no,
                    selection.period_id,
                    destination.kind,
                    destination.destination_id,
                )
            cursor.execute(
                "UPDATE KVK.SourceDelivery SET DeliveryState='claimed',AttemptCount=AttemptCount+1,OwnerID=?,Fence=?,Receipt=?,ClaimedUTC=SYSUTCDATETIME(),ConfirmedUTC=NULL,UpdatedUTC=SYSUTCDATETIME() WHERE PublicationID=? AND DestinationKind=? AND DestinationID=?",
                owner,
                fence,
                receipt,
                selection.publication_id,
                destination.kind,
                destination.destination_id,
            )
        return DeliveryClaim(selection, destination, owner, fence, "claimed", receipt)

    def _check_claim(self, cursor, claim):
        cursor.execute(
            "SELECT * FROM KVK.SourceDelivery WITH (UPDLOCK,HOLDLOCK) WHERE PublicationID=? AND DestinationKind=? AND DestinationID=?",
            claim.selection.publication_id,
            claim.destination.kind,
            claim.destination.destination_id,
        )
        row = one(cursor)
        if (
            not row
            or str(row["OwnerID"]) != claim.owner_id
            or row["Fence"] != claim.fence
            or row["DeliveryState"] not in ("claimed", "uncertain")
        ):
            raise SourceConflict("Delivery owner/fence changed.")
        return row

    @contextmanager
    def publication_gate(self, claim, selections):
        """Hold selection locks only for the bounded discoverable-pointer/send operation.

        All selection writers use the same season lock. A timeout leaves an uncertain
        receipt, so delayed external effects cannot race a subsequent destination worker.
        """
        with transaction(self.connect) as cursor:
            for selection in sorted(selections, key=lambda s: (s.kvk_no, s.period_id)):
                _selected(cursor, selection)
            self._check_claim(cursor, claim)
            yield

    def finish(self, claim, state, receipt):
        if (
            state not in ("confirmed", "failed", "uncertain")
            or not isinstance(receipt, str)
            or not 0 < len(receipt.encode("utf-16-le")) <= 2048
        ):
            raise ValueError("A bounded durable receipt is required.")
        json.loads(receipt)
        with transaction(self.connect) as cursor:
            old = self._check_claim(cursor, claim)
            data, previous = json.loads(receipt), json.loads(old["Receipt"])
            if data.get("export_key") != previous.get("export_key") or data.get(
                "selection_version"
            ) != previous.get("selection_version"):
                raise SourceConflict("Delivery receipt cannot change generation identity.")
            for field in ("attempt_slots", "quarantined_slots", "audience"):
                if field in previous:
                    data[field] = previous[field]
            receipt = self._receipt_json(data)
            cursor.execute(
                "UPDATE KVK.SourceDelivery SET DeliveryState=?,Receipt=?,ConfirmedUTC=CASE WHEN ?='confirmed' THEN SYSUTCDATETIME() ELSE NULL END,UpdatedUTC=SYSUTCDATETIME() WHERE PublicationID=? AND DestinationKind=? AND DestinationID=? AND OwnerID=? AND Fence=?",
                state,
                receipt,
                state,
                claim.selection.publication_id,
                claim.destination.kind,
                claim.destination.destination_id,
                claim.owner_id,
                claim.fence,
            )
        return receipt

    def rollback_completed_receipt(self, claim):
        """Recognize a terminal historical acknowledgement invalidated by audited rollback.

        This confirms only the old receipt, never the newly selected export. Unknown
        sends/writes have no completed acknowledgement and must still be probed externally.
        """
        data = json.loads(claim.receipt) if claim.receipt else {}
        version = data.get("selection_version")
        remote = data.get("remote_id")
        if (
            claim.state != "uncertain"
            or data.get("phase")
            != ("discord_confirmed" if claim.destination.kind == "discord" else "published")
            or data.get("export_complete") is not True
            or data.get("publication_id") != claim.selection.publication_id
            or type(version) is not int
            or not 0 < version < claim.selection.selection_version
            or not isinstance(remote, str)
            or not 0 < len(remote) <= 512
        ):
            return None
        with transaction(self.connect) as cursor:
            _selected(cursor, claim.selection)
            row = self._check_claim(cursor, claim)
            if row["Receipt"] != claim.receipt:
                raise SourceConflict("Rollback receipt changed during reconciliation.")
            cursor.execute(
                "SELECT ProvenanceJson FROM KVK.SourceAction WHERE SourceKey=? AND KVK_NO=? "
                "AND PeriodID=? AND NewPublicationID=? AND NewSelectionVersion=? AND ActionType='rollback'",
                SOURCE_KEY,
                claim.selection.kvk_no,
                claim.selection.period_id,
                claim.selection.publication_id,
                claim.selection.selection_version,
            )
            action = one(cursor)
            if not action or [claim.destination.kind, claim.destination.destination_id] not in (
                json.loads(action["ProvenanceJson"]).get("destinations", [])
            ):
                return None
        return claim.receipt

    def read_receipt(self, selection, destination):
        with transaction(self.connect) as cursor:
            cursor.execute(
                "SELECT * FROM KVK.SourceDelivery WHERE PublicationID=? AND DestinationKind=? AND DestinationID=?",
                selection.publication_id,
                destination.kind,
                destination.destination_id,
            )
            row = one(cursor)
        if not row:
            return None
        return DeliveryClaim(
            selection,
            destination,
            str(row["OwnerID"]),
            row["Fence"],
            row["DeliveryState"],
            row["Receipt"],
        )
