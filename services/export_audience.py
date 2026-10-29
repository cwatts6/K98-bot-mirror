"""Durable audience evidence shared by delivery, retirement and journal replay."""

import json

from kvk.dal.new_source_import_dal import SourceConflict


def audience_evidence(*, public):
    # Preserve historical private evidence bytes. New public evidence never
    # claims privacy, even where the SQL phase name predates public staging.
    return {"private": False, "audience": "public_viewer"} if public else {"private": True}


def check_audience(evidence, pool):
    if not isinstance(evidence, dict):
        raise SourceConflict("Typed audience readback required.")
    if evidence.get("private") is True and "audience" not in evidence:
        return "private"
    registration = json.loads(pool["RegistrationJson"])
    if (
        evidence.get("private") is False
        and evidence.get("audience") == "public_viewer"
        and registration.get("audience") == "public_viewer"
    ):
        return "public_viewer"
    raise SourceConflict("Readback audience differs from registered policy.")
