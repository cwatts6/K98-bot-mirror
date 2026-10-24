"""Retained Windows handles for an administrator's exact private writer birth."""

import hashlib
from pathlib import PureWindowsPath

from core.export_child_lifecycle import validate_host_birth
from core.export_execution_host import HostBoundaryError, current_sid, machine_identity
from core.export_process_identity import process_snapshot, verify_process_snapshot


class RecoveryHost:
    def __init__(self, authority_binding):
        self.binding = authority_binding

    def _birth(self, birth):
        validate_host_birth(birth)
        if birth["machine"] != machine_identity() or birth["authority_sid"] != current_sid():
            raise HostBoundaryError("Writer birth is outside this host and Windows identity.")

    def retain(self, birth):
        self._birth(birth)
        return RetainedWriter(birth, self.binding)

    def verify_terminated(self, birth, receipt):
        """Recheck an immutable earlier handle observation; never reopen a PID."""
        import pywintypes
        import win32job

        self._birth(birth)
        if (
            receipt.get("child_id") != birth["child_id"]
            or receipt.get("pid") != birth["pid"]
            or receipt.get("job_name_sha256")
            != hashlib.sha256(birth["job_name"].encode()).hexdigest()
            or receipt.get("job_empty") is not True
            or receipt.get("process_signaled") is not True
        ):
            raise HostBoundaryError("Saved exact-child termination receipt differs.")
        try:
            job = win32job.OpenJobObject(0x0004, False, birth["job_name"])
        except pywintypes.error as error:
            if error.winerror != 2:
                raise HostBoundaryError("Retained named job is inaccessible.") from error
            return
        try:
            if (
                win32job.QueryInformationJobObject(job, 9)["BasicLimitInformation"]["LimitFlags"]
                != 0x2000
                or win32job.QueryInformationJobObject(job, 1)["ActiveProcesses"] != 0
            ):
                raise HostBoundaryError("Retained named job is not empty and contained.")
        finally:
            job.Close()


class RetainedWriter:
    def __init__(self, birth, binding):
        self.birth, self.binding = birth, binding
        self.job = self.process = self.observed = None

    def __enter__(self):
        import win32api
        import win32job

        try:
            self.job = win32job.OpenJobObject(0x0004 | 0x0008, False, self.birth["job_name"])
            self.process = win32api.OpenProcess(0x1000 | 0x100000, False, self.birth["pid"])
            self.observed = process_snapshot(self.process)
            if (
                self.observed["pid"] != self.birth["pid"]
                or self.observed["token_profile"] != self.binding["token_profile"]
                or PureWindowsPath(self.observed["executable"])
                != PureWindowsPath(self.binding["executable"])
                or self.observed["sha256"] != self.binding["sha256"]
                or self.observed["created_filetime"] < self.binding["created_filetime"]
            ):
                raise HostBoundaryError("Private writer process does not match its authority.")
            self.inspect()
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def inspect(self):
        import win32job

        verify_process_snapshot(process_snapshot(self.process), self.observed)
        accounting = win32job.QueryInformationJobObject(self.job, 1)
        # The original execution host deliberately contains descendants in the
        # same named job. Positive membership of the pinned writer, unchanged
        # no-breakaway limits and an empty job after termination are the boundary;
        # child count is not process identity.
        if (
            not win32job.IsProcessInJob(self.process, self.job)
            or accounting["ActiveProcesses"] < 1
            or win32job.QueryInformationJobObject(self.job, 9)["BasicLimitInformation"][
                "LimitFlags"
            ]
            != 0x2000
        ):
            raise HostBoundaryError(
                "Exact writer containment is unproven: "
                f"active={accounting['ActiveProcesses']} total={accounting['TotalProcesses']} "
                f"member={win32job.IsProcessInJob(self.process, self.job)} "
                f"limits={win32job.QueryInformationJobObject(self.job, 9)['BasicLimitInformation']['LimitFlags']}"
            )

    def terminate_and_observe(self):
        import win32event
        import win32job

        self.inspect()
        win32job.TerminateJobObject(self.job, 1)
        if (
            win32event.WaitForSingleObject(self.process, 30000) != 0
            or win32job.QueryInformationJobObject(self.job, 1)["ActiveProcesses"] != 0
        ):
            raise HostBoundaryError("Exact writer termination has not been observed.")
        return dict(
            child_id=self.birth["child_id"],
            pid=self.birth["pid"],
            process_signaled=True,
            job_empty=True,
            job_name_sha256=hashlib.sha256(self.birth["job_name"].encode()).hexdigest(),
            observed_process=self.observed,
        )

    def __exit__(self, *_):
        for name in ("process", "job"):
            handle = getattr(self, name)
            if handle is not None:
                handle.Close()
                setattr(self, name, None)
