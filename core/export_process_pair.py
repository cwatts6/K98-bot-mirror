"""Manual process-pair provisioning; immutable expectations precede admission.

No process, SQL connection or file is opened on import. A reviewed static plan
and templates are inputs, never inferred from installed runtime metadata.
"""

from copy import deepcopy
import hashlib
from pathlib import PureWindowsPath
import re

from core.export_process_identity import validate_process_bindings, validate_token_profile
from services.export_execution_protocol import encode

ROLES = ("authority", "bot")


def validate_plan(plan):
    fields = {
        "version",
        "source_hashes",
        "application_sid",
        "token_profiles",
        "python",
        "python_sha256",
        "templates",
        "manifests",
        "commit_file",
    }
    if (
        not isinstance(plan, dict)
        or set(plan) != fields
        or type(plan["version"]) is not int
        or plan["version"] != 1
    ):
        raise ValueError("Exact reviewed manual process-pair plan required.")
    if set(plan["token_profiles"]) != set(ROLES):
        raise ValueError("Reviewed ordinary token profiles required for both roles.")
    for profile in plan["token_profiles"].values():
        validate_token_profile(profile, plan["application_sid"])
        if profile["elevated"] or profile["ui_access"]:
            raise ValueError("Application processes must remain ordinary, unelevated processes.")
    if not re.fullmatch(r"[0-9a-f]{64}", plan["python_sha256"]):
        raise ValueError("Reviewed interpreter digest required.")
    if set(plan["templates"]) != set(ROLES) or set(plan["manifests"]) != set(ROLES):
        raise ValueError("Both explicit templates and destinations required.")
    paths = [plan["python"], plan["commit_file"], *plan["manifests"].values()]
    for reference in plan["templates"].values():
        if set(reference) != {"path", "sha256"} or not re.fullmatch(
            r"[0-9a-f]{64}", reference["sha256"]
        ):
            raise ValueError("Exact reviewed template reference required.")
        paths.append(reference["path"])
    if any(not PureWindowsPath(path).is_absolute() for path in paths):
        raise ValueError("Absolute provisioned paths required.")
    if len({PureWindowsPath(path) for path in paths}) != len(paths):
        raise ValueError("Distinct interpreter, template and publication paths required.")
    return plan


def verify_role(descriptor, role, plan):
    from core.export_process_identity import validate_process_descriptor

    if role not in ROLES:
        raise ValueError("Exact application role required.")
    validate_process_descriptor(descriptor, plan["application_sid"])
    if (
        descriptor["token_profile"] != plan["token_profiles"][role]
        or PureWindowsPath(descriptor["executable"]) != PureWindowsPath(plan["python"])
        or descriptor["sha256"] != plan["python_sha256"]
    ):
        raise ValueError("Actual process differs from reviewed role identity.")


def bind_templates(plan, templates, bindings):
    validate_plan(plan)
    validate_process_bindings(bindings, plan["application_sid"])
    for role in ROLES:
        verify_role(bindings[role], role, plan)
    authority, bot = (deepcopy(templates[role]) for role in ROLES)
    boundary = authority["deployment_boundary"]
    # Only these dynamic fields may be filled. Deployment/review/registration,
    # all seven review records and SQL expectations remain reviewed inputs.
    if any(
        value is not None
        for value in (
            authority["process_bindings"],
            boundary["process_bindings"],
            bot["authority"]["process_bindings"],
            bot["authority"]["deployment_hash"],
        )
    ):
        raise ValueError("Fresh unbound templates required; old incarnations cannot be reused.")
    authority["process_bindings"] = deepcopy(bindings)
    boundary["process_bindings"] = deepcopy(bindings)
    bot["authority"]["process_bindings"] = deepcopy(bindings)
    bot["authority"]["deployment_hash"] = hashlib.sha256(encode(boundary)).hexdigest()
    if (
        any(value["source_hashes"] != plan["source_hashes"] for value in (authority, bot))
        or bot["registration"] != authority["runtime_registration"]
        or bot["sql_contract"] != authority["sql_contract"]
        or any(
            bot["authority"][key] != authority[key]
            for key in ("authority_sid", "bot_sid", "pipe_id", "trust_model")
        )
    ):
        raise ValueError("Reviewed Bot and authority contracts differ.")
    return dict(authority=authority, bot=bot)


def watchdog_launch(python, root, *, coordination, intake, recovery, plan):
    """Keep flags-off launch unchanged; every S11 launch uses a held Bot gate."""
    from pathlib import Path

    if not (coordination or intake or recovery):
        return [python, str(Path(root) / "DL_bot.py")], False
    if not coordination or not plan or not Path(plan).is_absolute():
        raise ValueError("Coordinated startup requires an absolute reviewed manual launch plan.")
    return [
        python,
        "-I",
        "-B",
        str(Path(root) / "scripts/run_export_process_gate.py"),
        "--role",
        "bot",
        "--plan",
        plan,
    ], True


def publication(plan_raw, manifests):
    return {
        "version": 1,
        "plan_sha256": hashlib.sha256(plan_raw).hexdigest(),
        "manifests": {role: hashlib.sha256(encode(manifests[role])).hexdigest() for role in ROLES},
    }
