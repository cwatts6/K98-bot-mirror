"""Explicit legacy sharing expectations in administrator-pinned registration.

External legacy editors are outside application writer coordination. These
exceptions never apply to S11 output pools or infer policy from observations.
"""

import re


def validate_legacy_file_access(policies, *, legacy_ids, pool_ids, authority_email):
    """Validate exact legacy-only policies; absent policies retain strict defaults."""
    if not isinstance(policies, dict) or len(policies) > 1024:
        raise ValueError("Bounded legacy file access policy required.")
    for file_id, policy in policies.items():
        if file_id not in legacy_ids or file_id in pool_ids:
            raise ValueError("Sharing exceptions require an exact legacy destination.")
        if not isinstance(policy, dict) or set(policy) != {
            "editors",
            "audience",
            "coordination_scope",
        }:
            raise ValueError("Exact legacy sharing policy required.")
        editors = policy["editors"]
        if (
            not isinstance(editors, list)
            or not 1 <= len(editors) <= 1000
            or any(
                not isinstance(editor, str)
                or (
                    editor != "anyone"
                    and not re.fullmatch(r"[A-Za-z0-9_.+%-]+@[A-Za-z0-9.-]+", editor)
                )
                for editor in editors
            )
            or editors != sorted(set(editors))
            or authority_email not in editors
            or not isinstance(policy["audience"], str)
            or policy["audience"] not in {"private", "anyone_reader", "anyone_writer"}
            or ("anyone" in editors) != (policy["audience"] == "anyone_writer")
            or policy["coordination_scope"] != "application_writers_only"
        ):
            raise ValueError("Exact editors, audience and legacy coordination scope required.")
    return policies
