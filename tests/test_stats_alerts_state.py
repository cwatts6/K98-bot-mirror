import json

import stats_alerts.state as state_mod


def _point_state_at(monkeypatch, tmp_path):
    path = tmp_path / "stats_alert_log.csv.state.json"
    monkeypatch.setattr(state_mod, "STATE_PATH", str(path))
    monkeypatch.setattr(state_mod, "_STATE_LOCK_PATH", f"{path}.lock")
    return path


def test_load_state_repairs_empty_file(monkeypatch, tmp_path, caplog):
    path = _point_state_at(monkeypatch, tmp_path)
    path.write_text("", encoding="utf-8")

    loaded = state_mod.load_state()

    assert loaded == {}
    assert json.loads(path.read_text(encoding="utf-8")) == {}
    assert "JSON decode failed" not in caplog.text


def test_load_state_repairs_whitespace_only_file(monkeypatch, tmp_path, caplog):
    path = _point_state_at(monkeypatch, tmp_path)
    path.write_text("  \n\t", encoding="utf-8")

    loaded = state_mod.load_state()

    assert loaded == {}
    assert json.loads(path.read_text(encoding="utf-8")) == {}
    assert "JSON decode failed" not in caplog.text


def test_load_state_preserves_valid_state(monkeypatch, tmp_path):
    path = _point_state_at(monkeypatch, tmp_path)
    original = '{\n  "prekvk_msg_id": 123\n}'
    path.write_text(original, encoding="utf-8")

    loaded = state_mod.load_state()

    assert loaded == {"prekvk_msg_id": 123}
    assert path.read_text(encoding="utf-8") == original


def test_message_patch_preserves_unrelated_unicode_and_compares_identity(monkeypatch, tmp_path):
    path = _point_state_at(monkeypatch, tmp_path)
    path.write_text('{"other":"é", "prekvk_msg_id":123}', encoding="utf-8")
    assert not state_mod.update_prekvk_message(None, expected_id=99)
    assert state_mod.update_prekvk_message(124, expected_id=123)
    assert state_mod.load_state() == {"other": "é", "prekvk_msg_id": 124}
    assert "é" in path.read_text(encoding="utf-8")
    assert state_mod.update_prekvk_message(None, expected_id=124)
    assert state_mod.load_state() == {"other": "é"}


def test_strict_patch_surfaces_error_without_destroying_evidence(monkeypatch, tmp_path):
    import pytest

    path = _point_state_at(monkeypatch, tmp_path)
    path.write_text("{", encoding="utf-8")
    with pytest.raises(ValueError):
        state_mod.update_prekvk_message(123)
    assert path.read_text(encoding="utf-8") == "{"
