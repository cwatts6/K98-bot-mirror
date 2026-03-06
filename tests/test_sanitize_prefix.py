# tests/test_sanitize_prefix.py
import random
import re
import string

from embed_utils import LocalTimeToggleView, sanitize_view_prefix


def random_long_string(n=300):
    # generate a long string with spaces and special chars
    chars = string.ascii_letters + string.digits + " _-!@#$%^&*()[]{};:,.<>?/\\|`~"
    return "".join(random.choice(chars) for _ in range(n))


def test_sanitize_view_prefix_basic():
    s = "My Prefix! With Spaces & Symbols"
    out = sanitize_view_prefix(s, max_len=64)
    assert isinstance(out, str)
    # only allowed chars (alnum, _ or -) plus underscore and hash suffix
    assert re.match(r"^[A-Za-z0-9_-]+_[0-9a-f]{8}$", out)


def test_sanitize_truncation_and_hash_distinguish():
    s1 = "A" * 200
    s2 = "A" * 200 + "Z"
    o1 = sanitize_view_prefix(s1, max_len=64)
    o2 = sanitize_view_prefix(s2, max_len=64)
    assert len(o1) <= 64
    assert len(o2) <= 64
    # Hash suffix should differ for different inputs — avoid collision (very high prob)
    assert o1 != o2


def test_localtimebutton_custom_id_length():
    # create a crazy prefix and ensure LocalTimeToggleView produces a button custom_id <= 100 chars
    crazy_prefix = random_long_string(400)
    view = LocalTimeToggleView(
        events=[{"name": "E", "type": "ruins", "start_time": "2025-01-01T00:00:00Z"}],
        prefix=crazy_prefix,
        timeout=None,
    )
    # find the button in children and assert custom_id length
    btns = [c for c in view.children if hasattr(c, "custom_id")]
    assert btns, "Expected at least one button in LocalTimeToggleView"
    custom_id = btns[0].custom_id
    assert isinstance(custom_id, str)
    assert len(custom_id) <= 100
