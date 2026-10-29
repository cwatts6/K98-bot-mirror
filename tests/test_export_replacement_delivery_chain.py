"""The original incident follows verified replacement delivery across failures."""

from copy import deepcopy
import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from kvk.dal.new_source_import_dal import SourceConflict
from services.export_replacement_delivery import ReplacementDelivery


def fixture():
    receipts, snapshots = {}, {}
    snapshots["original"] = dict(
        job=dict(JobID="original", InputHash="original", ConsumerKind="scan_data")
    )
    for original, child, activation in (("original", "second", "a"), ("second", "third", "b")):
        receipts[original, activation] = dict(
            OriginalJobID=original,
            ReplacementJobID=child,
            ActivationID=activation,
            OriginalInputHash=original,
            ReplacementInputHash=child,
        )
        snapshots[child] = dict(
            job=dict(
                JobID=child,
                State="uncertain",
                InputHash=child,
                ConsumerKind="scan_data",
                ProvenanceJson=json.dumps(
                    dict(
                        replacement=dict(
                            original_job_id=original,
                            activation_id=activation,
                            original_input_sha256=original,
                        )
                    )
                ),
            ),
            isolated_targets=["old-output"],
        )
    verify = Mock()
    service = ReplacementDelivery(
        dal=SimpleNamespace(read=lambda job, activation, account: receipts.get((job, activation))),
        discovery=SimpleNamespace(account="account", job=lambda key: deepcopy(snapshots[key])),
        verify_delivery=verify,
        next_activation=lambda job: dict(activation_id="b") if job == "second" else None,
    )
    return service, receipts, snapshots, verify


def test_failed_replacement_keeps_original_open_then_closes_after_successor_verifies():
    service, _, snapshots, verify = fixture()
    result = service.inspect("original", dict(activation_id="a"))
    assert result["job_id"] == "third"
    assert not result["resolved"] and not result["actions"]
    verify.assert_not_called()
    snapshots["third"]["job"]["State"] = "confirmed"
    result = service.inspect("original", dict(activation_id="a"))
    assert result["resolved"] and result["job_id"] == "third"
    verify.assert_called_once()
    assert verify.call_args.args[1] == dict(activation_id="b")
    assert snapshots["second"]["job"]["State"] == "uncertain"


def test_chain_does_not_move_successor_buttons_to_original_incident():
    service, receipts, _, _ = fixture()
    del receipts["second", "b"]
    result = service.inspect("original", dict(activation_id="a"))
    assert not result["resolved"] and not result["actions"]
    assert result["job_id"] == "second"


def test_chain_rejects_changed_input_and_does_not_hide_failed_final_verification():
    service, receipts, snapshots, verify = fixture()
    receipts["second", "b"]["OriginalInputHash"] = "changed"
    with pytest.raises(SourceConflict, match="lineage"):
        service.inspect("original", dict(activation_id="a"))
    receipts["second", "b"]["OriginalInputHash"] = "second"
    snapshots["third"]["job"]["State"] = "confirmed"
    verify.side_effect = SourceConflict("Original private journal is missing")
    with pytest.raises(SourceConflict, match="journal"):
        service.inspect("original", dict(activation_id="a"))


def test_chain_rejects_cycles():
    service, receipts, snapshots, _ = fixture()
    receipts["second", "b"]["ReplacementJobID"] = "original"
    receipts["second", "b"]["ReplacementInputHash"] = "original"
    snapshots["original"] = dict(
        job=dict(
            JobID="original",
            State="uncertain",
            InputHash="original",
            ConsumerKind="scan_data",
            ProvenanceJson=json.dumps(
                dict(
                    replacement=dict(
                        original_job_id="second", activation_id="b", original_input_sha256="second"
                    )
                )
            ),
        ),
        isolated_targets=["old-output"],
    )
    service.next_activation = lambda job: dict(activation_id="a" if job == "original" else "b")
    with pytest.raises(SourceConflict, match="cyclic"):
        service.inspect("original", dict(activation_id="a"))


def test_each_hop_authenticates_its_input_and_final_content_uses_root_commitment():
    from services.export_replacement_authority import ReplacementAuthority
    from services.export_replacement_publication import legacy_content
    from tests.test_export_replacement_content import expected_hash, legacy_records

    service, _, snapshots, _ = fixture()
    for snapshot in snapshots.values():
        snapshot["job"].update(AccountKey="account", IntentID=None)
    snapshots["third"]["job"]["State"] = "confirmed"
    root = dict(
        snapshots["original"]["job"], ProvenanceJson=json.dumps(dict(output_sha256=expected_hash()))
    )
    intermediate = dict(
        snapshots["second"]["job"], ProvenanceJson=json.dumps(dict(output_sha256="c" * 64))
    )
    service.next_activation = lambda _: dict(activation_id="b", input_commitment=intermediate)
    authority = ReplacementAuthority.__new__(ReplacementAuthority)
    service.verify_input = Mock(wraps=authority.verify_input)
    records = legacy_records()

    def verify(snapshot, activation):
        commitment = authority.verify_input(snapshot, activation)
        assert commitment == root
        legacy_content(
            records,
            [{"old-file": "fresh-file"}],
            json.loads(commitment["ProvenanceJson"])["output_sha256"],
        )

    service.verify_delivery = Mock(side_effect=verify)
    activation = dict(activation_id="a", input_commitment=root)
    assert service.inspect("original", activation)["resolved"]
    assert [call.args[0]["job"]["JobID"] for call in service.verify_input.call_args_list] == [
        "second",
        "third",
    ]
    assert service.verify_delivery.call_args.args[1]["content_commitment"] == root
    records[2][0].arguments["body"]["values"][1][1] = "wrong final content"
    records[3][1]["values"][1][1] = "wrong final content"
    with pytest.raises(SourceConflict, match="original private input"):
        service.inspect("original", activation)
    intermediate["InputHash"] = "forged intermediate"
    service.verify_delivery.reset_mock()
    with pytest.raises(SourceConflict, match="original input commitment"):
        service.inspect("original", activation)
    service.verify_delivery.assert_not_called()
