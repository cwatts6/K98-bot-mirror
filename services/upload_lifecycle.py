"""Local upload admission and observer drain; no durable business ownership."""

import asyncio
from functools import wraps

from core.owned_work import drain_awaitable

_closed = False
_tasks = set()


class UploadAdmissionClosed(RuntimeError):
    pass


def tracked_upload(function):
    @wraps(function)
    async def run(*args, **kwargs):
        if _closed:
            raise UploadAdmissionClosed("Upload admission is closed for shutdown")
        task = asyncio.current_task()
        _tasks.add(task)
        from services.optional_import_audit_worker import begin_scope, end_scope

        token = begin_scope()
        try:
            return await function(*args, **kwargs)
        finally:
            try:
                end_scope(token)
            finally:
                _tasks.discard(task)

    return run


def close_admission():
    global _closed
    _closed = True


async def drain():
    """Cancel observers; finite importer boundaries retain their physical work."""
    close_admission()
    pending = tuple(task for task in _tasks if task is not asyncio.current_task())
    for task in pending:
        task.cancel()
    if pending:
        await drain_awaitable(asyncio.gather(*pending, return_exceptions=True))
