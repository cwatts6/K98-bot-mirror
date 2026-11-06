# stats_alerts/__init__.py
"""stats_alerts package exports."""

__all__ = ["send_stats_update_embed"]


async def send_stats_update_embed(*args, **kwargs):
    """Lazily import the public stats alert entrypoint."""
    from .interface import send_stats_update_embed as _send_stats_update_embed

    return await _send_stats_update_embed(*args, **kwargs)
