"""Offline preflight for a resolved DEV profile. This module grants no launch authority."""

import hashlib
import hmac
import json
import re


class AdmissionError(ValueError):
    """Carries only a fixed diagnostic suitable for a commissioning receipt."""


def _unique_object(pairs):
    values = {}
    for key, value in pairs:
        if key in values:
            raise AdmissionError("duplicate_field")
        values[key] = value
    return values


def _object(raw):
    if type(raw) is not bytes or not 0 < len(raw) <= 16384:
        raise AdmissionError("invalid_input")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise AdmissionError("invalid_json") from None
    if type(value) is not dict:
        raise AdmissionError("invalid_profile")
    return value


def _fields(value, names):
    if type(value) is not dict or set(value) != set(names):
        raise AdmissionError("unexpected_fields")


def validate_offline_profile(policy_bytes, protected_digest, resolved_bytes):
    """Compare pre-resolved bindings with the release digest supplied by the protected caller.

    The caller owns policy custody and OS identity collection. A successful return is
    evidence for an offline check only. No credentials or connection strings are inputs.
    """
    if type(protected_digest) is not str or not re.fullmatch("[0-9a-f]{64}", protected_digest):
        raise AdmissionError("invalid_pin")
    expected = _object(policy_bytes)
    if not hmac.compare_digest(hashlib.sha256(policy_bytes).hexdigest(), protected_digest):
        raise AdmissionError("policy_drift")
    _fields(expected, ("mode", "guest", "principal", "sql", "discord", "google", "features"))
    if expected["mode"] != "dev-offline" or expected["features"] != []:
        raise AdmissionError("offline_required")
    sql, discord, google = (expected[k] for k in ("sql", "discord", "google"))
    _fields(sql, ("address", "port", "instance", "database", "auth", "tls"))
    _fields(discord, ("guild", "application"))
    _fields(google, ("project", "service_account", "spreadsheet_ids"))
    for val in (expected["guest"], expected["principal"], sql["instance"], sql["database"],
                google["project"], google["service_account"]):
        if type(val) is not str or not val.strip():
            raise AdmissionError("missing_binding")
    if (sql["address"] != "127.0.0.1" or type(sql["port"]) is not int
            or not 1 <= sql["port"] <= 65535 or sql["auth"] != "windows"
            or sql["tls"] != "verify-certificate"):
        raise AdmissionError("sql_binding")
    if any(type(v) is not str or not re.fullmatch("[1-9][0-9]{0,19}", v)
           for v in discord.values()):
        raise AdmissionError("discord_binding")
    ids = google["spreadsheet_ids"]
    if (type(ids) is not list or not ids
            or any(type(v) is not str or not re.fullmatch("[A-Za-z0-9_-]+", v) for v in ids)
            or len(set(ids)) != len(ids)):
        raise AdmissionError("google_binding")

    resolved = _object(resolved_bytes)
    # Compare serialized JSON so Python's True == 1 and 1.0 == 1 cannot admit type drift.
    if json.dumps(resolved, sort_keys=True) != json.dumps(expected, sort_keys=True):
        raise AdmissionError("resolved_drift")
