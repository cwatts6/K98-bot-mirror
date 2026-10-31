"""Bounded same-session admission before an authority SQL checkpoint."""

from contextlib import contextmanager
import hashlib

from kvk.dal.new_source_import_dal import SourceConflict, one
from services.export_coordination_dal import _mutex


@contextmanager
def execution_account_lock(cursor, account):
    """Keep the procedure's own transaction/CAS intact; never retry its body.

    SQL Server permits the same session to acquire the account lock again with
    Transaction ownership. The procedure still rejects ambient transactions and
    performs every ownership/version check after admission. This outer Session
    lock covers SQL only, is explicitly released before returning to the caller,
    and cannot stand in for a durable resource claim or execution receipt.
    """
    if (
        not isinstance(account, str)
        or not 1 <= len(account) <= 128
        or account != account.strip()
        or not account.isascii()
    ):
        raise ValueError("Exact SQL account key required.")
    key = "account:" + account
    _mutex(cursor, key, wait_ms=1000, owner="Session")
    try:
        yield
    finally:
        cursor.execute(
            "DECLARE @r int; EXEC @r=sys.sp_releaseapplock @Resource=?,"
            "@LockOwner='Session'; SELECT @r AS LockResult",
            "k98-export:" + hashlib.sha256(key.encode()).hexdigest(),
        )
        result = one(cursor)
        if not result or result["LockResult"] < 0:
            raise SourceConflict("Authority account lock release is unconfirmed.")
        if cursor.fetchall():
            raise SourceConflict("Unexpected account lock release response.")
        while cursor.nextset():
            if cursor.description is not None and cursor.fetchall():
                raise SourceConflict("Unexpected account lock release results.")
