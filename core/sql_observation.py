"""Mark non-authoritative observations, never authorize a write or a replay."""

from contextlib import contextmanager
from contextvars import ContextVar
import re

_observing = ContextVar("sql_observation", default=False)


class ObservationBusy(RuntimeError):
    """An observation rolled back and closed; its next check may wait."""


def observing():
    return _observing.get()


def lock_timeout(error):
    args = getattr(error, "args", ())
    return bool(
        args
        and args[0] == "42000"
        and any(isinstance(v, str) and re.search(r"\(1222\)", v[:8192]) for v in args[1:5])
    )


@contextmanager
def observation():
    token = _observing.set(True)
    try:
        yield
    finally:
        _observing.reset(token)


def observe_call(function, *args, **kwargs):
    with observation():
        return function(*args, **kwargs)
