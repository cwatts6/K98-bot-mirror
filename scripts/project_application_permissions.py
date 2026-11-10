"""Offline release preparation: preserve native permission order within each object.

The reader uses BIN2 for ObjectName, but the database collation for permission
and subentity names. Python sorting those inner fields changes the protected
fingerprint. This helper adds only independently qualified new object groups;
it cannot validate or authorize live grants, installation, or a release.
"""

from copy import deepcopy

from kvk.dal.new_source_import_dal import digest

FIELDS = {
    "schema_permissions": {"SchemaName", "PermissionName", "Subentity"},
    "object_permissions": {"ObjectName", "PermissionName", "Subentity"},
    "column_permissions": {"ObjectName", "ColumnName", "PermissionName", "Allowed"},
}


def project_new_object_permissions(before, additions, *, before_sha256, new_objects):
    """Merge reviewed new groups without reordering any native within-group rows.

    Inputs must come from the same qualified reader/collation and principal.
    The caller still verifies the native candidate against the returned hash.
    BMP object names cover the reviewed catalogue; other names require separate
    qualification of SQL binary ordering, not an inferred Python sort order.
    """
    if digest(before).hex() != before_sha256:
        raise ValueError("Protected predecessor permission fingerprint differs")
    if not isinstance(new_objects, (set, frozenset)) or not new_objects:
        raise ValueError("Explicit nonempty new object set required")
    for snapshot in (before, additions):
        if not isinstance(snapshot, dict) or set(snapshot) != set(FIELDS):
            raise ValueError("Complete native permission sections required")
        for section, fields in FIELDS.items():
            rows = snapshot[section]
            if not isinstance(rows, list):
                raise ValueError("Native permission rows required")
            seen = set()
            for row in rows:
                if not isinstance(row, dict) or set(row) != fields:
                    raise ValueError("Exact native permission row shape required")
                for field in fields - {"Allowed"}:
                    if not isinstance(row[field], str):
                        raise ValueError("Native permission names must be strings")
                if "Allowed" in row and (
                    type(row["Allowed"]) is not int or row["Allowed"] not in (0, 1)
                ):
                    raise ValueError("Known native column permission required")
                identity = tuple(row[field] for field in sorted(fields))
                if identity in seen:
                    raise ValueError("Duplicate native permission row")
                seen.add(identity)
            if section != "schema_permissions":
                names = [row["ObjectName"] for row in rows]
                if any(not n or any(ord(c) > 0xFFFF for c in n) for n in names):
                    raise ValueError("Object name ordering requires native qualification")
                if names != sorted(names):
                    raise ValueError("Native BIN2 object group order required")
    if additions["schema_permissions"] != before["schema_permissions"]:
        raise ValueError("Schema permission evidence differs")
    if {row["ObjectName"] for row in additions["object_permissions"]} != new_objects:
        raise ValueError("Exact new object evidence required")
    result = deepcopy(before)
    for section in ("object_permissions", "column_permissions"):
        if any(row["ObjectName"] in new_objects for row in before[section]):
            raise ValueError("New object overlaps protected predecessor")
        if any(row["ObjectName"] not in new_objects for row in additions[section]):
            raise ValueError("Unreviewed object in native additions")
        # Stable sort ONLY the binary object key. Do not sort PermissionName,
        # Subentity or ColumnName: their native row order is already evidence.
        result[section] = sorted(
            deepcopy(before[section] + additions[section]), key=lambda row: row["ObjectName"]
        )
    return result
