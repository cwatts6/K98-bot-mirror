"""Retain the qualified historical family through authenticated successors."""

import hashlib
import json
from pathlib import Path
import subprocess

import pytest

from scripts import prepare_k98_update as updater
from tests.test_p02_maintenance_update import (
    bot,  # noqa: F401
    test_complete_source_seed_start_readiness_packet_never_replays_sql as complete_packet,
)

ROOT = Path(__file__).resolve().parents[1]
BASES = ("729ece15c2dd665906525a4a457667d53516e805", "7491c71a945f6f961a3ca5a25698668ef8f19cfc")


def family():
    return next(
        t for t in updater.reviewed_transitions() if t["id"] == updater.P02_QUALIFIED_TRANSITION
    )


@pytest.fixture(autouse=True)
def authenticated_admission_successor(monkeypatch):
    """Keep this historical family test bound through the exact reviewed successor."""
    successors = [
        next(t for t in updater.reviewed_transitions() if t["id"] == identity)
        for identity in (updater.P02_VERIFICATION_TRANSITION, updater.P02_ADMISSION_TRANSITION)
    ]
    pairs = [
        {
            m["after_sha256"]: m["before_sha256"]
            for m in successor["members"]
            if m["before_sha256"] is not None
        }
        for successor in successors
    ]
    original = updater.sha256

    def historical_hash(raw):
        value = original(raw)
        for mapping in pairs:
            value = mapping.get(value, value)
        return value

    monkeypatch.setattr(updater, "sha256", historical_hash)


def blobs():
    result = {}
    for member in family()["members"]:
        path = member["path"]
        result["new", path] = (ROOT / path).read_bytes()
        if member["before_sha256"] is not None:
            for base in BASES:
                probe = subprocess.run(
                    ["git", "show", base + ":" + path], cwd=ROOT, capture_output=True
                )
                if probe.returncode == 0:
                    result["old", path] = probe.stdout
                    break
            else:
                pytest.fail(
                    "Retained predecessor unavailable; fetch full mirror or private history"
                )
    return result


def test_all_91_historical_families_unchanged():
    items = updater.reviewed_transitions()
    assert len(items) == 94
    assert hashlib.sha256(json.dumps(items[:91], sort_keys=True).encode()).hexdigest() == (
        "ca56fa94f3921b714a07a63e94fc10c051f3869b1fdca8f962e7c051740ed92c"
    )
    assert {m["path"] for m in family()["members"]} == updater.P02_QUALIFIED_COMPATIBILITY_PATHS


def test_authenticated_historical_pair_matches_qualified_family():
    data = blobs()
    assert updater.matches_protocol_transition(family(), lambda *k: data.get(k), "old", "new")
    for member in family()["members"]:
        assert (
            updater.check_protocol_transition(member["path"], lambda *k: data.get(k), "old", "new")
            == updater.P02_QUALIFIED_COMPATIBILITY_PATHS
        )


@pytest.mark.parametrize("path", sorted(updater.P02_QUALIFIED_COMPATIBILITY_PATHS))
@pytest.mark.parametrize("side", ["old", "new"])
def test_any_source_member_drift_refuses_complete_pair(path, side):
    data = blobs()
    data[side, path] = (data.get((side, path)) or b"") + b"\n# unexpected\n"
    assert not updater.matches_protocol_transition(family(), lambda *k: data.get(k), "old", "new")


def test_qualified_family_builds_complete_packet(tmp_path, monkeypatch, bot):  # noqa: F811
    # Reuse the complete source/seed/start/readiness harness with the exact new
    # family's shape; its installed authority and all seed checks remain real.
    original = updater.reviewed_transitions
    import tests.test_p02_maintenance_update as previous

    real_helper = previous.assert_complete_repair_packet

    def qualified(*args, **kwargs):
        value = kwargs["family"]
        value["id"] = updater.P02_QUALIFIED_TRANSITION
        for path in sorted(
            updater.P02_QUALIFIED_COMPATIBILITY_PATHS - updater.P02_MAINTENANCE_COMPATIBILITY_PATHS
        ):
            value["members"].append(
                dict(
                    path=path,
                    before_sha256=updater.sha256(b"old\n"),
                    after_sha256=updater.sha256(b"new\n"),
                )
            )
        return real_helper(*args, **kwargs)

    monkeypatch.setattr(previous, "assert_complete_repair_packet", qualified)
    complete_packet(tmp_path, monkeypatch, bot)
    assert original()[-3]["id"] == updater.P02_QUALIFIED_TRANSITION
    assert original()[-2]["id"] == updater.P02_ADMISSION_TRANSITION
    assert original()[-1]["id"] == updater.P02_VERIFICATION_TRANSITION
