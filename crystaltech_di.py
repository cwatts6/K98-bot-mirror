# crystaltech_di.py
from __future__ import annotations

from crystaltech_config import ValidationReport
from crystaltech_service import CrystalTechService

_service: CrystalTechService | None = None


async def init_crystaltech_service(*, fail_on_warn: bool = False) -> ValidationReport:
    """Create + load the singleton service. Safe to call multiple times."""
    global _service
    if _service is None:
        _service = CrystalTechService()
    report = await _service.load(fail_on_warn=fail_on_warn)
    return report


def get_crystaltech_service() -> CrystalTechService:
    """Access the singleton. Call init_crystaltech_service() first (e.g., at startup)."""
    if _service is None:
        raise RuntimeError(
            "CrystalTechService not initialized. Call init_crystaltech_service() at startup."
        )
    return _service
