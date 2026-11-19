"""Recovery-only snapshots and atomic preservation checks on the installed DAL."""

from contextlib import contextmanager
from copy import deepcopy

from kvk.dal.new_source_import_dal import SourceConflict, rows, transaction
from kvk.dal.source_output_pool_dal import _wire
from services.export_coordination_dal import ExportCoordinationDAL, identity


class StrandedExportRecoveryDAL(ExportCoordinationDAL):
    def __init__(self, closeout_dal):
        super().__init__(
            closeout_dal.connect, preparations=True, output_operations=True, execution_evidence=True
        )
        self.closeout_dal = closeout_dal
        self.expected_state = None

    def _snapshot(self, cursor, job_id):
        state = self.closeout_dal._snapshot(cursor, identity(job_id))
        cursor.execute(
            "SELECT p.* FROM dbo.ExportAttemptPart p WITH (UPDLOCK,HOLDLOCK) "
            "JOIN dbo.ExportAttempt a WITH (UPDLOCK,HOLDLOCK) ON a.AttemptID=p.AttemptID "
            "WHERE a.JobID=? ORDER BY a.AttemptID,p.PartNo",
            identity(job_id),
        )
        state["attempt_parts"] = _wire(rows(cursor))
        return state

    def snapshot(self, job_id):
        with transaction(self.connect) as cursor:
            return self._snapshot(cursor, job_id)

    @contextmanager
    def _owned(self, claim):
        with super()._owned(claim) as (cursor, job):
            if (
                self.expected_state is None
                or self._snapshot(cursor, claim.job_id) != self.expected_state
            ):
                raise SourceConflict("Reviewed recovery history changed before settlement.")
            yield cursor, job

    def fail_reviewed(self, claim, expected):
        if self.expected_state is not None:
            raise SourceConflict("Recovery settlement is already active.")
        self.expected_state = deepcopy(expected)
        try:
            self.fail(claim, retain_claims=True)
        finally:
            self.expected_state = None
