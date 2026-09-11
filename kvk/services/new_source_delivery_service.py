"""Explicit private export/delivery orchestration over injected transports and durable DAL.

No background worker or daily-send admission is installed here. A Discord caller must
already own normal cadence admission; uncertain outcomes never authorize replacement.
"""

from dataclasses import dataclass
import json
import logging

from kvk.dal.new_source_import_dal import SourceConflict

logger = logging.getLogger(__name__)


class DestinationSetupRequired(RuntimeError):
    """Operator must provision or repair an explicitly registered destination."""


class RemoteOutcomeUnknown(RuntimeError):
    """A non-idempotent remote operation may have completed; reconcile before retry."""


class RemoteRequestRejected(RuntimeError):
    """Provider returned a terminal rejection; this request did not take effect."""


@dataclass(frozen=True)
class DeliveryOutcome:
    sql_selected: bool
    export_complete: bool
    delivery_state: str
    receipt: str | None = None
    setup_required: str | None = None
    diagnostic: dict | None = None


def _receipt(
    key,
    *,
    publication_id,
    selection_version,
    export_complete=False,
    remote_id=None,
    phase,
    diagnostic=None,
    audience=None,
):
    if remote_id is not None and (
        not isinstance(remote_id, str) or not remote_id or len(remote_id) > 512
    ):
        raise ValueError("Transport receipt must be a bounded opaque identity.")
    if phase in ("published", "discord_confirmed") and remote_id is None:
        raise ValueError("Successful delivery requires an actual remote receipt.")
    payload = dict(
        export_key=key,
        publication_id=publication_id,
        selection_version=selection_version,
        export_complete=export_complete,
        remote_id=remote_id,
        phase=phase,
    )
    if diagnostic is not None:
        payload["diagnostic"] = diagnostic
    if audience is not None:
        payload["audience"] = audience
    value = json.dumps(payload, separators=(",", ":"))
    if len(value.encode("utf-16-le")) > 2048:
        raise ValueError("Receipt exceeds durable storage contract.")
    return value


def deliver_export(
    *,
    generation,
    selection,
    destination,
    repository,
    transport,
    recover_private=False,
    prior_registration=None,
):
    """Transport writes/reads private immutable generation ranges using RAW strings.

    ensure_private(key, manifest) must create/resume an isolated private generation.
    write_range overwrites the same exact range; verify must return the complete remote
    name/hash/row/column manifest (including unexpected tabs). publish_current changes
    the discoverable pointer after any configured Viewer grants and returns a receipt.
    Unknown Google mutations block retries. Explicit private recovery fences the old
    attempt and quarantines its slots; publication uncertainty requires reconciliation.
    """
    if destination.kind not in ("sheets", "file") or selection not in generation.selections:
        raise ValueError("Export destination and publication must be explicit.")
    with repository.serialize(destination):
        from kvk.services.new_source_export_service import GoogleSheetsTransport, SheetsRegistration

        google = isinstance(transport, GoogleSheetsTransport)
        if recover_private and (
            not google or not isinstance(prior_registration, SheetsRegistration)
        ):
            raise ValueError("Private recovery requires the explicit prior Google registration.")
        if google:
            generation = transport.prepare_generation(generation)
        repository.check_selections(generation.selections)
        if recover_private:
            if prior_registration.index_file_id != destination.destination_id:
                raise ValueError("Recovery must retain the same destination index.")
            claim = repository.recover_private_claim(
                selection,
                destination,
                generation.key,
                prior_registration.slot_file_ids,
                transport.registration.slot_file_ids,
            )
        else:
            claim = repository.claim(selection, destination, generation.key)
        audience = transport.registration.audience if google else None
        if claim.state == "confirmed":
            if google and json.loads(claim.receipt).get("audience", "private") != audience:
                raise SourceConflict(
                    "Confirmed destination audience differs; explicit republication required."
                )
            return DeliveryOutcome(True, True, "confirmed", claim.receipt)
        complete, exposed = False, False
        try:
            if google:
                transport.quarantined = repository.quarantined_files(destination)
                if transport.quarantined.intersection(transport.registration.slot_file_ids):
                    raise SourceConflict("Registration contains quarantined workbook slots.")
                claim = repository.checkpoint(
                    claim,
                    phase="private_started",
                    export_complete=False,
                    attempt_slots=list(transport.registration.slot_file_ids),
                    audience=audience,
                )
            manifest = generation.manifest()
            transport.ensure_private(destination, generation.key, manifest)
            for item in generation.tables:
                transport.write_range(
                    destination,
                    generation.key,
                    item.name,
                    "A1",
                    item.raw_values(),
                    value_input_option="RAW",
                )
            if transport.verify(destination, generation.key) != manifest:
                raise SourceConflict("Private export sections failed exact manifest verification.")
            complete = True
            if google:
                # Durable before any public permission or pointer request can be submitted.
                claim = repository.checkpoint(
                    claim, phase="publication_pending", export_complete=True
                )
            with repository.publication_gate(claim, generation.selections):
                exposed = True
                remote = transport.publish_current(destination, generation.key, claim.fence)
            receipt = _receipt(
                generation.key,
                publication_id=selection.publication_id,
                selection_version=selection.selection_version,
                export_complete=True,
                remote_id=remote,
                phase="published",
                audience=audience,
            )
            receipt = repository.finish(claim, "confirmed", receipt) or receipt
            logger.info(
                "Source export confirmed publication=%s fence=%s",
                selection.publication_id,
                claim.fence,
            )
            return DeliveryOutcome(True, True, "confirmed", receipt)
        except Exception as exc:
            state = "uncertain" if exposed or isinstance(exc, RemoteOutcomeUnknown) else "failed"
            receipt = _receipt(
                generation.key,
                publication_id=selection.publication_id,
                selection_version=selection.selection_version,
                export_complete=complete,
                phase="publish_uncertain" if exposed else "private_incomplete",
                diagnostic=transport.last_error if google else None,
                audience=audience,
            )
            receipt = repository.finish(claim, state, receipt) or receipt
            logger.warning(
                "Source export outcome publication=%s state=%s", selection.publication_id, state
            )
            return DeliveryOutcome(
                True,
                complete,
                state,
                receipt,
                str(exc) if isinstance(exc, DestinationSetupRequired) else None,
                transport.last_error if google else None,
            )


def deliver_discord(
    *,
    selection,
    destination,
    export_key,
    export_receipt,
    repository,
    transport,
    cadence_admitted,
    message_id=None,
):
    """Send or edit exactly the admitted operation; an uncertain edit never becomes a send."""
    if destination.kind != "discord" or cadence_admitted is not True:
        raise ValueError(
            "Discord delivery requires explicit destination and normal cadence admission."
        )
    receipt_data = json.loads(export_receipt)
    if (
        receipt_data.get("export_key") != export_key
        or receipt_data.get("phase") != "published"
        or receipt_data.get("export_complete") is not True
    ):
        raise ValueError("Discord delivery requires the matching completed export receipt.")
    if (
        receipt_data.get("publication_id") != selection.publication_id
        or receipt_data.get("selection_version") != selection.selection_version
    ):
        raise ValueError("Export receipt belongs to another selection version.")
    if message_id is not None and (
        not isinstance(message_id, str)
        or not message_id.isdecimal()
        or int(message_id) <= 0
        or len(message_id) > 32
    ):
        raise ValueError("Invalid explicit edit receipt.")
    with repository.serialize(destination):
        claim = repository.claim(selection, destination, export_key)
        if claim.state == "confirmed":
            return DeliveryOutcome(True, True, "confirmed", claim.receipt)
        invoked = False
        try:
            with repository.publication_gate(claim, (selection,)):
                invoked = True
                remote = transport.deliver(destination, export_receipt, message_id=message_id)
            receipt = _receipt(
                export_key,
                publication_id=selection.publication_id,
                selection_version=selection.selection_version,
                export_complete=True,
                remote_id=remote,
                phase="discord_confirmed",
            )
            repository.finish(claim, "confirmed", receipt)
            return DeliveryOutcome(True, True, "confirmed", receipt)
        except Exception:
            state = "uncertain" if invoked else "failed"
            receipt = _receipt(
                export_key,
                publication_id=selection.publication_id,
                selection_version=selection.selection_version,
                export_complete=True,
                remote_id=message_id,
                phase="discord_uncertain" if invoked else "not_sent",
            )
            repository.finish(claim, state, receipt)
            logger.warning(
                "Source Discord outcome publication=%s state=%s",
                selection.publication_id,
                state,
            )
            return DeliveryOutcome(True, True, state, receipt)


def reconcile_delivery(*, selection, destination, repository, transport):
    """Read-only external receipt probe; unknown/in-flight remains blocked across restarts.

    Probe returns (confirmed|absent|unknown, receipt). 'absent' must prove the previous
    operation is terminal with no delayed effect, never merely a momentary missing item.
    This method does not retry or delete any external artifact/message.
    """
    with repository.serialize(destination):
        claim = repository.read_receipt(selection, destination)
        if claim is None or claim.state not in ("claimed", "uncertain"):
            return claim
        historical = repository.rollback_completed_receipt(claim)
        if historical is not None:
            # An audited rollback invalidated the fence after this operation completed.
            # Preserve its old selection version: the new export still needs a fresh claim.
            repository.finish(claim, "confirmed", historical)
            return repository.read_receipt(selection, destination)
        state, receipt = transport.reconcile(destination, claim)
        if state == "unknown":
            return claim
        if state not in ("confirmed", "absent"):
            raise ValueError("Invalid receipt reconciliation outcome.")
        data = json.loads(receipt)
        original = json.loads(claim.receipt)
        if (
            data.get("publication_id") != original.get("publication_id")
            or data.get("export_key") != original.get("export_key")
            or data.get("selection_version") != original.get("selection_version")
        ):
            raise SourceConflict("Receipt probe returned another generation.")
        if state == "confirmed" and (
            not data.get("remote_id")
            or data.get("export_complete") is not True
            or data.get("phase")
            != ("discord_confirmed" if destination.kind == "discord" else "published")
        ):
            raise SourceConflict("Confirmed probe requires complete destination evidence.")
        repository.finish(claim, "confirmed" if state == "confirmed" else "failed", receipt)
        return repository.read_receipt(selection, destination)
