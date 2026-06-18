# Consolidated unit tests for process_utils.py


import file_utils
import process_utils


# --- pid_alive tests -------------------------------------------------------
def test_pid_alive_non_positive():
    assert process_utils.pid_alive(-1) is False
    assert process_utils.pid_alive(0) is False


def test_coerce_pid_rejects_invalid():
    assert process_utils.pid_alive(None) is False
    assert process_utils.pid_alive("") is False
    assert process_utils.pid_alive("not_a_number") is False


def test_pid_alive_with_psutil_monkeypatch(monkeypatch):
    # Fake psutil with pid_exists behavior
    class FakePsutil:
        def pid_exists(self, pid):
            return pid == 12345

    monkeypatch.setattr(process_utils, "psutil", FakePsutil())
    assert process_utils.pid_alive(12345) is True
    assert process_utils.pid_alive(99999) is False


def test_pid_alive_falls_back_when_psutil_raises(monkeypatch):
    # psutil that raises from pid_exists
    class FakePsutil:
        def pid_exists(self, pid):
            raise RuntimeError("simulated psutil failure")

    monkeypatch.setattr(process_utils, "psutil", FakePsutil())

    # monkeypatch os.kill to emulate success (no exception)
    def fake_kill(pid, sig):
        return None

    monkeypatch.setattr(process_utils.os, "kill", fake_kill)
    assert process_utils.pid_alive(99999) is True


# --- get_process_info tests -----------------------------------------------
def test_get_process_info_with_psutil(monkeypatch):
    # Build fake psutil.Process
    class FakeProc:
        def __init__(self, pid):
            self._pid = pid

        def is_running(self):
            return True

        def exe(self):
            return "/usr/bin/fakeproc"

        def create_time(self):
            return 1000.0

    class FakePsutil:
        class NoSuchProcess(Exception):
            pass

        def pid_exists(self, pid):
            return True

        def Process(self, pid):
            if pid == 1:
                raise self.NoSuchProcess()
            return FakeProc(pid)

    monkeypatch.setattr(process_utils, "psutil", FakePsutil())
    info = process_utils.get_process_info(42)
    assert info["pid_exists"] is True
    assert info["is_running"] is True
    assert info["exe"] == "/usr/bin/fakeproc"
    assert info["create_time"] == 1000.0

    # When NoSuchProcess, is_running should be False but pid_exists True (as per fake)
    info2 = process_utils.get_process_info(1)
    assert info2["pid_exists"] is True
    assert info2["is_running"] is False


def test_get_process_info_fallback_to_os_kill_when_psutil_unreliable(monkeypatch):
    # Simulate psutil.pid_exists raising; ensure we fall back to os.kill via pid_alive
    class FakePsutil:
        def pid_exists(self, pid):
            raise RuntimeError("simulated psutil.pid_exists failure")

    monkeypatch.setattr(process_utils, "psutil", FakePsutil())

    # os.kill -> success (no exception)
    def fake_kill(pid, sig):
        return None

    monkeypatch.setattr(process_utils.os, "kill", fake_kill)
    info = process_utils.get_process_info("42")
    assert info["pid_exists"] is True
    assert info["is_running"] is True
    assert info["exe"] is None
    assert info["create_time"] is None


# --- matches_process tests -----------------------------------------------
def test_matches_process_exe_and_create_time(monkeypatch):
    # Build fake psutil.Process with exe and create_time
    class FakeProc:
        def __init__(self, pid, exe, ct):
            self._pid = pid
            self._exe = exe
            self._ct = ct

        def is_running(self):
            return True

        def exe(self):
            return self._exe

        def create_time(self):
            return self._ct

    class FakePsutil:
        class NoSuchProcess(Exception):
            pass

        def pid_exists(self, pid):
            return True

        def Process(self, pid):
            return FakeProc(pid, "/opt/bin/prog", 1000.0)

    monkeypatch.setattr(process_utils, "psutil", FakePsutil())

    # exe mismatch -> False
    assert process_utils.matches_process(123, exe_path="/different/path") is False

    # If proc create_time is 1000.0:
    # - created_before much smaller (500.0): proc_ct (1000) > created_before + 1 -> treat as PID reuse => no match (False)
    assert process_utils.matches_process(123, created_before=500.0) is False

    # - created_before equal or greater than proc_ct (1000.0): not considered newer -> match True
    assert process_utils.matches_process(123, created_before=1000.0) is True


def test_matches_process_realpath_normalisation(monkeypatch):
    # Prepare two representations that normalise to same realpath:
    proc_exe = "/usr/bin/../bin/python"
    expected_exe = "/usr/bin/python"

    # Monkeypatch get_process_info to return proc_exe and a create_time
    def fake_get_info(pid):
        return {"pid_exists": True, "is_running": True, "exe": proc_exe, "create_time": 1000.0}

    monkeypatch.setattr(process_utils, "get_process_info", fake_get_info)

    # realpath/normcase should treat these as equivalent strings (no filesystem check required)
    assert process_utils.matches_process(123, exe_path=expected_exe, created_before=2000.0) is True


# --- re-export checks -----------------------------------------------------
def test_file_utils_reexports():
    # file_utils should expose the same functions (re-export or wrapper)
    assert getattr(file_utils, "pid_alive", None) is not None
    assert getattr(file_utils, "get_process_info", None) is not None
    assert getattr(file_utils, "matches_process", None) is not None
