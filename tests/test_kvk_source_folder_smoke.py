"""Offline boundaries of the disposable local transport; never connect to SQL."""

from unittest.mock import Mock

import pytest

from scripts import smoke_kvk_source_intake as smoke


def test_wrong_target_rejected_before_connect(monkeypatch):
    connect = Mock(side_effect=AssertionError("must not connect"))
    monkeypatch.setattr(smoke, "connect", connect)
    with pytest.raises(ValueError, match="exact approved"):
        smoke.FolderIntake("production|real")
    connect.assert_not_called()


@pytest.mark.parametrize("name", ["../outside.xlsx", "C:/elsewhere.xlsx", "notes.txt"])
def test_inbox_escape_and_other_extensions_rejected(tmp_path, name):
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    (tmp_path / "outside.xlsx").write_bytes(b"synthetic")
    (inbox / "notes.txt").write_bytes(b"synthetic")
    with pytest.raises((ValueError, FileNotFoundError)):
        smoke.read_workbook(inbox, name)


def test_bounded_read_and_empty_rejection(tmp_path, monkeypatch):
    monkeypatch.setattr(smoke, "MAX_BYTES", 8)
    path = tmp_path / "input.xlsx"
    for content in (b"", b"123456789"):
        path.write_bytes(content)
        with pytest.raises(ValueError, match="Workbook must contain"):
            smoke.read_workbook(tmp_path, path.name)
    path.write_bytes(b"12345678")
    assert smoke.read_workbook(tmp_path, path.name) == (path.name, b"12345678")


def test_all_paths_prevalidated_before_first_receipt(tmp_path, monkeypatch):
    (tmp_path / "inbox").mkdir()
    (tmp_path / "inbox" / "valid.xlsx").write_bytes(b"synthetic")
    monkeypatch.setattr(smoke, "ROOT", tmp_path)
    adapter = object.__new__(smoke.FolderIntake)
    adapter.intake = Mock()
    with pytest.raises(FileNotFoundError):
        adapter.upload(900001, ["valid.xlsx", "missing.xlsx"])
    adapter.intake.stage_upload.assert_not_called()


def test_upload_identity_bounds_and_shared_message(tmp_path, monkeypatch):
    (tmp_path / "inbox").mkdir()
    for name in ("players.xlsx", "totals.xlsx"):
        (tmp_path / "inbox" / name).write_bytes(b"synthetic")
    monkeypatch.setattr(smoke, "ROOT", tmp_path)
    adapter = object.__new__(smoke.FolderIntake)
    adapter.intake = Mock()
    adapter.record = Mock()
    adapter.upload(900001, ["totals.xlsx", "players.xlsx"])
    calls = adapter.intake.stage_upload.call_args_list
    assert calls[0].kwargs["message_id"] == calls[1].kwargs["message_id"]
    for call in calls:
        assert len(call.kwargs["message_id"]) <= 32
        assert len(call.kwargs["attachment_id"]) <= 32
        assert call.kwargs["season"] == 900001
    assert [call.kwargs["filename"] for call in calls] == ["totals.xlsx", "players.xlsx"]


def test_confirmation_cannot_be_implied_or_change_version():
    adapter = object.__new__(smoke.FolderIntake)
    adapter.intake = Mock()
    adapter.reviews = Mock()
    for phrase in ("yes", "CONFIRM SYNTHETIC receipt id 1"):
        with pytest.raises(ValueError, match="Explicit confirmation"):
            adapter.confirm("receipt", "id", 2, phrase)
    adapter.intake.confirm.assert_not_called()
    adapter.reviews.confirm.assert_not_called()


def test_retargeted_connection_closed(monkeypatch):
    import pyodbc

    connection = Mock()
    connection.cursor.return_value.execute.return_value.fetchone.return_value = (
        smoke.SERVER,
        "unexpected_database",
    )
    monkeypatch.setattr(pyodbc, "connect", Mock(return_value=connection))
    with pytest.raises(RuntimeError, match="Unexpected disposable SQL identity"):
        smoke.connect()
    connection.close.assert_called_once()
    connection.commit.assert_not_called()
