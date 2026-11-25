"""Pair each catalogue read with its existing boundary in one ODBC dispatch.

Only the candidate collector borrows this adapter. SQL text and bound values are
unchanged except for a trailing boundary EXEC. The full boundary parser still
checks every checkpoint. No ownership, deadline, transaction or cleanup moves
here, and no failed or partially consumed batch can be dispatched again.
"""

from services.catalogue_observation_dal import BOUNDARY_SQL, ObservationContractError


class CatalogueBatchCursor:
    """Consume both result sets before admitting the next catalogue batch.

    SQLMoreResults can discard unread rows. Check exhaustion explicitly before
    advancing, and require precisely the boundary result and its completion.
    The original cursor remains responsible for timeouts and physical custody.
    """

    def __init__(self, cursor):
        self._cursor = cursor
        self._mode = "idle"
        self._exhausted = False

    @property
    def connection(self):
        return self._cursor.connection

    @property
    def description(self):
        return self._cursor.description

    def _call(self, method, *args):
        try:
            return getattr(self._cursor, method)(*args)
        except BaseException:
            self._mode = "failed"
            raise

    def _refuse(self, message):
        self._mode = "failed"
        raise ObservationContractError(message)

    def execute(self, statement, *parameters):
        if self._mode in {"boundary", "failed"}:
            self._refuse("Previous catalogue batch has not completed successfully.")
        if statement == BOUNDARY_SQL:
            if parameters:
                self._refuse("The fixed observation boundary takes no parameters.")
            if self._mode == "data":
                if not self._exhausted and self._call("fetchone") is not None:
                    self._refuse("Catalogue rows remain unread before the boundary.")
                if not self._call("nextset"):
                    self._refuse("The catalogue batch is missing its boundary result.")
            else:
                self._call("execute", statement)
            self._mode = "boundary"
        else:
            if self._mode != "idle" or not isinstance(statement, str) or not statement.strip():
                self._refuse("Every catalogue read requires its completed checkpoint.")
            self._call("execute", statement + "\n;" + BOUNDARY_SQL, *parameters)
            self._mode = "data"
        self._exhausted = False
        return self

    def fetchone(self):
        if self._mode not in {"data", "boundary"}:
            self._refuse("No active catalogue result to consume.")
        result = self._call("fetchone")
        self._exhausted = result is None
        return result

    def fetchall(self):
        if self._mode != "data":
            self._refuse("Catalogue rows must precede their boundary result.")
        result = self._call("fetchall")
        self._exhausted = True
        return result

    def nextset(self):
        if self._mode != "boundary" or not self._exhausted:
            self._refuse("The complete boundary must be consumed before completion.")
        if self._call("nextset"):
            self._refuse("Unexpected additional catalogue batch result.")
        self._mode = "idle"
        return False
