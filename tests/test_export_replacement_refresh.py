"""Concurrent registration changes must return an actionable guided refresh."""

from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

from services.export_replacement_workflow import ReplacementWorkflow
from services.export_runtime_composition import RuntimeRegistration
from tests.test_export_runtime_composition import registration_fixture


def workflow(*, checking=False):
    registration = registration_fixture()
    newer = deepcopy(registration)
    newer["pools"][0]["owner_email"] = "other-registered-owner@example.com"
    original, current = RuntimeRegistration(registration), RuntimeRegistration(newer)
    key = str(uuid4())
    proposals = SimpleNamespace(
        registration=original,
        containment=SimpleNamespace(
            inspect=lambda _: dict(
                outcome="targets_isolated",
                token="sealed-isolation",
                targets=["legacy-scan_data"],
                actor="recovery:" + str(uuid4()),
                reason="Original decision",
            )
        ),
        dal=SimpleNamespace(for_job=lambda *a, **k: ["proposal"]),
        inspect=lambda _: dict(
            mapping={"legacy-scan_data": "fresh-unused-output"}, replacement_id="proposal"
        ),
    )
    # Keep the original receipt stable across every independent review.
    isolated = proposals.containment.inspect(key)
    proposals.containment.inspect = lambda _: isolated
    checked = dict(state="checking" if checking else "verified", can_finish=False)
    verification = SimpleNamespace(
        dal=SimpleNamespace(list_for_plan=lambda *a, **k: ["check"]), inspect=lambda _: checked
    )
    writer = SimpleNamespace(registration=current, propose=Mock())
    result = ReplacementWorkflow(
        proposals=proposals,
        verification=verification,
        activation=SimpleNamespace(dal=SimpleNamespace(chain=lambda _: [])),
        plan_factory=Mock(),
        continuation=Mock(),
        proposal_writer=writer,
    )
    return result, key, writer


def test_stale_verified_proposal_offers_form_and_cannot_activate_over_other_recovery():
    service, key, writer = workflow()
    evidence, token, resolved = service.inspect(key)
    assert not resolved
    assert evidence["outcome"] == "refresh_replacement_choices"
    assert set(evidence["actions"]) == {"choose_replacements"}
    fields = service.input_fields(key, "choose_replacements", token)
    assert "other-registered-owner@example.com" in fields[0]["help"]
    payload = dict(
        owner_email="other-registered-owner@example.com",
        **{"legacy-scan_data": "fresh-unused-output"},
    )
    assert "fresh spreadsheets" in service.validate_input(
        key, "choose_replacements", token, payload
    )
    actor = "recovery:" + str(uuid4())
    service.execute(
        key, "choose_replacements", token, actor, "Reviewed current registration", payload=payload
    )
    assert writer.propose.call_args.kwargs["replacements"] == {
        "legacy-scan_data": "fresh-unused-output"
    }


def test_active_read_must_be_discarded_before_refreshing_choices():
    service, key, writer = workflow(checking=True)
    evidence, _, resolved = service.inspect(key)
    assert not resolved
    assert evidence["outcome"] == "checking_replacements"
    assert "discard_replacement_check" in evidence["actions"]
    assert "choose_replacements" not in evidence["actions"]
    writer.propose.assert_not_called()
