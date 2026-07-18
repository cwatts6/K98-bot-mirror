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
