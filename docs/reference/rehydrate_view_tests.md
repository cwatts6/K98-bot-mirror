```markdown
# Phase 0 — Tests (Safety & helpers)

This document explains how to run the Phase 0 unit tests we added and what to expect.

Files added:
- tests/test_event_utils_roundtrip.py
- tests/test_rehydrate_sanitize_and_fileio.py
- requirements-dev.txt

Instructions
1. From the repository root, create and activate a virtual environment (recommended):
   python -m venv .venv
   source .venv/bin/activate   # Linux/macOS
   .venv\Scripts\activate      # Windows

2. Install developer requirements:
   pip install -r requirements-dev.txt

3. Run tests:
   pytest -q

Expected output
- All tests should pass. You'll see output like:

  $ pytest -q
  3 passed

- If any test fails, the pytest output will show failing assertions and stack traces. The tests are small and self-contained:
  - event_utils roundtrip: checks ISO serialization and timezone-aware parsing
  - sanitize & fileio: checks _sanitize_prefix, atomic JSON write/read and read_json_safe default behavior

Notes
- Tests run against the repository modules in-place. Run them from the repository root so Python imports find the package modules.
- These tests do NOT change any runtime behavior — they only exercise helpers for correctness and safety.
```
