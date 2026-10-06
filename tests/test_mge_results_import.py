from mge.mge_results_import import sha256_hex


def test_sha256_hex():
    assert len(sha256_hex(b"abc")) == 64
