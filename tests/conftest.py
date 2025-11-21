# tests/conftest.py
# Ensure the repository root is on sys.path during pytest collection so tests can `import event_utils` etc.
# This is a small, safe helper used only for the test environment.
import os
import sys

# Determine repository root (one directory up from tests/)
_THIS_DIR = os.path.dirname(__file__)
REPO_ROOT = os.path.abspath(os.path.join(_THIS_DIR, ".."))

if REPO_ROOT not in sys.path:
    # Insert at front so local package modules shadow installed packages with same names.
    sys.path.insert(0, REPO_ROOT)
