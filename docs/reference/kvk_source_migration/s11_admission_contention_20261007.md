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
`config_reader_active`, `older_queue_ticket`, or `older_sql_ticket`, with a UTC observation time,
request preparation ID, holder IDs, fence/version, and oldest eligible queue
ticket/type/ID where applicable. Resource keys are represented by SHA256, and
blocked-reason prose, account names, request bodies and credentials are omitted.
Diagnostic projections add no extra query to the pre-existing guard checks.
The SQL-stage FIFO check described below adds one read. Selecting the oldest
queue blocker does not change queue eligibility.

These DAL events are explicitly transaction-read observations, not commit proof.
`export_admission_result` separately records an acknowledged admission/refusal,
or an unknown outcome, with the same preparation ID, stage, attempt and elapsed
time. Unknown outcomes include only a bounded exception class, never its message.
This distinguishes a resource refusal from a subsequent lost acknowledgment and
lets the operator correlate retained SQL evidence without replaying execution.

SQL-stage waiters are ordered by their original account ticket too. Writing
admission checks for an older `sql_pending` preparation under the same account
mutex before claiming the shared SQL snapshot. `older_sql_ticket` records its
ID and ticket. This adds one read to SQL-stage admission, without schema or
permission changes; a newer polling thread cannot overtake the older writer.

Preflight ordering includes older `sql_pending` writers as well as `pending`
preparations. A newer configuration reader cannot acquire the account ahead of
an older writer between its provider and SQL stages, then block that writer's
SQL admission. All preflight consumers honor the retained account ticket; the
existing terminal-state exclusions and account mutex remain in place.
Delivery-job and output-rollover admission use the same waiting-state eligibility,
so those consumers also defer behind an older SQL-pending writer. The account
queue is not bypassed through a different admission entry point.

If waiting is interrupted after an acknowledged refusal and before the next
claim starts, the service uses the existing guarded withdrawal CAS, then
propagates the interruption. `wait_aborted_withdrawn` means withdrawal returned
successfully; `withdrawal_unknown` retains a failed/lost withdrawal acknowledgment
for reconciliation. An exception from the claim itself never enters this cleanup
path. Abrupt process/host loss still requires authoritative reconciliation; this
does not infer safety from elapsed time or automatically adopt abandoned tickets.
