"""
maintenance_worker.py

CLI worker for maintenance tasks that must run in an isolated OS process.

This copy keeps the defensive recombination logic (extra safety) but the real
root fix is applied in file_utils.normalize_args_for_maintenance / run_maintenance_with_isolation.
Keeping the defensive logic here is an additional safety net for misbehaving callers.
"""

from __future__ import annotations

import argparse
import asyncio
import importlib
import json
import logging
import os
import sys
import time
import traceback
from typing import Any

# Initialize logging via project's logging_setup if available; otherwise minimal handler
try:
    from logging_setup import setup_logging  # type: ignore

    setup_logging(level=logging.INFO)
except Exception:
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        sh = logging.StreamHandler(sys.stderr)
        sh.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        sh.setFormatter(formatter)
        root_logger.addHandler(sh)
    root_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)
telemetry_logger = logging.getLogger("telemetry")

OFFLOAD_FILE_PREFIX = "__OFFLOAD_FILE__:"
OFFLOAD_JSON_PREFIX = "__OFFLOAD_JSON__:"

# Maximum number of characters of 'result' we will include verbatim in worker JSON.
# Environment knob for ops to adjust immediately.
_MAX_RESULT_SNIPPET = int(os.getenv("MAINT_WORKER_RESULT_SNIPPET", "1000"))


def emit_telemetry_event(payload: dict, *, max_snippet: int = 2000) -> None:
    try:
        telemetry_logger.info(json.dumps(payload, default=str))
    except Exception:
        try:
            telemetry_logger.info(str(payload))
        except Exception:
            pass


def _print_result_json(
    command: str,
    status: str,
    returncode: int = 0,
    details: str | None = None,
    result: Any | None = None,
):
    """
    Print a single-line JSON result to stdout so the parent can parse structured output.
    This prints to sys.__stdout__ to be resilient to logging redirection.
    To avoid emitting large blobs into telemetry we summarize/truncate `result` when needed.
    """
    payload: dict[str, Any] = {
        "worker_result": True,
        "command": command,
        "status": status,
        "returncode": returncode,
    }
    if details:
        payload["details"] = str(details)

    # Handle result trimming and summary:
    if result is not None:
        try:
            # If result is a simple scalar or small, include it directly up to a cap
            if isinstance(result, (str, int, float, bool)):
                sres = str(result)
                if len(sres) <= _MAX_RESULT_SNIPPET:
                    payload["result"] = result
                else:
                    payload["result_summary"] = {
                        "type": type(result).__name__,
                        "length": len(sres),
                        "preview": sres[:_MAX_RESULT_SNIPPET],
                    }
            else:
                # For containers (dict, list, large objects) attempt to serialize to JSON string,
                # but do not include more than _MAX_RESULT_SNIPPET characters. Instead include a structured summary.
                try:
                    serialized = json.dumps(result, default=str)
                except Exception:
                    serialized = str(result)
                if len(serialized) <= _MAX_RESULT_SNIPPET:
                    # safe to include whole result
                    try:
                        # attempt to include parsed JSON if it's JSON-serializable
                        payload["result"] = json.loads(serialized)
                    except Exception:
                        payload["result"] = serialized
                else:
                    # too big - include a short summary with preview
                    payload["result_summary"] = {
                        "type": type(result).__name__,
                        "length": len(serialized),
                        "preview": serialized[:_MAX_RESULT_SNIPPET],
                    }
        except Exception:
            # Last-resort: include a tiny textual summary
            try:
                payload["result_summary"] = {
                    "type": type(result).__name__,
                    "repr": repr(result)[:200],
                }
            except Exception:
                payload["result_summary"] = {"type": "unserializable", "repr": "<unserializable>"}

    try:
        # Always write to sys.__stdout__ for parent parsing
        sys.__stdout__.write(json.dumps(payload, default=str) + "\n")
        sys.__stdout__.flush()
    except Exception:
        try:
            print(json.dumps(payload, default=str))
        except Exception:
            pass


def import_proc_import():
    try:
        from proc_config_import import run_proc_config_import

        return run_proc_config_import
    except Exception:
        logger.exception("Failed to import proc_config_import.run_proc_config_import")
        return None


def import_post_stats():
    try:
        from file_utils import run_post_import_stats_update

        return run_post_import_stats_update
    except Exception:
        logger.exception("Failed to import file_utils.run_post_import_stats_update")
        return None


def do_proc_import():
    fn = import_proc_import()
    if fn is None:
        emit_telemetry_event(
            {"event": "proc_import_worker", "status": "failed", "error": "import_error"}
        )
        _print_result_json("proc_import", "failed", returncode=3, details="import_error")
        return 3
    try:
        logger.info("Starting proc_config_import")
        import inspect

        if inspect.iscoroutinefunction(fn):
            import asyncio

            res = asyncio.run(fn())
        else:
            res = fn()
        logger.info("proc_config_import completed successfully")
        emit_telemetry_event({"event": "proc_import_worker", "status": "success"})
        _print_result_json("proc_import", "success", returncode=0, result=res)
        return 0
    except Exception as e:
        logger.exception("proc_config_import failed: %s", e)
        emit_telemetry_event({"event": "proc_import_worker", "status": "failed", "error": str(e)})
        _print_result_json("proc_import", "failed", returncode=3, details=str(e))
        return 3


def do_post_stats(
    server: str | None, database: str | None, username: str | None, password: str | None
):
    fn = import_post_stats()
    if fn is None:
        emit_telemetry_event(
            {"event": "post_stats_worker", "status": "failed", "error": "import_error"}
        )
        _print_result_json("post_stats", "failed", returncode=3, details="import_error")
        return 3
    try:
        logger.info("Starting post-import stats update for database=%s", database)
        res = fn(server, database, username, password)
        logger.info("post-import stats update completed")
        emit_telemetry_event(
            {"event": "post_stats_worker", "status": "success", "database": database or ""}
        )
        _print_result_json("post_stats", "success", returncode=0, result=res)
        return 0
    except Exception as e:
        logger.exception("post-import stats update failed: %s", e)
        emit_telemetry_event({"event": "post_stats_worker", "status": "failed", "error": str(e)})
        _print_result_json("post_stats", "failed", returncode=3, details=str(e))
        return 3


def do_test_sleep(seconds: float):
    try:
        logger.info("test_sleep: sleeping for %.3fs", seconds)
        time.sleep(seconds)
        emit_telemetry_event({"event": "test_sleep", "status": "slept", "seconds": float(seconds)})
        _print_result_json(
            "test_sleep",
            "success",
            returncode=0,
            details=f"slept={seconds}",
            result={"slept": seconds},
        )
        return 0
    except Exception as e:
        logger.exception("test_sleep failed: %s", e)
        emit_telemetry_event({"event": "test_sleep", "status": "failed", "error": str(e)})
        _print_result_json("test_sleep", "failed", returncode=3, details=str(e))
        return 3


def _reconstruct_token(tok: str) -> Any:
    if not isinstance(tok, str):
        return tok
    if tok.startswith(OFFLOAD_FILE_PREFIX):
        path = tok[len(OFFLOAD_FILE_PREFIX) :]
        try:
            with open(path, "rb") as f:
                return f.read()
        except Exception as e:
            raise RuntimeError(f"failed to read offloaded file {path}: {e!r}")
    if tok.startswith(OFFLOAD_JSON_PREFIX):
        payload = tok[len(OFFLOAD_JSON_PREFIX) :]
        try:
            if os.path.exists(payload):
                with open(payload, "rb") as f:
                    b = f.read()
                try:
                    return json.loads(b.decode("utf-8"))
                except Exception:
                    return b
        except Exception:
            pass
        try:
            return json.loads(payload)
        except Exception:
            return payload
    return tok


def _sanitize_for_logging(obj: Any, *, max_collection_items: int = 8) -> str:
    try:
        if isinstance(obj, (bytes, bytearray, memoryview)):
            try:
                length = len(obj)
            except Exception:
                length = -1
            return f"<bytes len={length}>"

        if isinstance(obj, str):
            if obj.startswith(OFFLOAD_FILE_PREFIX) or obj.startswith(OFFLOAD_JSON_PREFIX):
                try:
                    _, path = obj.split(":", 1)
                    bn = os.path.basename(path)
                    return f"{obj.split(':',1)[0]}:{bn}"
                except Exception:
                    return obj.split(":", 1)[0] + ":<path>"
            if len(obj) > 200:
                return repr(obj[:200] + "...(truncated)")
            return repr(obj)

        if isinstance(obj, (list, tuple, set)):
            try:
                length = len(obj)
            except Exception:
                length = -1
            return f"<{type(obj).__name__} len={length}>"

        if isinstance(obj, dict):
            try:
                length = len(obj)
            except Exception:
                length = -1
            return f"<dict len={length}>"

        r = repr(obj)
        if len(r) > 300:
            return r[:300] + "...(truncated)"
        return r
    except Exception:
        return "<unserializable>"


def _sanitize_args_for_logging(args: list[Any]) -> list[str]:
    out: list[str] = []
    for a in args:
        out.append(_sanitize_for_logging(a))
    return out


def _recombine_char_tokens_if_path_like(
    reconstructed: list[Any], original_tokens: list[str]
) -> list[Any]:
    """
    Defensive helper: if original_tokens look like character-split path tokens,
    recombine them into a single string if the joined result looks path-like.
    This is a safety net and should not be relied upon if the caller is fixed.
    """
    try:
        if not original_tokens:
            return reconstructed
        if (
            all(isinstance(t, str) and len(t) == 1 for t in original_tokens)
            and len(original_tokens) > 3
        ):
            joined = "".join(original_tokens)
            import re as _re

            if _re.search(r"^[A-Za-z]:\\.*\.(xlsx|xls|csv)$", joined, _re.IGNORECASE) or (
                (("/" in joined) or ("\\" in joined)) and _re.search(r"\.\w{2,5}$", joined)
            ):
                logger.warning(
                    "Detected likely character-split path tokens; recombining into single arg: %s",
                    joined if len(joined) < 200 else joined[:200] + "...(truncated)",
                )
                return [joined]
    except Exception:
        pass
    return reconstructed


def run_callable_spec(spec: str, remaining_args: list[str]) -> int:
    try:
        if ":" not in spec:
            logger.error("Invalid callable spec (missing ':'): %s", spec)
            _print_result_json(spec, "failed", returncode=2, details="invalid_spec")
            return 2
        module_name, func_name = spec.split(":", 1)
        try:
            mod = importlib.import_module(module_name)
        except Exception as e:
            logger.exception("Failed to import module %s: %s", module_name, e)
            _print_result_json(spec, "failed", returncode=3, details=f"import_module_error:{e}")
            return 3
        if not hasattr(mod, func_name):
            logger.error("Module %s has no attribute %s", module_name, func_name)
            _print_result_json(spec, "failed", returncode=3, details="no_such_function")
            return 3
        fn = getattr(mod, func_name)
        call_args: list[Any] = []
        try:
            reconstructed = [_reconstruct_token(t) for t in remaining_args]
        except Exception as e:
            logger.exception("Failed to reconstruct args for %s: %s", spec, e)
            _print_result_json(spec, "failed", returncode=3, details=f"arg_reconstruct_error:{e}")
            return 3

        # Defensive recombination (safety net)
        reconstructed = _recombine_char_tokens_if_path_like(reconstructed, remaining_args)

        if len(remaining_args) == 1 and isinstance(remaining_args[0], str):
            first = remaining_args[0].strip()
            if first.startswith("[") or first.startswith("{"):
                try:
                    parsed = json.loads(first)
                    if isinstance(parsed, list):
                        call_args = parsed
                    else:
                        call_args = [parsed]
                except Exception:
                    call_args = reconstructed
            else:
                call_args = reconstructed
        else:
            call_args = reconstructed

        safe_args = _sanitize_args_for_logging(call_args)
        logger.info("Invoking callable %s.%s with args=%s", module_name, func_name, safe_args)

        ret = None
        if asyncio.iscoroutinefunction(fn):
            ret = asyncio.run(fn(*call_args))
        else:
            ret = fn(*call_args)

        _print_result_json(spec, "success", returncode=0, result=ret)
        return 0
    except Exception as e:
        logger.exception("callable %s failed: %s", spec, e)
        _print_result_json(spec, "failed", returncode=3, details=str(e))
        return 3


def main(argv=None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if argv:
        first = argv[0]
        if isinstance(first, str) and ":" in first:
            return run_callable_spec(first, argv[1:])

    parser = argparse.ArgumentParser(prog="maintenance_worker")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("proc_import", help="Run proc_config_import synchronously")

    p_post = sub.add_parser("post_stats", help="Run post-import stats stored procedure")
    p_post.add_argument("--server", required=False)
    p_post.add_argument("--database", required=False)
    p_post.add_argument("--username", required=False)
    p_post.add_argument("--password", required=False)

    p_test = sub.add_parser("test_sleep", help="TEST: sleep for N seconds")
    p_test.add_argument("--seconds", required=False, type=float, default=1.0)

    args = parser.parse_args(argv)

    if args.cmd == "proc_import":
        return do_proc_import()

    if args.cmd == "post_stats":
        server = args.server or os.environ.get("SQL_SERVER")
        database = args.database or os.environ.get("SQL_DATABASE")
        username = args.username or os.environ.get("SQL_USERNAME")
        password = args.password or os.environ.get("SQL_PASSWORD")
        if not database or not server:
            logger.error("post_stats requires server and database (via args or env)")
            _print_result_json("post_stats", "failed", returncode=2, details="missing_args")
            return 2
        return do_post_stats(server, database, username, password)

    if args.cmd == "test_sleep":
        return do_test_sleep(args.seconds)

    logger.error("Unknown command")
    _print_result_json("unknown", "failed", returncode=2, details="unknown_command")
    return 2


if __name__ == "__main__":
    try:
        code = main()
        sys.exit(code)
    except Exception:
        traceback.print_exc()
        sys.exit(3)
