"""Guided recovery through Bot adapter, typed IPC, broker and private authority.

Only the pipe transport and provider child are simulated. The SQL transactions,
authority composition, registration refresh and admin decisions are unchanged.
"""

from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from scripts.run_export_authority import AuthorityBroker
from services.export_execution_protocol import decode, encode
from services.export_recovery_service import ExportRecoveryAdapter
from services.export_replacement_authority import ReplacementAuthority
from services.export_replacement_recovery_adapter import ReplacementRecoveryAdapter
from services.export_replacement_verification_service import ReplacementVerificationService
from services.export_runtime_composition import AuthorityClient, ExportRuntime, RuntimeLifetime
from services.recovery_service import RecoveryService
from tests.test_export_replacement_guided_sql import (
    contained_job as contained_job,
    guided as guided,
    proposal_service as proposal_service,
    pytestmark as pytestmark,
    recovery as recovery,
    store as store,
    test_saved_admin_form_to_verified_activation_and_single_retained_queue as guided_completion,
    verification as verification,
)
from tests.test_guided_recovery import ACTOR


@pytest.fixture
def rpc(guided, monkeypatch):
    r = guided
    registration = r.service.proposals.registration
    boundary = SimpleNamespace(
        fingerprint="b" * 64,
        recheck=Mock(return_value="b" * 64),
        _manifest=dict(
            service_account_email=registration.value()["service_account_email"],
            project_id="example",
            deployment_boundary=dict(
                identity=dict(
                    client_id="test",
                    private_key_id="test",
                    credential_sha256="c" * 64,
                )
            ),
        ),
    )
    broker = AuthorityBroker(r.service.authority, registration, boundary=boundary)
    broker.replacements = ReplacementAuthority(broker)
    messages = []

    class Pipe:
        def __init__(self, handle):
            self.handle = handle

        def send(self, message):
            self.message = decode(encode(message))
            messages.append(self.message)

        def receive(self):
            result = broker.dispatch(self.message)
            return decode(encode(dict(version=1, result=result)))

    monkeypatch.setattr("core.export_execution_host.MessagePipe", Pipe)
    monkeypatch.setattr(ReplacementVerificationService, "start", ReplacementVerificationService.run)
    client = AuthorityClient(
        pipe_id=str(uuid4()),
        authority_sid="S-1-5-21-11",
        bot_sid="S-1-5-21-12",
        pipe_factory=Mock,
        verify_server=lambda _: Mock(),
        deployment_hash=boundary.fingerprint,
    )
    runtime = ExportRuntime.__new__(ExportRuntime)
    RuntimeLifetime.__init__(runtime, SimpleNamespace())
    runtime.connect, runtime.client = r.f.connect, client
    runtime.registration = runtime.base_registration = registration
    runtime._legacy_streams = SimpleNamespace()
    runtime._legacy_adapter = SimpleNamespace()
    runtime.dal = r.workflow.continuation.dal.coordinator
    base = ExportRecoveryAdapter(r.workflow.continuation.discovery, runtime.dal, None)
    adapter = ReplacementRecoveryAdapter(base, runtime=runtime, store=r.workflow.continuation.store)
    runtime.legacy.recovery_adapters = (adapter, SimpleNamespace())
    r.recovery = RecoveryService(
        r.recovery.store, {"export_job": adapter}, admin_id=1, guild_id=2, channel_id=3
    )
    r.row = r.recovery.review(ACTOR, r.row["IncidentID"])
    r.rpc_runtime, r.broker, r.messages = runtime, broker, messages
    return r


def test_admin_form_through_broker_activation_publication_and_final_private_verification(rpc):
    r = rpc
    guided_completion(r)
    current, history = r.rpc_runtime.client.effective_registration(r.rpc_runtime.base_registration)
    assert len(history) == 2 and current.fingerprint == r.activated["registration_sha256"]
    assert r.rpc_runtime.registration == current
    assert {m["operation"] for m in r.messages if m["action"] == "replacement_recovery"} >= {
        "inspect",
        "fields",
        "validate",
        "execute",
        "context",
        "reconcile",
    }
    assert all(m["deployment_hash"] == r.broker.boundary.fingerprint for m in r.messages)
    r.broker.boundary.recheck.assert_called()


def test_stale_deployment_cannot_access_recovery_or_create_actions(rpc):
    with pytest.raises(ValueError, match="deployment"):
        rpc.broker.dispatch(
            dict(
                version=1,
                action="replacement_recovery",
                operation="inspect",
                job_id=rpc.f.job,
                deployment_hash="a" * 64,
            )
        )
    assert rpc.f.sql.execute("SELECT COUNT(*) FROM #ExportReplacementActivation").fetchval() == 0
