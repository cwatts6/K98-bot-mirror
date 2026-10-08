"""Desktop launch token must be the issuer's exact linked ordinary logon."""

from copy import deepcopy
from types import SimpleNamespace

import pytest

from core.export_execution_host import inspect_bot_token
from core.export_startup_windows import verify_desktop_token


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "identification",
        "account",
        "session",
        "authentication",
        "groups",
        "group_attributes",
        "privilege_attributes",
        "elevated",
        "ui_access",
    ],
)
def test_desktop_token_cannot_substitute_identity_or_capabilities(damage):
    sid = "S-1-5-21-1-2-3-1001"
    # Queryable linked impersonation token and a primary token have different
    # types/TokenIds, but must describe precisely the same ordinary logon.
    linked = {
        "TokenType": 2,
        "TokenUser": (sid, 0),
        "TokenGroups": [("S-1-5-32-544", 16), ("S-1-5-5-0-1", 7)],
        "TokenPrivileges": [(1, 0)],
        "TokenElevationType": 3,
        "TokenElevation": 0,
        "TokenUIAccess": 0,
        "TokenSessionId": 3,
        "TokenStatistics": {"AuthenticationId": 42},
    }
    desktop = deepcopy(linked)
    desktop["TokenType"] = 1
    if damage == "identification":
        desktop["TokenType"] = 2
    elif damage == "account":
        desktop["TokenUser"] = ("S-1-5-18", 0)
    elif damage == "session":
        desktop["TokenSessionId"] = 4
    elif damage == "authentication":
        desktop["TokenStatistics"]["AuthenticationId"] = 43
    elif damage == "groups":
        desktop["TokenGroups"].append(("S-1-5-32-545", 7))
    elif damage == "group_attributes":
        desktop["TokenGroups"][0] = ("S-1-5-32-544", 7)
    elif damage == "privilege_attributes":
        desktop["TokenPrivileges"] = [(1, 2)]
    elif damage == "elevated":
        desktop["TokenElevation"] = 1
    elif damage == "ui_access":
        desktop["TokenUIAccess"] = 1
    fields = set(linked)
    security = SimpleNamespace(
        **{field: field for field in fields},
        TokenPrimary=1,
        GetTokenInformation=lambda token, field: token[field],
        ConvertSidToStringSid=lambda value: value,
        LookupPrivilegeName=lambda machine, luid: "SeChangeNotifyPrivilege",
    )
    profile = inspect_bot_token(linked, sid, security=security, observe_only=True)
    if damage:
        with pytest.raises(ValueError):
            verify_desktop_token(linked, desktop, profile, sid, security=security)
    else:
        verify_desktop_token(linked, desktop, profile, sid, security=security)
