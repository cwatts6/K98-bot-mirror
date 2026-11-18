"""Order independently derived contract rows exactly like the SQL observer.

Qualification helper only. It does not read catalogues, install SQL, publish a
contract, or change which metadata rows are expected. The P0a target database
uses Latin1_General_CI_AS; ObjectName alone has the observer's BIN2 override.
"""

from collections import Counter
import json


def order_dependencies(cursor, dependencies):
    return _ordered(
        cursor,
        dependencies,
        "SELECT value FROM OPENJSON(?) ORDER BY "
        "JSON_VALUE(value,'$.ObjectName') COLLATE Latin1_General_100_BIN2,"
        "CONVERT(int,JSON_VALUE(value,'$.MinorID')),"
        "JSON_VALUE(value,'$.ServerName') COLLATE Latin1_General_CI_AS,"
        "JSON_VALUE(value,'$.DatabaseName') COLLATE Latin1_General_CI_AS,"
        "JSON_VALUE(value,'$.SchemaName') COLLATE Latin1_General_CI_AS,"
        "JSON_VALUE(value,'$.EntityName') COLLATE Latin1_General_CI_AS,"
        "CONVERT(int,JSON_VALUE(value,'$.ReferencedMinorID'))",
    )


def order_object_permissions(cursor, permissions):
    return _ordered(
        cursor,
        permissions,
        "SELECT value FROM OPENJSON(?) ORDER BY "
        "JSON_VALUE(value,'$.ObjectName') COLLATE Latin1_General_100_BIN2,"
        "JSON_VALUE(value,'$.PermissionName') COLLATE Latin1_General_CI_AS,"
        "JSON_VALUE(value,'$.Subentity') COLLATE Latin1_General_CI_AS",
    )


def _ordered(cursor, expected, query):
    raw = json.dumps(expected, ensure_ascii=False, separators=(",", ":"))
    if not isinstance(expected, list) or len(expected) > 20000 or len(raw) > 16000000:
        raise ValueError("Bounded independently derived rows required.")
    cursor.execute(query, raw)
    ordered = [json.loads(row[0]) for row in cursor.fetchall()]

    def key(row):
        return json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":"))

    if Counter(map(key, ordered)) != Counter(map(key, expected)):
        raise ValueError("Ordering must preserve every expected row.")
    return ordered
