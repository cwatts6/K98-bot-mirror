# tests/test_file_utils_lockinfo.py
import os

from file_utils import get_lockfile_info


def test_get_lockfile_info_parses_pid_and_content(tmp_path):
    lock_path = os.path.join(str(tmp_path), "test.lock")
    # Write simulated lockfile with pid in first line and additional content
    with open(lock_path, "w", encoding="utf-8") as f:
        f.write("12345\nheld-by-test\n")

    info = get_lockfile_info(lock_path)
    assert isinstance(info, dict)
    assert info.get("content") is not None
    # pid may not be alive on CI, but should be parsed as int
    assert info.get("pid") == 12345
    assert "held-by-test" in info.get("content")
    # pid_alive key present (bool)
    assert "pid_alive" in info
