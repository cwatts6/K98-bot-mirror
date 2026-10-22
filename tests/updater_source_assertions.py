"""Check historical transition pins through the separately pinned P0 successor."""

from scripts import p0a_release, prepare_k98_update


def historical_runtime_hash(root, path):
    actual = prepare_k98_update.sha256((root / path).read_bytes().replace(b"\r\n", b"\n"))
    successor = next((r for r in p0a_release.specification()["sources"] if r["path"] == path), None)
    if successor is None:
        return actual
    # Historical bundle tests still check their original final preimage. The
    # current runtime must independently match the installed coordinated policy.
    assert actual == successor["after"], path
    assert successor["before"] is not None, path
    return successor["before"]
