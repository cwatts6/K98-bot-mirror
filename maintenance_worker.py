#!/usr/bin/env python3
"""
maintenance_worker.py

Lightweight CLI worker for maintenance tasks that must run in an isolated OS process.

Supported commands:
  - proc_import       : Run proc_config_import (uses proc_config_import.run_proc_config_import)
  - post_stats        : Run post-import stats stored procedure (file_utils.run_post_import_stats_update)
  - test_sleep        : TESTING helper — sleep for N seconds (used by integration tests)

Notes:
- This process intentionally stays small and synchronous so it can be killed by the parent
  if the operation overruns a timeout.
- It logs using the central logging_setup so telemetry records remain consistent.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
import traceback

# Initialize logging via the project's logging_setup if available; otherwise attach a minimal handler.
try:
    # This will configure queue logging and the telemetry handler as in the main process.
    from logging_setup import setup_logging  # type: ignore

    setup_logging(level=logging.INFO)
except Exception:

    # Add a minimal StreamHandler only if no handlers are present.
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


def import_proc_import():
    try:
        # Import lazily so worker stays lightweight until needed
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
        telemetry_logger.error(
            '{"event":"proc_import_worker","status":"failed","error":"%s"}', "import_error"
        )
        return 3
    try:
        logger.info("Starting proc_config_import")
        # Support coroutine or sync function
        import inspect

        if inspect.iscoroutinefunction(fn):
            import asyncio

            asyncio.run(fn())
        else:
            fn()
        logger.info("proc_config_import completed successfully")
        telemetry_logger.info('{"event":"proc_import_worker","status":"success"}')
        return 0
    except Exception as e:
        logger.exception("proc_config_import failed: %s", e)
        telemetry_logger.error(
            '{"event":"proc_import_worker","status":"failed","error":"%s"}', str(e)
        )
        return 3


def do_post_stats(
    server: str | None, database: str | None, username: str | None, password: str | None
):
    fn = import_post_stats()
    if fn is None:
        telemetry_logger.error(
            '{"event":"post_stats_worker","status":"failed","error":"%s"}', "import_error"
        )
        return 3
    try:
        logger.info("Starting post-import stats update for database=%s", database)
        # run_post_import_stats_update(signature: server, database, username, password, timeout_seconds=...)
        fn(server, database, username, password)
        logger.info("post-import stats update completed")
        telemetry_logger.info(
            '{"event":"post_stats_worker","status":"success","database":"%s"}', database or ""
        )
        return 0
    except Exception as e:
        logger.exception("post-import stats update failed: %s", e)
        telemetry_logger.error(
            '{"event":"post_stats_worker","status":"failed","error":"%s"}', str(e)
        )
        return 3


def do_test_sleep(seconds: float):
    try:
        logger.info("test_sleep: sleeping for %.3fs", seconds)
        time.sleep(seconds)
        # Write a deterministic token to the ORIGINAL stdout so parent processes that capture stdout
        # (e.g., our asyncio subprocess capture) will see the marker regardless of logging redirection.
        try:
            # sys.__stdout__ is preserved by logging_setup (it redirects sys.stdout but keeps __stdout__)
            sys.__stdout__.write(f"TEST_SLEEP_DONE slept={seconds}\n")
            sys.__stdout__.flush()
        except Exception:
            # Fallback to regular print if __stdout__ isn't available for some reason
            print(f"TEST_SLEEP_DONE slept={seconds}")
        telemetry_logger.info('{"event":"test_sleep","status":"slept","seconds":%s}', seconds)
        return 0
    except Exception as e:
        logger.exception("test_sleep failed: %s", e)
        telemetry_logger.error('{"event":"test_sleep","status":"failed","error":"%s"}', str(e))
        return 3


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="maintenance_worker")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("proc_import", help="Run proc_config_import synchronously")

    p_post = sub.add_parser("post_stats", help="Run post-import stats stored procedure")
    p_post.add_argument("--server", required=False)
    p_post.add_argument("--database", required=False)
    p_post.add_argument("--username", required=False)
    p_post.add_argument("--password", required=False)

    # TEST helper used by integration tests to simulate a long-running task
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
            return 2
        return do_post_stats(server, database, username, password)

    if args.cmd == "test_sleep":
        return do_test_sleep(args.seconds)

    logger.error("Unknown command")
    return 2


if __name__ == "__main__":
    try:
        code = main()
        sys.exit(code)
    except Exception:
        traceback.print_exc()
        sys.exit(3)
