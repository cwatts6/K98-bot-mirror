"""Compatibility shim for the canonical KVK history view module."""

from importlib import import_module
import sys

_canonical = import_module("ui.views.kvk_history_view")
sys.modules[__name__] = _canonical
