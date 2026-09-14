from __future__ import annotations

import argparse
import asyncio
import importlib
import inspect
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

# Try to reuse central definitions from file_utils when available to avoid duplication.
# Guarded import to avoid circular import issues.
try:
    from file_utils import (
        OFFLOAD_FILE_PREFIX as OFFLOAD_FILE_PREFIX,  # type: ignore
        OFFLOAD_JSON_PREFIX as OFFLOAD_JSON_PREFIX,  # type: ignore
        emit_telemetry_event as emit_telemetry_event,  # type: ignore
        normalize_args_for_maintenance as normalize_args_for_maintenance,  # type: ignore
    )
except Exception:
    OFFLOAD_FILE_PREFIX = "__OFFLOAD_FILE__:"
    OFFLOAD_JSON_PREFIX = "__OFFLOAD_JSON__:"
    normalize_args_for_maintenance = None  # type: ignore

    def emit_telemetry_event(payload: dict, *, max_snippet: int = 2000) -> None:
        try:
            telemetry_logger.info(json.dumps(payload, default=str))
        except Exception:
            try:
                telemetry_logger.info(str(payload))
            except Exception:
                pass


_RECOMBINE_DISABLE = os.getenv("MAINT_RECOMBINE_DISABLE", "0").strip().lower() in (
    "1",
    "true",
    "yes",
)
_RECOMBINE_MIN_RUN = int(os.getenv("MAINT_RECOMBINE_MIN_RUN", "6"))
_MAX_RESULT_SNIPPET = int(os.getenv("MAINT_WORKER_RESULT_SNIPPET", "1000"))


def _parse_allowlist(raw: str | None) -> list[str] | None:
    if not raw:
        return None
    raw = raw.strip()
    if not raw:
        return None
    try:
        if raw.startswith("["):
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(x).strip() for x in parsed if x]
    except Exception:
        pass
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    return parts if parts else None


def _spec_allowed(spec: str) -> bool:
    """
    Decide whether a callable spec like 'module:func' is allowed given the env configuration.

    Allowlist entries:
      - 'module:func' -> allow that exact spec
      - 'module' -> allow any function in that module
      - 'module*' or 'module.*' -> prefix match on module name
      - 'module:func*' -> prefix match on function name

    Precedence:
      - If MAINT_SPEC_ALLOWLIST is present (non-empty), it is enforced and takes precedence.
      - Otherwise MAINT_ALLOW_ALL enables permissive mode (backwards compatible).
    """
    raw_allowlist = os.getenv("MAINT_SPEC_ALLOWLIST", None)
    allowlist = _parse_allowlist(raw_allowlist)
    if allowlist is not None:
        spec = spec.strip()
        if ":" in spec:
            module_name, func_name = spec.split(":", 1)
        else:
            module_name = spec
            func_name = None

        def _match_pat(value: str | None, pat: str | None) -> bool:
            """Match value against pat supporting simple suffix '*' for prefix matching."""
            if pat is None:
                return True
            if value is None:
                return False
            pat = pat.strip()
            if pat == "*":
                return True
            # Normalize entry that uses '.' as namespace wildcard (allow 'mod.*' or 'mod*')
            if pat.endswith(".*") or pat.endswith("*"):
                prefix = pat[:-1] if pat.endswith("*") else pat
                # if pat was 'mod.*' prefix becomes 'mod.' — we want startswith('mod') as well
                prefix = prefix.rstrip(".")
                return str(value).startswith(prefix)
            return str(value) == pat

        for entry in allowlist:
            if ":" in entry:
                mod_pat, func_pat = entry.split(":", 1)
            else:
                mod_pat, func_pat = entry, None

            if _match_pat(module_name, mod_pat) and _match_pat(func_name, func_pat):
                return True
        return False

    # No allowlist configured -> consult MAINT_ALLOW_ALL (backwards compatible)
    ma = os.getenv("MAINT_ALLOW_ALL", "0").strip().lower()
    if ma in ("1", "true", "yes"):
        return True
    return True  # default permissive if nothing configured


def _print_result_json(
    command: str,
    status: str,
    returncode: int = 0,
    details: str | None = None,
    result: Any | None = None,
):
    payload: dict[str, Any] = {
        "worker_result": True,
        "command": command,
        "status": status,
        "returncode": returncode,
    }
    if details:
        payload["details"] = str(details)
    if result is not None:
        try:
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
                try:
                    serialized = json.dumps(result, default=str)
                except Exception:
                    serialized = str(result)
                if len(serialized) <= _MAX_RESULT_SNIPPET:
                    try:
                        payload["result"] = json.loads(serialized)
                    except Exception:
                        payload["result"] = serialized
                else:
                    payload["result_summary"] = {
                        "type": type(result).__name__,
                        "length": len(serialized),
                        "preview": serialized[:_MAX_RESULT_SNIPPET],
                    }
        except Exception:
            try:
                payload["result_summary"] = {
                    "type": type(result).__name__,
                    "repr": repr(result)[:200],
                }
            except Exception:
                payload["result_summary"] = {"type": "unserializable", "repr": "<unserializable>"}
    try:
        sys.__stdout__.write(json.dumps(payload, default=str) + "\n")
        sys.__stdout__.flush()
    except Exception:
        try:
            print(json.dumps(payload, default=str))
        except Exception:
            pass


def _run_coroutine_safely(fn, args_tuple):
    """
    Build coro = fn(*args_tuple), try asyncio.run(coro). On RuntimeError, close coro and
    create a fresh coro and execute it on a fresh loop from the policy (policy.new_event_loop())
    to avoid any monkeypatch on asyncio.new_event_loop interfering.
    """
    coro = None
    coro2 = None
    loop = None
    try:
        coro = fn(*args_tuple)
        if not inspect.iscoroutine(coro):
            return coro
        try:
            return asyncio.run(coro)
        except RuntimeError:
            # close original if possible
            try:
                if getattr(coro, "close", None):
                    coro.close()
            except Exception:
                pass
            # create fresh coro and use policy.new_event_loop()
            coro2 = fn(*args_tuple)
            policy = asyncio.get_event_loop_policy()
            loop = policy.new_event_loop()
            try:
                return loop.run_until_complete(coro2)
            finally:
                try:
                    loop.close()
                except Exception:
                    pass
    finally:
        try:
            if coro and getattr(coro, "close", None):
                coro.close()
        except Exception:
            pass
        try:
            if coro2 and getattr(coro2, "close", None):
                coro2.close()
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
        if inspect.iscoroutinefunction(fn):
            try:
                res = _run_coroutine_safely(fn, ())
            except Exception as e:
                logger.exception("proc_config_import coroutine failed: %s", e)
                _print_result_json("proc_import", "failed", returncode=3, details=str(e))
                return 3
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
    Defensive helper: join contiguous runs of single-character tokens into single string tokens
    if the joined chunk looks path-like (contains slashes or drive prefix and an extension).
    The function attempts to preserve original reconstructed types when possible.

    Recombination can be disabled by setting env MAINT_RECOMBINE_DISABLE=1.
    Tunable minimum run length for consideration via MAINT_RECOMBINE_MIN_RUN (default 6).
    """
    try:
        if _RECOMBINE_DISABLE:
            return reconstructed

        if not original_tokens:
            return reconstructed

        # Identify contiguous runs of single-character string tokens
        out_tokens: list[str] = []
        groups: list[tuple[int, int]] = []
        i = 0
        n = len(original_tokens)
        while i < n:
            tok = original_tokens[i]
            if isinstance(tok, str) and len(tok) == 1:
                j = i
                run = []
                while (
                    j < n and isinstance(original_tokens[j], str) and len(original_tokens[j]) == 1
                ):
                    run.append(original_tokens[j])
                    j += 1
                run_len = j - i
                if run_len >= _RECOMBINE_MIN_RUN:
                    joined = "".join(run)
                    import re as _re

                    looks_like_path = bool(
                        _re.search(r"^[A-Za-z]:\\.*\.(xlsx|xls|csv)$", joined, _re.IGNORECASE)
                        or (("/" in joined or "\\" in joined) and _re.search(r"\.\w{2,5}$", joined))
                        or (joined.startswith("/") and _re.search(r"\.\w{2,5}$", joined))
                    )
                    if looks_like_path:
                        out_tokens.append(joined)
                        groups.append((i, j - 1))
                        i = j
                        continue
                for k in range(i, j):
                    out_tokens.append(original_tokens[k])
                    groups.append((k, k))
                i = j
            else:
                out_tokens.append(tok)
                groups.append((i, i))
                i += 1

        if len(out_tokens) == len(original_tokens) and all(
            out_tokens[k] == original_tokens[k] for k in range(len(original_tokens))
        ):
            return reconstructed

        new_reconstructed: list[Any] = []
        can_map = len(reconstructed) == len(original_tokens)
        for (start, end), token_str in zip(groups, out_tokens, strict=False):
            if start == end:
                if start < len(reconstructed):
                    new_reconstructed.append(reconstructed[start])
                else:
                    new_reconstructed.append(token_str)
            else:
                if can_map:
                    try:
                        sub = reconstructed[start : end + 1]
                        if all(isinstance(x, str) and len(x) == 1 for x in sub):
                            new_reconstructed.append("".join(sub))
                        else:
                            new_reconstructed.append(token_str)
                    except Exception:
                        new_reconstructed.append(token_str)
                else:
                    new_reconstructed.append(token_str)

        return new_reconstructed
    except Exception:
        return reconstructed


def run_callable_spec(spec: str, remaining_args: list[str]) -> int:
    try:
        if ":" not in spec:
            logger.error("Invalid callable spec (missing ':'): %s", spec)
            _print_result_json(spec, "failed", returncode=2, details="invalid_spec")
            return 2

        # Enforce allowlist early to avoid imports / side-effects for blocked specs
        if not _spec_allowed(spec):
            logger.warning("Spec %s not allowed by MAINT_SPEC_ALLOWLIST", spec)
            try:
                emit_telemetry_event({"event": "maintenance_spec_denied", "spec": spec})
            except Exception:
                pass
            _print_result_json(spec, "failed", returncode=2, details="spec_not_allowed")
            return 2

        # Audit / telemetry: record that we are evaluating/allowing this spec
        try:
            emit_telemetry_event(
                {
                    "event": "maintenance_spec_evaluated",
                    "spec": spec,
                    "allow_all": os.getenv("MAINT_ALLOW_ALL", "0").strip().lower()
                    in ("1", "true", "yes"),
                    "allowlist_present": bool(os.getenv("MAINT_SPEC_ALLOWLIST", None)),
                }
            )
        except Exception:
            pass

        # Telemetry: spec allowed (audit)
        try:
            emit_telemetry_event(
                {
                    "event": "maintenance_spec_allowed",
                    "spec": spec,
                    "allow_all": os.getenv("MAINT_ALLOW_ALL", "0").strip().lower()
                    in ("1", "true", "yes"),
                    "allowlist_present": bool(os.getenv("MAINT_SPEC_ALLOWLIST", None)),
                }
            )
        except Exception:
            pass

        module_name, func_name = spec.split(":", 1)
        try:
            mod = importlib.import_module(module_name)
        except ModuleNotFoundError as e:
            # Module not importable is expected in common cases (local/test callables).
            # Log at INFO so logs aren't noisy; include full traceback under DEBUG for diagnostics.
            logger.info(
                "Offload module %r not importable: %s. This is expected for non-installable/local callables; "
                "caller may fall back to in-thread execution.",
                module_name,
                e,
            )
            logger.debug("Import traceback for module %s:\n%s", module_name, traceback.format_exc())
            _print_result_json(spec, "failed", returncode=3, details=f"import_module_error:{e}")
            return 3
        except Exception as e:
            # Everything else is still an unexpected import failure — keep exception logging.
            logger.exception("Failed to import module %s: %s", module_name, e)
            _print_result_json(spec, "failed", returncode=3, details=f"import_module_error:{e}")
            return 3
        fn = getattr(mod, func_name)
        call_args: list[Any] = []

        # Prefer central normalizer if available
        normalized = None
        if normalize_args_for_maintenance is not None:
            try:
                normalized = normalize_args_for_maintenance(remaining_args)
            except Exception:
                normalized = None

        if normalized is not None:
            try:
                # Normalizer provided something; ensure any OFFLOAD_* tokens are reconstructed
                try:
                    reconstructed_from_normalizer = [_reconstruct_token(t) for t in normalized]
                except Exception as e:
                    logger.exception(
                        "Failed to reconstruct tokens returned by normalize_args_for_maintenance: %s",
                        e,
                    )
                    # Fall back to using normalized as-is (we'll record telemetry below)
                    call_args = normalized
                else:
                    # Defensive recombination based on tokens returned by normalizer
                    try:
                        reconstructed_from_normalizer = _recombine_char_tokens_if_path_like(
                            reconstructed_from_normalizer, normalized
                        )
                    except Exception:
                        # If recombination fails, keep the reconstructed values
                        pass
                    call_args = reconstructed_from_normalizer
            except Exception:
                call_args = list(remaining_args)
        else:
            try:
                reconstructed = [_reconstruct_token(t) for t in remaining_args]
            except Exception as e:
                logger.exception("Failed to reconstruct args for %s: %s", spec, e)
                _print_result_json(
                    spec, "failed", returncode=3, details=f"arg_reconstruct_error:{e}"
                )
                return 3

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

        # After building call_args, warn if any OFFLOAD tokens remain (should not happen)
        try:
            if any(
                isinstance(a, str)
                and (a.startswith(OFFLOAD_FILE_PREFIX) or a.startswith(OFFLOAD_JSON_PREFIX))
                for a in call_args
            ):
                try:
                    emit_telemetry_event(
                        {
                            "event": "maintenance_offload_unreconstructed",
                            "spec": spec,
                            "note": "call_args contains OFFLOAD_* token after normalization/reconstruction",
                        }
                    )
                except Exception:
                    pass
                logger.warning(
                    "call_args for %s contains OFFLOAD_* tokens after normalization/reconstruction: %s",
                    spec,
                    _sanitize_args_for_logging(call_args),
                )
        except Exception:
            # keep moving; we've attempted to report the issue
            pass

        safe_args = _sanitize_args_for_logging(call_args)
        logger.info("Invoking callable %s.%s with args=%s", module_name, func_name, safe_args)

        ret = None
        if asyncio.iscoroutinefunction(fn):
            try:
                ret = _run_coroutine_safely(fn, tuple(call_args))
            except Exception as e:
                logger.exception("Coroutine execution failed: %s", e)
                _print_result_json(spec, "failed", returncode=3, details=str(e))
                return 3
        else:
            try:
                ret = fn(*call_args)
            except Exception as e:
                logger.exception("Synchronous callable raised: %s", e)
                _print_result_json(spec, "failed", returncode=3, details=str(e))
                return 3

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
