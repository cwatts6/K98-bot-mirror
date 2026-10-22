"""Validate permanent isolation separately from the replacement registration.

A missing activation receipt must not create a verification cycle: isolation can
be checked from its own original sealed snapshot and the exact SQL retirement
association. This function grants no authority to the replacement registration.
"""

import hashlib
import json

from kvk.dal.new_source_import_dal import SourceConflict
from services.export_coordination_dal import identity


def isolated_pool(dal, store, current, before, containment_id, *, rollover=False):
    activation = dal.replacement_retirement(current["PoolID"], current["AccountKey"])
    if (
        not activation
        or activation["AccountKey"] != current["AccountKey"]
        or identity(activation["ContainmentID"]) != identity(containment_id)
        or identity(activation["OldPoolID"]) != identity(current["PoolID"])
        or identity(activation["NewPoolID"]) != identity(activation["ReplacementID"])
        or identity(current["RetiredByReplacementID"]) != identity(activation["ReplacementID"])
    ):
        raise SourceConflict("Retired pool has no exact containment/replacement association.")
    try:
        raw = store.read_reference(
            identity(activation["ReceiptReference"]), bytes.fromhex(activation["ReceiptHash"])
        )
    except (SourceConflict, OSError, KeyError, ValueError):
        # The independent containment snapshot already authenticates the old
        # pool. Only its fixed isolation transition and one SQL retirement may
        # differ. No field of RegistrationJson participates in this proof.
        expected = dict(before)
        expected.setdefault("RetiredByReplacementID", None)
        expected.update(
            PoolState="blocked",
            BlockedReason="Targets permanently isolated; verified replacements required",
            Version=before["Version"] + 1,
        )
        if rollover:
            expected["OwnerID"] = None
        retired_fields = {"RetiredByReplacementID", "Version", "UpdatedUTC"}
        if current["Version"] != expected["Version"] + 1 or {
            k: v for k, v in current.items() if k not in retired_fields
        } != {k: v for k, v in expected.items() if k not in retired_fields}:
            raise SourceConflict(
                "Current permanent isolation differs from its sealed original pool."
            )
        return expected
    audit = json.loads(raw)
    isolated = audit.get("before_pool")
    retired_fields = {"RetiredByReplacementID", "Version", "UpdatedUTC"}
    if (
        hashlib.sha256(raw).hexdigest() != activation["ReceiptHash"]
        or audit.get("kind") != "export_replacement_activation/1"
        or audit.get("activation_id") != identity(activation["ActivationID"])
        or audit.get("replacement_id") != identity(activation["ReplacementID"])
        or not isinstance(isolated, dict)
        or current["Version"] != isolated["Version"] + 1
        or {k: v for k, v in current.items() if k not in retired_fields}
        != {k: v for k, v in isolated.items() if k not in retired_fields}
    ):
        raise SourceConflict("Pool replacement differs from its sealed retirement.")
    return isolated
