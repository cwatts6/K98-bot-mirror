from datetime import datetime, timedelta
import json

from offload_monitor_lib import rotate_registry_file


def _make_registry(path, count=10, older_than_days=0):
    data = {}
    now = datetime.utcnow()
    for i in range(count):
        start = (now - timedelta(days=(older_than_days + i))).isoformat()
        end = (now - timedelta(days=(older_than_days + i - 0.5))).isoformat()
        off = {
            "offload_id": f"id{i}",
            "start_time": start,
            "end_time": end,
            "status": "completed",
            "pid": None,
        }
        data[off["offload_id"]] = off
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return data


def test_rotate_removes_old_entries(tmp_path):
    p = tmp_path / "offload_registry.json"
    _make_registry(str(p), count=6, older_than_days=31)
    res = rotate_registry_file(str(p), retention_days=30, max_entries=100)
    assert res["before_count"] == 6
    assert res["after_count"] == 0 or res["after_count"] < 6


def test_rotate_respects_max_entries(tmp_path):
    p = tmp_path / "offload_registry.json"
    _make_registry(str(p), count=50, older_than_days=0)
    res = rotate_registry_file(str(p), retention_days=365, max_entries=10)
    assert res["after_count"] <= 10
