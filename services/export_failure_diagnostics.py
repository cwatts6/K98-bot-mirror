"""Bounded worker diagnostics without exception prose, SQL text or payloads."""

from datetime import UTC, datetime
import re
from uuid import uuid4

_CODE_FILES = {
    "export_coordination_service.py",
    "export_coordination_dal.py",
    "export_provider_adapter.py",
    "export_runtime_composition.py",
    "export_execution_authority.py",
    "export_request_budget.py",
    "export_snapshot_store.py",
    "legacy_export_snapshot_service.py",
}


def failure_record(error, *, job_id=None, stage="delivery"):
    """Retain code locations and driver codes; never include exception messages."""
    types, frames, states, numbers = [], [], set(), set()
    current, seen = error, set()
    for _ in range(4):
        if not isinstance(current, BaseException) or id(current) in seen:
            break
        seen.add(id(current))
        name = type(current).__name__
        types.append(name if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,63}", name) else "Exception")
        args = current.args
        if (
            type(current).__module__ == "pyodbc"
            and args
            and isinstance(args[0], str)
            and re.fullmatch(r"[A-Z0-9]{5}", args[0])
        ):
            states.add(args[0])
            for arg in args[1:5]:
                if isinstance(arg, str):
                    numbers.update(int(n) for n in re.findall(r"\((\d{3,6})\)", arg[:4096])[:8])
        tb = current.__traceback__
        for _ in range(64):
            if tb is None:
                break
            code = tb.tb_frame.f_code
            filename = code.co_filename.replace("\\", "/").rsplit("/", 1)[-1]
            if filename in _CODE_FILES and re.fullmatch(
                r"[A-Za-z_][A-Za-z0-9_]{0,63}", code.co_name
            ):
                frames.append(dict(file=filename, function=code.co_name, line=tb.tb_lineno))
            tb = tb.tb_next
        current = current.__cause__ or current.__context__
    return dict(
        diagnostic_id=str(uuid4()),
        observed_utc=datetime.now(UTC).isoformat(),
        job_id=(
            job_id.lower()
            if isinstance(job_id, str)
            and re.fullmatch(r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", job_id)
            else None
        ),
        stage=(
            stage
            if stage in {"authorization", "snapshot", "delivery", "terminal_record"}
            else "unknown"
        ),
        exception_types=types,
        sqlstates=sorted(states)[:4],
        sql_numbers=sorted(numbers)[:8],
        code_locations=frames[-16:],
    )
