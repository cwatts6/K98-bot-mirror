from uuid import UUID, uuid4

import pytest

from services.legacy_export_closeout_dal import _receipt_wire


@pytest.mark.parametrize("representation", [str, lambda x: str(x).upper(), UUID])
def test_sql_receipt_ids_match_private_json_without_changing_other_values(representation):
    identifier = str(uuid4())
    row = dict(
        ActionID=representation(identifier),
        ContainmentID=representation(identifier),
        ReceiptReference=representation(identifier),
        ReceiptHash=b"h" * 32,
        AccountKey="Case-Sensitive",
        Reason="Retain Original",
        FileID="AbC_123",
    )
    result = _receipt_wire(row)
    assert all(result[k] == identifier for k in ("ActionID", "ContainmentID", "ReceiptReference"))
    assert result["ReceiptHash"] == (b"h" * 32).hex()
    assert (result["AccountKey"], result["Reason"], result["FileID"]) == (
        "Case-Sensitive",
        "Retain Original",
        "AbC_123",
    )
    assert row["ActionID"] == representation(identifier)


def test_missing_optional_receipt_identity_remains_missing():
    assert _receipt_wire(None) is None
    assert _receipt_wire(dict(ContainmentID=None)) == dict(ContainmentID=None)


def test_invalid_receipt_identity_is_rejected():
    with pytest.raises(ValueError):
        _receipt_wire(dict(ReceiptReference="not-a-guid"))
