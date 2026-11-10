"""Restore independently pinned predecessor grants in a local SQL reference fixture.

This qualification helper is never imported by deployment. The previous reference
fixture omitted six existing direct EXECUTE grants and therefore produced images
that disagreed with the complete application's installed permission contract.
"""

import hashlib
import json
import re

PREDECESSOR_PLAN_SHA256 = "2fbd9d05023090bd7c09730b3d2b25a16234c235faf103d51d98a6b5ed0aef3c"


def predecessor_grants(raw, affected_objects):
    """Select the exact 13 existing grants from the immutable predecessor plan."""
    if hashlib.sha256(raw).hexdigest() != PREDECESSOR_PLAN_SHA256:
        raise ValueError("Exact predecessor application grant plan required.")
    selected = [
        (row["object"], row["permission"])
        for row in json.loads(raw)["grants"]
        if row.get("object") in affected_objects
    ]
    if len(selected) != 13 or len(set(selected)) != 13:
        raise ValueError("Complete affected predecessor permission inventory required.")
    return selected


def install_reference_grants(connection, raw, affected_objects):
    """Change only the explicitly named development reference database."""
    selected = predecessor_grants(raw, affected_objects)
    server, database = connection.execute(
        "SELECT CONVERT(nvarchar(128),SERVERPROPERTY('ServerName')),DB_NAME()"
    ).fetchone()
    if server != "9SX2VF4\\K98DEV" or not re.fullmatch(
        r"K98_P0a_Migrations_[0-9a-f]{12}", database
    ):
        raise ValueError("Exact local disposable SQL reference required.")
    for name, permission in selected:
        if not re.fullmatch(r"(?:dbo|KVK)\.[A-Za-z_][A-Za-z0-9_]*", name) or permission not in {
            "SELECT",
            "INSERT",
            "UPDATE",
            "EXECUTE",
        }:
            raise ValueError("Unsupported predecessor grant.")
        connection.execute(
            "GRANT " + permission + " ON OBJECT::" + name + " TO S11_ExportApplication;"
        )
