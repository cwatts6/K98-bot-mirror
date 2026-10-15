"""Authority-owned investigation and settlement of registered abandoned reads.

Only a preparation identity and an evidence digest cross IPC. Private journals,
SQL identity and resource membership are reconstructed inside the authority.
"""

import json

from kvk.dal.new_source_import_dal import SourceConflict, digest
from services.config_preparation_recovery_dal import ConfigPreparationRecoveryDAL
from services.config_preparation_recovery_service import ConfigPreparationRecovery, RecoveryTarget
from services.export_coordination_dal import identity
from services.legacy_export_snapshot_service import configuration_digest


def _inspect(authority, registration, preparation_id):
    configured = registration.value()
    scope = configured["legacy_configuration"]["config"]
    dal = ConfigPreparationRecoveryDAL(authority.dal.connect)
    data = dal.target_data(
        preparation_id, account=configured["account"], storage_owner=configured["storage_owner"]
    )
    # Finish interrupted local closure, or verify retirement of an old-session
    # read from its private birth. No live process or writer is adopted.
    for stream_id in data["stream_ids"]:
        owned = authority._streams.get(stream_id)
        if owned is not None and owned.purpose == "probe" and (owned.frozen or owned.uncertain):
            try:
                authority.recover_owned_closure(stream_id)
            except Exception:
                # Existing inspection below retains the incident and explains the
                # unverified closure. A temporary SQL/store failure is not release.
                pass
        elif owned is None:
            try:
                authority.recover_abandoned_read_closure(stream_id)
            except Exception:
                # Older/missing birth, another host, live child or unknown SQL
                # acknowledgement retains ownership; inspection reports the hold.
                pass
    data = dal.target_data(
        preparation_id, account=configured["account"], storage_owner=configured["storage_owner"]
    )
    p = data["preparation"]
    result = dict(
        preparation_id=preparation_id,
        token=digest(data).hex(),
        outcome="held",
        eligible=False,
        settled_token=None,
        explanation="The read remains held until its exact execution evidence is verified.",
    )
    audit = json.loads(p["GenerationJson"]) if p["GenerationJson"] else {}
    if not data["resources"] and p["State"] == "completed":
        result.update(
            outcome="resolved",
            explanation="The configuration read completed and released its reservations.",
        )
        return result, None
    if (
        not data["resources"]
        and p["State"] == "unavailable"
        and audit.get("kind") in {"config_no_dispatch_recovery/1", "config_read_containment/1"}
    ):
        if audit["kind"] == "config_read_containment/1":
            from services.config_read_containment import (
                verify_contained_read,
                verify_preparation_receipt,
            )

            verify_preparation_receipt(
                authority.store,
                audit,
                preparation_id=preparation_id,
                account=configured["account"],
                storage_owner=configured["storage_owner"],
            )
            if data["stream_ids"] != [s["StreamID"] for s in audit["before"]["streams"]]:
                raise SourceConflict("Contained read membership changed after release.")
            for stream_id in data["stream_ids"]:
                stream = authority.dal.read_stream(stream_id)
                if (
                    str(stream["ClosureReference"]).lower() != audit["receipt"]["reference"]
                    or bytes(stream["ClosureHash"]).hex() != audit["receipt"]["sha256"]
                ):
                    raise SourceConflict("Contained read receipt differs after release.")
                verify_contained_read(
                    authority.dal,
                    authority.store,
                    stream,
                    account=configured["account"],
                    registration_hash=bytes.fromhex(configuration_digest(scope)),
                )
        result.update(
            outcome="resolved",
            settled_token=audit.get("snapshot_sha256"),
            explanation=(
                "The read was cancelled before execution and its exact reservations released. No provider request was dispatched."
                if audit.get("kind") == "config_read_containment/1" and not data["stream_ids"]
                else "The read was isolated from further dispatch and its exact reservations released. Its result was discarded; no child termination or provider health is asserted."
                if audit.get("kind") == "config_read_containment/1"
                else "The abandoned read was safely closed and its reservations released. This does not assert that the provider is healthy."
            ),
        )
        return result, None
    target_identity = dal.identity()
    target = RecoveryTarget(
        target_identity["server"],
        target_identity["database"],
        preparation_id,
        configured["account"],
        identity(p["OwnerID"]),
        p["Fence"],
        p["Version"],
        tuple((r["ResourceKey"], r["Version"]) for r in data["resources"]),
        tuple(data["stream_ids"]),
    )
    expected_keys = sorted(
        {"account:" + configured["account"], *("destination:" + d for d in scope["destinations"])}
    )
    if [key for key, _ in target.resources] != expected_keys:
        result["explanation"] = (
            "Reservation membership differs from the installed configuration. No release is permitted."
        )
        return result, None
    recovery = ConfigPreparationRecovery(
        dal=dal,
        execution=authority.dal,
        store=authority.store,
        target=target,
        registration_hash=configuration_digest(scope),
        storage_owner=configured["storage_owner"],
        allow_reads=True,
    )
    try:
        report = recovery.inspect()
    except (ValueError, KeyError, TypeError, OSError) as exc:
        result["explanation"] = str(exc)
        from services.config_read_containment import ConfigReadContainment

        recovery = ConfigReadContainment(
            dal=dal,
            execution=authority.dal,
            store=authority.store,
            target=target,
            registration_hash=configuration_digest(scope),
            storage_owner=configured["storage_owner"],
        )
        try:
            report = recovery.inspect()
        except (ValueError, KeyError, TypeError, OSError):
            return result, None
        result.update(
            token=report["snapshot_sha256"],
            eligible=True,
            outcome="read_containment" if data["stream_ids"] else "unstarted_read",
            explanation=(
                "The registered configuration read claimed reservations but never opened an execution stream. Its complete SQL ledger contains no provider request. An admin can cancel this read and atomically fence its old claim before releasing its exact reservations."
                if not data["stream_ids"]
                else "Private closure could not be verified. The complete SQL request ledger is read-only. An admin can discard this read and atomically prevent further requests before releasing its exact reservations. This does not assert child termination or provider health."
            ),
        )
        return result, recovery
    result.update(
        token=report["snapshot_sha256"],
        eligible=True,
        outcome="abandoned_read",
        explanation="The authority verified the complete private journal, a closed child and read-only requests. The failed read can be abandoned without releasing any writer.",
    )
    return result, recovery


def inspect_configuration_recovery(authority, registration, preparation_id):
    with authority._lock:
        result, _ = _inspect(authority, registration, identity(preparation_id))
        return result


def apply_configuration_recovery(
    authority, registration, preparation_id, token, actor, reason, *, action="release_read"
):
    if not isinstance(actor, str) or not 1 <= len(actor) <= 128:
        raise ValueError("Bounded recovery actor required.")
    if not isinstance(reason, str) or not 1 <= len(reason.strip()) <= 512:
        raise ValueError("Bounded recovery reason required.")
    with authority._lock:
        result, recovery = _inspect(authority, registration, identity(preparation_id))
        if result["outcome"] == "resolved" and result["settled_token"] == token:
            return result
        expected_outcomes = {
            "release_read": {"abandoned_read"},
            "contain_read": {"read_containment", "unstarted_read"},
        }.get(action, set())
        if (
            recovery is None
            or result["token"] != token
            or result["outcome"] not in expected_outcomes
        ):
            raise SourceConflict("Read recovery evidence changed; review its current status.")
        recovery.apply(approved_snapshot_sha256=token, actor=actor, reason=reason)
        # Read the committed release; an unknown acknowledgement remains unknown.
        result, _ = _inspect(authority, registration, identity(preparation_id))
        if result["outcome"] != "resolved" or result["settled_token"] != token:
            raise SourceConflict("Read recovery settlement is not yet verified.")
        return result
