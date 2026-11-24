import copy
import hashlib
import json
import unittest

from dev_offline_admission import AdmissionError, validate_offline_profile


class OfflineProfileTests(unittest.TestCase):
    def setUp(self):
        self.profile = {
            "mode": "dev-offline", "guest": "fixture-vm", "principal": "fixture-runner",
            "sql": {"address": "127.0.0.1", "port": 14330, "database": "fixture",
                    "instance": "fixture", "auth": "windows", "tls": "verify-certificate"},
            "discord": {"guild": "101", "application": "102"},
            "google": {"project": "fixture", "service_account": "runner@example.invalid",
                       "spreadsheet_ids": ["sheet-fixture"]},
            "features": [],
        }
        self.raw = json.dumps(self.profile).encode()
        self.pin = hashlib.sha256(self.raw).hexdigest()

    def test_pinned_offline_profile(self):
        validate_offline_profile(self.raw, self.pin, self.raw)

    def test_changed_bindings_hold_without_disclosing_input(self):
        for group, key, value in (
            ("sql", "address", "foreign.invalid"), ("sql", "database", "foreign"),
            ("sql", "tls", "trust-any"), ("sql", "dsn", "synthetic-canary"),
            ("discord", "guild", "103"), ("discord", "application", "104"),
            ("google", "spreadsheet_ids", ["foreign"]), ("google", "project", "foreign"),
            ("google", "service_account", "other@example.invalid"),
            (None, "principal", "foreign"), (None, "guest", "foreign"),
            (None, "features", ["calendar"]), (None, "token", "synthetic-canary"),
        ):
            with self.subTest(key=key):
                changed = copy.deepcopy(self.profile)
                (changed if group is None else changed[group])[key] = value
                with self.assertRaisesRegex(AdmissionError, "^resolved_drift$"):
                    validate_offline_profile(self.raw, self.pin, json.dumps(changed).encode())

    def test_bad_pin_missing_policy_and_duplicate_fields(self):
        for policy, pin in ((self.raw, "0" * 64), (b"", self.pin),
                            (b'{"mode":1,"mode":2}', self.pin)):
            with self.subTest(policy_size=len(policy)), self.assertRaises(AdmissionError):
                validate_offline_profile(policy, pin, self.raw)
