"""Guided file roles and strict identity-only input; never follow supplied URLs."""

import re
from urllib.parse import urlsplit

from kvk.dal.new_source_import_dal import SourceConflict


def file_identity(value):
    if not isinstance(value, str) or not 1 <= len(value) <= 512:
        raise SourceConflict("Paste the new Google Sheets link for each displayed role.")
    text = value.strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{6,128}", text):
        return text
    try:
        url = urlsplit(text)
        match = re.fullmatch(
            r"/spreadsheets/d/([A-Za-z0-9_-]{6,128})(?:/(?:edit|view|preview|copy))?/?", url.path
        )
        if (
            url.scheme == "https"
            and url.hostname == "docs.google.com"
            and url.port is None
            and url.username is None
            and url.password is None
            and match
        ):
            return match.group(1)
    except ValueError:
        pass
    raise SourceConflict(
        "Use a Google Sheets link beginning https://docs.google.com/spreadsheets/d/."
    )


def replacement_owners(registration, targets):
    value = registration.value()
    pools = [p for p in value["pools"] if set(targets) & {p["index_file_id"], *p["slot_file_ids"]}]
    return sorted({p["owner_email"] for p in (pools or value["pools"])})


def replacement_fields(registration, targets):
    value = registration.value()
    roles = {}
    configuration = set(value["legacy_configuration"]["config"]["destinations"])
    for pool in value["pools"]:
        roles[pool["index_file_id"]] = "Report index"
        for ordinal, file_id in enumerate(pool["slot_file_ids"], 1):
            roles[file_id] = f"Report slot {ordinal}"
    for kind in ("scan_data", "all_kvk"):
        scope = value["legacy_configuration"][kind]
        for title, file_id in scope.get("spreadsheets", {}).items():
            roles.setdefault(file_id, str(title))
        for ordinal, file_id in enumerate(scope["destinations"], 1):
            roles.setdefault(file_id, f"{kind.replace('_', ' ')} output {ordinal}")
    fields = [
        dict(
            key="owner_email",
            label="Owner of the new spreadsheets",
            max_length=254,
            placeholder="Owner email shown below",
            help="Create the files under one of these registered owners: "
            + ", ".join(replacement_owners(registration, targets)),
        )
    ]
    for old in targets:
        from services.export_replacement_configuration import CONFIGURATION_TABS

        preparation = (
            "Create a fresh spreadsheet. Copy these configuration tabs as values from your verified settings: "
            + ", ".join(CONFIGURATION_TABS)
            + ". Preserve UK date formatting, keep one blank Sheet1 for output, and remove old report tabs. Each tab must have at most 50,000 cells. "
            if old in configuration
            else "Create a new spreadsheet with one blank worksheet named Sheet1; keep it at 50,000 cells or fewer. "
        )
        policy = value.get("legacy_file_access", {}).get(old)
        pool = next(
            (p for p in value["pools"] if old in {p["index_file_id"], *p["slot_file_ids"]}), None
        )
        audience = (
            policy["audience"]
            if policy
            else "anyone_reader" if pool and pool["audience"] == "public_viewer" else "private"
        )
        editors = policy["editors"] if policy else [value["service_account_email"]]
        fields.append(
            dict(
                key=old,
                label=(
                    "Configuration and report workbook"
                    if old in configuration
                    else roles.get(old, "Output spreadsheet")[:45]
                ),
                max_length=512,
                placeholder="Paste the NEW Google Sheets link",
                help=(
                    f"Replaces [this old output](https://docs.google.com/spreadsheets/d/{old}/edit). "
                    + preparation
                    + f"Editors: {', '.join(editors)}. Sharing: {audience.replace('_', ' ')}. "
                    "The bot checks the owner, permissions and all cells before using it."
                ),
            )
        )
    return fields


def replacement_input(registration, targets, payload):
    if not isinstance(payload, dict) or set(payload) != {"owner_email", *targets}:
        raise SourceConflict("Complete every replacement role and owner field.")
    owner = payload["owner_email"]
    if owner not in replacement_owners(registration, targets):
        raise SourceConflict("Choose one of the displayed registered owners.")
    mapping = {old: file_identity(payload[old]) for old in targets}
    if len(set(mapping.values())) != len(mapping):
        raise SourceConflict("Each replacement role needs a different fresh spreadsheet.")
    return owner, mapping
