"""Qualify delivered ZIP members, not just the intermediate component collector."""

import hashlib
import io
import json
import random
from unittest.mock import Mock
import zipfile

import pytest

from services import operator_status_service as status, recovery_evidence_bundle as bundle
from services.recovery_service import RecoveryActor, SourceConflict
from tests.test_guided_recovery import ACTOR
from tests.test_recovery_report import report_service


def read_archive(report):
    assert hashlib.sha256(report["content"]).hexdigest() == report["sha256"]
    with zipfile.ZipFile(io.BytesIO(report["content"])) as archive:
        assert archive.testzip() is None
        members = {name: archive.read(name) for name in archive.namelist()}
    manifest = json.loads(members.pop("manifest.json"))
    for name, data in members.items():
        descriptor = manifest["components"][name]
        assert descriptor["bytes"] == len(data)
        assert descriptor["sha256"] == hashlib.sha256(data).hexdigest()
    for name, descriptor in manifest["components"].items():
        if descriptor["status"] == "available":
            assert name in members, f"Available component was not delivered: {name}"
    return members, manifest


@pytest.mark.parametrize("source", ["available", "unavailable", "oversize"])
def test_real_archive_delivers_every_collected_component(monkeypatch, source):
    projection = status.snapshot()
    getter = Mock(return_value=projection)
    if source == "unavailable":
        getter.side_effect = OSError("password=DO_NOT_EXPORT")
    elif source == "oversize":
        getter.return_value = {"rows": ["x" * 1000] * 30}
    monkeypatch.setattr(status, "snapshot", getter)
    monkeypatch.setattr(status, "check_sql", Mock(side_effect=AssertionError("No active check")))
    captured = {}
    collect = bundle.collect_components

    def capture(**kwargs):
        components, descriptors, identity = collect(**kwargs)
        captured.update(components)
        return components, descriptors, identity

    monkeypatch.setattr(bundle, "collect_components", capture)
    service, _, _ = report_service(3)
    ordinary = json.loads(service.download_report(ACTOR)["content"])
    report = service.download_complete_report(ACTOR)
    members, manifest = read_archive(report)
    assert report["complete"] and report["diagnostic_token"] is None
    assert set(captured) <= set(members)
    for name, data in captured.items():
        assert members[name] == data
    health = json.loads(members["health-observations.json"])
    coverage = manifest["components"]["health-observations.json"]
    assert coverage["schema"] == "health_observations_v1"
    if source == "available":
        assert health == ordinary["monitor"]["health_observations_v1"] == projection
        assert coverage["status"] == "available"
    else:
        assert coverage["status"] == "unavailable"
        assert coverage["reason"]
    assert b"DO_NOT_EXPORT" not in b"".join(members.values())
    assert len(json.loads(members["summary.json"])["groups"]) > 0
    assert len(members["incidents.jsonl"].splitlines()) == 3


def test_health_budget_omission_is_recoverable_without_displacing_existing_members(monkeypatch):
    rng = random.Random(13)
    health = bundle.encode({"retained": rng.randbytes(7000).hex()})
    diagnostics = bundle.encode({"retained": rng.randbytes(38000).hex()})
    components = {
        "startup.json": b"[]",
        "diagnostic-health.json": diagnostics,
        "operations.jsonl": b"",
        "health-observations.json": health,
    }
    descriptors = {name: {"status": "available"} for name in components}
    collect = Mock(return_value=(components, descriptors, {}))
    monkeypatch.setattr(bundle, "collect_components", collect)
    service, _, _ = report_service(0)
    initial = service.download_complete_report(ACTOR, max_bytes=65536)
    members, manifest = read_archive(initial)
    assert set(members) == {
        "incidents.jsonl",
        "summary.json",
        "startup.json",
        "diagnostic-health.json",
        "operations.jsonl",
    }
    descriptor = manifest["components"]["health-observations.json"]
    assert descriptor["status"] == "partial"
    assert descriptor["reason"] == "diagnostic_continuation"
    assert descriptor["sha256"] == bundle.sha(health)
    assert descriptor["bytes"] == len(health)
    assert manifest["diagnostic_continuation"] and initial["diagnostic_token"]
    assert len(initial["content"]) <= 65536
    token = initial["diagnostic_token"]
    with pytest.raises(SourceConflict):
        service.download_diagnostic_part(RecoveryActor(9, 2, 3), token, 65536)
    collect.side_effect = AssertionError("Continuation must not recollect")
    part = service.download_diagnostic_part(ACTOR, token, 65536)
    delivered, continuation = read_archive(part)
    assert delivered == {"health-observations.json": health}
    assert continuation["previous_sha256"] == initial["sha256"]
    assert continuation["components"]["health-observations.json"]["component_sha256"] == bundle.sha(
        health
    )
    assert part["diagnostic_token"] is None
    assert service.download_diagnostic_part(ACTOR, token, 65536) == part
    assert collect.call_count == 1
