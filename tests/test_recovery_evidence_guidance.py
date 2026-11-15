"""Unknown ownership must lead to evidence collection, never a release shortcut."""

import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from services.producer_refusal_recovery import ProducerRefusalRecovery
from services.queue_admission_recovery import QueueAdmissionRecovery


def test_unsupported_queue_owner_has_concrete_collection_steps_without_action():
    state = dict(
        preparation=dict(
            RequestJson=json.dumps({"request": {}}),
            GenerationJson=None,
            State="uncertain",
            Version=3,
            ConsumerKind="unknown",
            EnqueueSequence=4,
            CreatedUTC="2026-10-21",
            RequestHash="a" * 64,
        ),
        counts={"streams": 1},
    )
    dal = SimpleNamespace(
        snapshot=lambda _: state,
        eligible=lambda _: False,
        withdrawn_read=lambda *a, **k: False,
        configuration_read_continuation_candidate=lambda _: False,
    )
    evidence, _, resolved = QueueAdmissionRecovery(dal).inspect("saved")
    assert not resolved and not evidence["actions"] and not evidence["recovery_links"]
    assert "read-only SQL" in " ".join(evidence["required_evidence"])
    assert "linked operation" not in evidence["failure_context"]["summary"]


@pytest.mark.parametrize("mapped", [False, True])
def test_mixed_unattributed_hold_keeps_guidance_even_with_another_link(mapped):
    blocker = dict(
        ResourceKey="snapshot",
        ActiveOutputOperationID=None,
        ActiveJobID=None,
        ActivePreparationID=None,
        ConsumerKind=None,
    )
    blockers = [blocker]
    if mapped:
        blockers.append(dict(blocker, ActiveJobID="known-job"))
    state = dict(
        attempts=[],
        original_phase="refused",
        blockers=blockers,
        preparation=dict(
            RequestJson=json.dumps({"request": {"config": {}}}), CreatedUTC="2026-10-21"
        ),
        current_registration={},
        producer={"inputs": dict(metadata={}, completed_filename="retained.csv", rank=1, seed=1)},
    )
    evidence, _, resolved = ProducerRefusalRecovery(
        SimpleNamespace(snapshot=lambda _: state), Mock()
    ).inspect("saved")
    assert not resolved
    assert set(evidence["actions"]) == {"cancel_saved_stage"}
    assert "owner, fence and version" in " ".join(evidence["required_evidence"])
    assert bool(evidence["recovery_links"]) is mapped
