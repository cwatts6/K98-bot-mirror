"""Shared optional-upload startup/drain; business custody remains with its owner."""

import asyncio

from core.owned_work import drain_awaitable, drain_thread
from services import download_log_service, operation_diagnostics, optional_import_audit_worker


def configure(path):
    download_log_service.configure(path)
    optional_import_audit_worker.configure()


async def shutdown():
    """Close both admissions before joining either, including during cancellation."""

    async def settle():
        owners = (download_log_service, optional_import_audit_worker)
        errors = []
        for owner in owners:
            try:
                owner.request_close()
            except Exception as exc:
                errors.append(exc)
        results = await asyncio.gather(
            *(drain_thread(owner.wait_closed) for owner in owners), return_exceptions=True
        )
        errors.extend(result for result in results if isinstance(result, Exception))
        try:
            await drain_thread(operation_diagnostics.shutdown)
        except Exception as exc:
            errors.append(exc)
        if errors:
            raise ExceptionGroup("Optional upload drainage unconfirmed", errors)

    await drain_awaitable(settle())
