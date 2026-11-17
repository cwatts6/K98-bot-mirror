"""Deploy only the qualified direct successor; retain every historic family."""

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


def blobs():
    result = {}
    for member in family()["members"]:
        path = member["path"]
        result["new", path] = (ROOT / path).read_bytes()
        if member["before_sha256"] is not None:
            for base in BASES:
                probe = subprocess.run(["git", "show", base + ":" + path], capture_output=True)
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
    assert len(items) == 92
    assert hashlib.sha256(json.dumps(items[:91], sort_keys=True).encode()).hexdigest() == (
        "ca56fa94f3921b714a07a63e94fc10c051f3869b1fdca8f962e7c051740ed92c"
    )
    assert {m["path"] for m in family()["members"]} == updater.P02_QUALIFIED_COMPATIBILITY_PATHS


def test_real_direct_source_pair_matches_qualified_family():
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
    assert original()[-1]["id"] == updater.P02_QUALIFIED_TRANSITION
