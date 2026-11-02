"""Retained SQL observation for the private operator status command."""

from services.gsheets_health_service import HealthProbe
from services.legacy_export_snapshot_service import drain_thread
from services.operator_status_dal import check_connection

_probe = HealthProbe(label="SQL")


async def check_sql(*, timeout=5.0):
    return await _probe.observe(lambda: drain_thread(check_connection), timeout=timeout)


def close_admission():
    _probe.close()


async def shutdown():
    await _probe.shutdown()
