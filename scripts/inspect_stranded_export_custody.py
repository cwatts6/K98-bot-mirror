"""Read-only adapter around a pinned recovery Inspect; never returns a review."""

from contextlib import redirect_stderr, redirect_stdout
import io
import json


class ObservationComplete(Exception):
    def __init__(self, checks):
        self.checks = checks


def observe(entry, *, manifest_path, manifest_hash, stage, collector):
    """Caller authenticates all staged bytes and the installed bootstrap first.

    Keep the original process handles retained while observing the missing-birth
    stop. The adapter ALWAYS raises out of Inspect before any review write. It
    neither replaces read_birth nor supplies a synthetic successful inspection.
    """
    if (stage / "journal" / "intent.json").exists():
        return dict(stage="CUSTODY_DIAGNOSTIC_REFUSED", failed_check="existing_recovery_intent")
    original_load = entry.__globals__["load_tool"]

    def load(path, name):
        module = original_load(path, name)
        if name != "_stranded_recovery":
            return module
        original_class = module.StrandedExportRecovery

        class Diagnostic(original_class):
            def inspect(self):
                try:
                    original_class.inspect(self)
                except ValueError as error:
                    if str(error) != "This stream has no bound restart birth evidence.":
                        raise
                    state, _, stream = self._read()
                    if set(json.loads(stream["ScopeJson"])) != {"resources"}:
                        raise ValueError("Unexpected legacy scope shape.") from None
                    # Original Inspect has already checked all rows and the live
                    # process pair. Verify it did not change before collection.
                    trace, original_state = error.__traceback__, None
                    while trace:
                        if trace.tb_frame.f_code is original_class.inspect.__code__:
                            original_state = trace.tb_frame.f_locals.get("state")
                        trace = trace.tb_next
                    if original_state != state:
                        raise ValueError("State changed before custody inspection.") from None
                    manifest = json.loads(manifest_path.read_bytes())
                    checks = collector(
                        binding=self.host.binding,
                        child_script=manifest["child_script"],
                        manifest_path=manifest_path,
                        child_id=stream["ChildIdentity"],
                    )
                    self.check_boundary()
                    if self._read()[0] != state:
                        raise ValueError("State changed during custody inspection.") from None
                    raise ObservationComplete(checks) from None
                raise ValueError("Birth binding is present; custody diagnostic not applicable.")

        module.StrandedExportRecovery = Diagnostic
        return module

    entry.__globals__["load_tool"] = load
    try:
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            entry(
                [
                    "--action",
                    "Inspect",
                    "--manifest",
                    str(manifest_path),
                    "--manifest-sha256",
                    manifest_hash,
                    "--target",
                    str(stage / "recovery-target.json"),
                    "--journal",
                    str(stage / "journal"),
                ]
            )
        raise ValueError("Unexpected inspection return.")
    except ObservationComplete as result:
        return dict(
            stage="LIVE_CUSTODY_OBSERVED_NOT_RECOVERED",
            checks=result.checks,
            production_changed=False,
            provider_requests=0,
            apply_authorized=False,
        )
    except Exception as error:
        known = {
            "Exactly one original live writer required.": "original_live_writer_count",
            "Exactly one authority-owned private writer Job required.": "authority_writer_job_count",
            "Original writer containment changed.": "writer_containment",
            "Writer incarnation differs from original authority.": "writer_identity",
            "Native handle enumeration unavailable.": "native_handle_enumeration",
            "Native handle layout is invalid.": "native_handle_layout",
            "Native handle enumeration exceeded its bound.": "native_handle_bound",
            "Native Job type could not be established.": "native_job_type",
            "Job name observation unavailable.": "native_job_name",
            "Job name layout is invalid.": "native_job_name_layout",
            "Original writer parent observation unavailable.": "native_parent_observation",
            "Authority child membership changed.": "child_membership_changed",
            "Unexpected legacy scope shape.": "unexpected_scope_shape",
            "State changed before custody inspection.": "state_changed_before_inspection",
            "State changed during custody inspection.": "state_changed_during_inspection",
            "Birth binding is present; custody diagnostic not applicable.": "birth_binding_present",
            "Original process pair exited; preserve recovery evidence.": "original_process_pair_exited",
        }
        return dict(
            stage="CUSTODY_DIAGNOSTIC_STOPPED",
            failed_check=known.get(str(error), "unclassified_stop"),
            error_type=type(error).__name__,
            production_changed=False,
            provider_requests=0,
            apply_authorized=False,
        )
    finally:
        entry.__globals__["load_tool"] = original_load
