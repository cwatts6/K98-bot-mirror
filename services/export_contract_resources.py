"""Read fixed deployment metadata from the same import source as this module.

File and zip importers share get_data(). No working-directory or loose-file
fallback is allowed. Callers still authenticate the metadata's reviewed digest;
the deployment boundary remains responsible for authenticating executable code.
"""

from pathlib import Path

_RESOURCES = frozenset({"s11_activation_scope.json", "s11_application_grants.json"})


def read_contract_resource(name):
    """Return one bounded metadata member from this code's repository/bundle."""
    if not isinstance(name, str) or name not in _RESOURCES:
        raise ValueError("Exact deployment contract resource required.")
    read = getattr(__loader__, "get_data", None)
    if not callable(read):
        raise ValueError("Deployment contract import source cannot read resources.")
    data = read(str(Path(__file__).parent.parent / "deploy" / name))
    if not isinstance(data, bytes) or not data or len(data) > 1024 * 1024:
        raise ValueError("Bounded deployment contract bytes required.")
    return data
