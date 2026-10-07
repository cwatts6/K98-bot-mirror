# S11 bounded admission waiting

The 2026-10-07 production startup evidence showed a health probe owning account
admission from 16:39:45 through 16:39:49 UTC. The initial stats producer and
ProcConfig importer both requested admission at 16:39:48 and were withdrawn as
unavailable before execution. A manual import at 17:09:48 also received an
acknowledged admission refusal during the next health-probe cadence; its exact
resource holder was not captured. Neither traceback establishes a Google API
failure.

ProcConfig configuration reads and legacy SQL producers now retain their original
durable preparation and queue ticket while waiting for admission. The service
rechecks the existing DAL claim, at most once per second between refusals, with a
60-second waiting deadline and a maximum of 61 checks per admission stage. DAL
transaction/lock timeouts remain independent; an in-flight claim is not canceled
or assumed refused at the deadline. Health reads do not opt into waiting.

Only a returned `None` is a confirmed refusal eligible for another admission
check. Exceptions propagate immediately without retry or withdrawal because the
claim outcome may be unknown. Waiting never clears another resource owner,
changes a fence, bypasses queue order, or starts provider/producer work before a
claim succeeds. A final confirmed refusal uses the existing guarded withdrawal.
Once admitted, provider calls, SQL producers, capture, completion, and uncertain
outcome handling retain their existing behaviour; no execution is replayed.

No SQL schema, permissions, registrations, runtime flags, enrollment, or KVK
activation changes are included. Deployment still requires refreshed protected
source/runtime pins through the existing promotion process. The retained failed
export job is not replayed. Production acceptance requires a successful fresh
ProcConfig import and a fresh export with recorded provider completion.

Admission diagnostics now identify the decision at read time, rather than
inferring it from a later resource query. `export_admission_refused` records one
of `resource_owned`, `resource_blocked`, `sql_writer_active`,
`config_reader_active`, or `older_queue_ticket`, with a UTC observation time,
request preparation ID, holder IDs, fence/version, and oldest eligible queue
ticket/type/ID where applicable. Resource keys are represented by SHA256, and
blocked-reason prose, account names, request bodies and credentials are omitted.
The same existing guard queries project diagnostic columns; no extra query is
issued. Selecting the oldest queue blocker does not change queue eligibility.

These DAL events are explicitly transaction-read observations, not commit proof.
`export_admission_result` separately records an acknowledged admission/refusal,
or an unknown outcome, with the same preparation ID, stage, attempt and elapsed
time. Unknown outcomes include only a bounded exception class, never its message.
This distinguishes a resource refusal from a subsequent lost acknowledgment and
lets the operator correlate retained SQL evidence without replaying execution.
