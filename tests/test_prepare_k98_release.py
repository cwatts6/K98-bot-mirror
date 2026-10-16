from copy import deepcopy
import hashlib
import json

import pytest

from scripts.prepare_k98_release import prepare, validate_manifest, validate_updater_manifest


def specification():
    invocation = dict(file="step.ps1", arguments={"Mode": "verify"})
    return dict(
        version=1,
        release_id="cb3629f8-c848-4aec-afdf-07e5e1bf44a0",
        host="FIXTURE",
        application_sid="S-1-5-21-1-2-3-1001",
        repository="C:/fixture/repo",
        policy=dict(path="C:/fixture/policy.json", sha256="a" * 64),
        issuer_launcher=dict(path="C:/fixture/python.exe", sha256="b" * 64),
        members=[dict(name="step.ps1", sha256="c" * 64)],
        preflight=deepcopy(invocation),
        steps=[
            dict(id=kind, kind=kind, apply=deepcopy(invocation), verify=deepcopy(invocation))
            for kind in ("sql", "source", "seed", "start", "readiness")
        ],
    )


def updater_specification(count):
    value = specification()
    value["version"] = 4
    value["members"] = [
        dict(name="Release-Step.ps1", sha256="c" * 64),
        dict(name="ReleaseBindings.json", sha256="d" * 64),
    ] + [dict(name=f"source-{i:04d}.bin", sha256="e" * 64) for i in range(count - 2)]

    def invocation(action):
        return dict(
            file="Release-Step.ps1", arguments=dict(Action=action, ExpectedBindingsSHA256="d" * 64)
        )

    value["preflight"] = invocation("Preflight")
    value["steps"] = [
        dict(id=kind, kind=kind, apply=invocation(apply), verify=invocation(verify))
        for kind, apply, verify in (
            ("source", "ApplySource", "VerifySource"),
            ("seed", "ApplySeed", "VerifySeed"),
            ("start", "ApplyStart", "VerifyStart"),
            ("readiness", "AwaitReadiness", "VerifyReadiness"),
        )
    ]
    return value


@pytest.mark.parametrize("count", [243, 512])
def test_coordinated_source_inventory_fits_fixed_adapter_packet(count):
    value = updater_specification(count)
    validate_updater_manifest(value)
    assert len(json.dumps(value, separators=(",", ":")).encode()) <= 65536
    with pytest.raises(ValueError, match="Unsupported release version"):
        validate_manifest(value)
    value["steps"][0]["apply"]["arguments"]["Action"] = "ArbitraryCommand"
    with pytest.raises(ValueError, match="exact normal-updater"):
        validate_updater_manifest(value)


def test_oversized_fixed_adapter_and_generic_inventory_remain_refused():
    with pytest.raises(ValueError, match="Bounded release inventory"):
        validate_updater_manifest(updater_specification(513))
    value = specification()
    value["members"] += [dict(name=f"extra-{i}.bin", sha256="e" * 64) for i in range(128)]
    with pytest.raises(ValueError, match="Bounded release inventory"):
        validate_manifest(value)


def test_packet_preserves_exact_steps_and_calculates_pins_without_execution(tmp_path):
    source = tmp_path / "input"
    source.mkdir()
    contents = b"throw 'must never execute during preparation'\r\n"
    (source / "step.ps1").write_bytes(contents)
    runner = tmp_path / "runner.ps1"
    runner.write_bytes(b"reviewed runner")
    value = specification()
    value["members"][0].pop("sha256")
    spec = source / "spec.json"
    spec.write_text(json.dumps(value))
    output = tmp_path / "output"
    result = prepare(spec, output, runner)
    actual = json.loads((output / "release.json").read_bytes())
    assert actual["steps"] == value["steps"]
    assert actual["members"][0]["sha256"] == hashlib.sha256(contents).hexdigest()
    assert (
        result["manifest_sha256"]
        == hashlib.sha256((output / "release.json").read_bytes()).hexdigest()
    )
    assert result["production_changed"] is False
    assert (output / "step.ps1").read_bytes() == contents
    with pytest.raises(FileExistsError):
        prepare(spec, output, runner)


def test_reviewed_member_change_stops_before_output_creation(tmp_path):
    value = specification()
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps(value))
    (tmp_path / "step.ps1").write_bytes(b"changed")
    with pytest.raises(ValueError, match="changed"):
        prepare(spec, tmp_path / "output", tmp_path / "unused-runner")
    assert not (tmp_path / "output").exists()


def test_generic_packager_rejects_updater_continuation_protocol(tmp_path):
    value = specification()
    value["version"] = 4
    contents = b"reviewed arbitrary adapter"
    (tmp_path / "step.ps1").write_bytes(contents)
    value["members"][0]["sha256"] = hashlib.sha256(contents).hexdigest()
    spec = tmp_path / "spec.json"
    spec.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="Unsupported release version"):
        validate_manifest(value)
    with pytest.raises(ValueError, match="Unsupported release version"):
        prepare(spec, tmp_path / "output", tmp_path / "unused-runner")
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize(
    "name",
    ["../step.ps1", "CON.ps1", "step.ps1.", "release.json", "Deploy-K98Release.ps1", "C:/step.ps1"],
)
def test_unsafe_or_reserved_names_are_rejected(name):
    value = specification()
    value["members"][0]["name"] = name
    with pytest.raises(ValueError):
        validate_manifest(value)


@pytest.mark.parametrize(
    "damage", ["reorder", "duplicate", "missing-seed", "unlisted", "arguments", "version"]
)
def test_invalid_release_protocol_is_rejected(damage):
    value = specification()
    if damage == "reorder":
        value["steps"].reverse()
    elif damage == "duplicate":
        value["members"].append(dict(name="STEP.ps1", sha256="c" * 64))
    elif damage == "missing-seed":
        value["steps"] = [step for step in value["steps"] if step["kind"] != "seed"]
    elif damage == "unlisted":
        value["preflight"]["file"] = "unreviewed.ps1"
    elif damage == "arguments":
        value["steps"][0]["apply"]["arguments"] = {"Mode": ["unexpected"]}
    else:
        value["version"] = True
    with pytest.raises(ValueError):
        validate_manifest(value)
