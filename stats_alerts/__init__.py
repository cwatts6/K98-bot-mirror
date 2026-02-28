# stats_alerts/__init__.py
"""
stats_alerts package — refactored KVK/offseason stats alert logic.

Public entrypoint:
  - send_stats_update_embed(bot, timestamp, is_kvk, is_test=False)
"""

from .interface import send_stats_update_embed

__all__ = ["send_stats_update_embed"]
