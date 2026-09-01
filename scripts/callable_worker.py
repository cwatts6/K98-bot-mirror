#!/usr/bin/env python3
"""
callable_worker.py

A small worker script used to run a Python callable in a separate process for offloaded work.

Usage:
  python scripts/callable_worker.py --module <module.path> --function <func_name> [--args '<json-array>']

Behavior:
- Ensures the repository root (parent of the scripts/ directory) is on sys.path so imports like
  "tests.test_worker_module" succeed when the worker is started via an absolute script path.
- Imports <module.path>, looks up function <func_name>.
- If args provided (JSON array), will pass them as positional args.
- If the function is a coroutine, runs via asyncio.run.
- Emits a single-line JSON result to stdout on completion:

  {
    "worker_result": true,
    "command": "callable",
    "module": "<module.path>",
    "function": "<func_name>",
    "status": "success" | "failed",
    "return": <value or str>,
    "returncode": 0,
    "details": "<optional text>"
  }
"""

from __future__ import annotations

import argparse
import asyncio
import importlib
import json
import logging
from pathlib import Path
import sys
import traceback

# Basic logging to stderr so stdout stays reserved for the JSON marker
root = logging.getLogger()
if not root.handlers:
    sh = logging.StreamHandler(sys.stderr)
    sh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    root.addHandler(sh)
root.setLevel(logging.INFO)
logger = logging.getLogger("callable_worker")


def _print_result(payload: dict):
    try:
        # Write to the real stdout to be robust against logging redirection
        sys.__stdout__.write(json.dumps(payload, default=str) + "\n")
        sys.__stdout__.flush()
    except Exception:
        # Fallback
        print(json.dumps(payload, default=str))


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--module", required=True)
    p.add_argument("--function", required=True)
    p.add_argument("--args", required=False, help="JSON array of positional args")
    args = p.parse_args(argv)

    module_name = args.module
    func_name = args.function
    raw_args = args.args

    # Ensure repo root (parent of scripts/) is on sys.path so imports like "tests.xxx" resolve.
    try:
        script_path = Path(__file__).resolve()
        repo_root = script_path.parent.parent
        repo_root_str = str(repo_root)
        if repo_root_str not in sys.path:
            sys.path.insert(0, repo_root_str)
    except Exception:
        # Non-fatal if this fails; import error will be handled below.
        logger.debug("Failed to adjust sys.path to include repo root", exc_info=True)

    try:
        module = importlib.import_module(module_name)
    except Exception as e:
        logger.exception("Failed to import module %s", module_name)
        _print_result(
            {
                "worker_result": True,
                "command": "callable",
                "module": module_name,
                "function": func_name,
                "status": "failed",
                "returncode": 2,
                "details": f"import_error: {e}",
            }
        )
        return 2

    try:
        func = getattr(module, func_name)
    except Exception as e:
        logger.exception("Function %s not found in module %s", func_name, module_name)
        _print_result(
            {
                "worker_result": True,
                "command": "callable",
                "module": module_name,
                "function": func_name,
                "status": "failed",
                "returncode": 3,
                "details": f"function_not_found: {e}",
            }
        )
        return 3

    # Parse args if provided
    call_args = []
    if raw_args:
        try:
            call_args = json.loads(raw_args)
            if not isinstance(call_args, list):
                call_args = [call_args]
        except Exception:
            # treat raw string as single-argument fallback
            call_args = [raw_args]

    try:
        logger.info("Calling %s.%s(%s)", module_name, func_name, call_args)
        if asyncio.iscoroutinefunction(func):
            result = asyncio.run(func(*call_args))
        else:
            result = func(*call_args)
        _print_result(
            {
                "worker_result": True,
                "command": "callable",
                "module": module_name,
                "function": func_name,
                "status": "success",
                "return": result,
                "returncode": 0,
            }
        )
        return 0
    except Exception as e:
        tb = traceback.format_exc()
        logger.exception("Callable failed: %s", e)
        _print_result(
            {
                "worker_result": True,
                "command": "callable",
                "module": module_name,
                "function": func_name,
                "status": "failed",
                "returncode": 4,
                "details": str(e),
                "traceback": tb,
            }
        )
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
