"""Attribute the existing zero-wait producer guard without retrying admission."""

import re
import time


class SnapshotAdmissionRefused(RuntimeError):
    """Known SQL guard refusal before entry; not a claim about the blocking owner."""

    def __init__(self, *, result, session, transaction_state, transaction_count, elapsed_ms):
        super().__init__("Legacy SQL snapshot admission refused; inspect structured diagnostics.")
        self.result = result
        self.session = session
        self.transaction_state = transaction_state
        self.transaction_count = transaction_count
        self.elapsed_ms = elapsed_ms


def acquire_snapshot_guard(cursor):
    started = time.monotonic()
    try:
        cursor.execute(
            "DECLARE @r int; EXEC @r=sys.sp_getapplock "
            "@Resource=N'k98-legacy-output-snapshot',@LockMode='Exclusive',"
            "@LockOwner='Session',@LockTimeout=0; "
            "IF @r<0 BEGIN DECLARE @m nvarchar(2048)=CONCAT("
            "'K98_SNAPSHOT_ADMISSION result=',@r,' session=',@@SPID,"
            "' xact=',XACT_STATE(),' count=',@@TRANCOUNT); THROW 51421,@m,1; END;"
        )
    except Exception as original:
        args = getattr(original, "args", ())
        text = " ".join(v[:8192] for v in args[1:5] if isinstance(v, str))
        match = re.search(
            r"K98_SNAPSHOT_ADMISSION result=(-1|-2|-3|-999) session=(\d{1,5}) "
            r"xact=(-1|0|1) count=(\d{1,10})(?!\d)",
            text,
        )
        if args and args[0] == "42000" and "(51421)" in text and match:
            result, session, state, count = map(int, match.groups())
            raise SnapshotAdmissionRefused(
                result=result,
                session=session,
                transaction_state=state,
                transaction_count=count,
                elapsed_ms=max(0, int((time.monotonic() - started) * 1000)),
            ) from original
        raise
