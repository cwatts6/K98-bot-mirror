"""Private, bounded observations; never receipts, retry inputs or raw error prose."""

from contextlib import contextmanager
from datetime import UTC, datetime
import json
import logging
import os
from pathlib import Path
import re
import sys
from uuid import uuid4

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
logger.propagate = False
_STAGES = frozenset(
    {
        "AUTHORITY_CAPTURE_READY",
        "AUTHORITY_PROCESS_FAILED",
        "AUTHORITY_SERVING",
        "AUTHORITY_DISPATCH_FAILED",
        "AUTHORITY_CONNECTION_FAILED",
        "AUTHORITY_REQUEST_FAILED",
        "AUTHORITY_REQUEST_COMPLETED",
        "AUTHORITY_STOPPED",
    }
)
_ACTIONS = frozenset({"ready", "open", "execute", "close", "prove"})
_STEPS = frozenset(
    {
        "request_lookup",
        "request_payload",
        "request_prepared",
        "request_budget",
        "request_guard",
        "request_dispatch",
        "provider_child",
        "response_validation",
        "request_result",
        "budget_complete",
        "budget_feedback",
    }
)
_SQL_REASONS = {
    "Owned SQL producer must drain before observational probe.": "sql_snapshot_owned",
    "Export admission busy.": "account_busy",
    "Resource admission busy.": "resource_busy",
    "Resource owner/fence/version conflict.": "resource_version_conflict",
    "Request stream CAS lost or closed.": "stream_version_conflict",
    "Preparation CAS conflict.": "preparation_version_conflict",
}


def _identifier(value):
    return (
        value.lower()
        if isinstance(value, str)
        and re.fullmatch(r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}", value)
        else None
    )


def diagnostic_record(stage, *, message=None, error=None, checkpoint=None):
    """Project only typed identifiers, bounded code locations and SQL classifications."""
    message = message if isinstance(message, dict) else {}
    scope = message.get("scope")
    scope = scope if isinstance(scope, dict) else {}
    request = message.get("request")
    request = request if isinstance(request, dict) else {}
    action = message.get("action")
    action = action if isinstance(action, str) and action in _ACTIONS else "invalid"
    types, states, numbers, frames = [], set(), set(), []
    reason = None
    current, seen = error, set()
    for _ in range(8):
        if not isinstance(current, BaseException) or id(current) in seen:
            break
        seen.add(id(current))
        name = type(current).__name__
        types.append(name if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,63}", name) else "Exception")
        if type(current).__module__ == "pyodbc" and current.args:
            args = current.args
            if isinstance(args[0], str) and re.fullmatch(r"[A-Z0-9]{5}", args[0]):
                states.add(args[0])
                for arg in args[1:5]:
                    if isinstance(arg, str):
                        text = arg[:4096]
                        numbers.update(int(n) for n in re.findall(r"\((\d{3,6})\)", text)[:8])
                        for prose, code in _SQL_REASONS.items():
                            if prose in text:
                                reason = code
        tb = current.__traceback__
        while tb is not None and len(frames) < 16:
            code = tb.tb_frame.f_code
            filename = Path(code.co_filename).name
            function = code.co_name
            # Never include paths, source lines, locals or arbitrary pseudo-filenames.
            if re.fullmatch(r"[A-Za-z0-9_]{1,80}\.py", filename) and re.fullmatch(
                r"[A-Za-z_][A-Za-z0-9_]{0,79}", function
            ):
                frames.append(dict(file=filename, function=function, line=tb.tb_lineno))
            tb = tb.tb_next
        current = current.__cause__ or current.__context__
    return dict(
        stage=stage if stage in _STAGES else "AUTHORITY_DISPATCH_FAILED",
        observed_utc=datetime.now(UTC).isoformat(),
        diagnostic_id=str(uuid4()),
        authority_pid=os.getpid(),
        action=action,
        checkpoint=checkpoint if checkpoint in _STEPS else None,
        stream_id=_identifier(
            request.get("stream_id") if action == "execute" else message.get("stream_id")
        ),
        object_id=_identifier(
            message.get("object_id") if action == "prove" else scope.get("ObjectID")
        ),
        request_id=_identifier(request.get("request_id")) if action == "execute" else None,
        exception_types=types,
        sqlstates=sorted(states)[:4],
        sql_numbers=sorted(numbers)[:8],
        reason_code=reason,
        frames=frames,
    )


def report_authority_event(stage, *, message=None, error=None, checkpoint=None):
    """Logging failure never changes the original result, closes work or requests replay."""
    try:
        text = json.dumps(
            diagnostic_record(stage, message=message, error=error, checkpoint=checkpoint),
            separators=(",", ":"),
        )
        try:
            logger.info(text)
        except Exception:
            pass
        # Preserve the existing console diagnostic for explicit/manual launchers.
        try:
            if sys.stderr is not None:
                print(text, file=sys.stderr, flush=True)
        except Exception:
            pass
    except Exception:
        pass


def configure_authority_diagnostics(evidence_root, *, inspect_path):
    """Reuse private timing-log custody/rotation, without inheriting console handles."""
    from services.export_reconciliation_service import _PublicationTimingHandler

    try:
        destination = str(Path(evidence_root).absolute() / "authority-diagnostics.jsonl")
        existing = [h for h in logger.handlers if isinstance(h, _PublicationTimingHandler)]
        if not any(h.baseFilename == destination for h in existing):
            handler = _PublicationTimingHandler(
                evidence_root, inspect_path, filename="authority-diagnostics.jsonl"
            )
            handler.setFormatter(logging.Formatter("%(message)s"))
            logger.addHandler(handler)
            for previous in existing:
                logger.removeHandler(previous)
                previous.close()
        logger.setLevel(logging.INFO)
        report_authority_event("AUTHORITY_CAPTURE_READY")
        return True
    except Exception:
        return False  # No diagnostic fallback into an unverified directory.


@contextmanager
def authority_request_step(name, request):
    from services.export_publication_metrics import measure_publication_step

    try:
        with measure_publication_step(name):
            yield
    except BaseException as error:
        report_authority_event(
            "AUTHORITY_REQUEST_FAILED",
            checkpoint=name,
            error=error,
            message={
                "action": "execute",
                "request": {
                    "request_id": request.request_id,
                    "stream_id": request.stream_id,
                },
            },
        )
        raise
