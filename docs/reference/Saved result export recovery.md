# Saved result export recovery

P03a.1 implements one explicitly reviewed recovery of an uncertain legacy export with
one frozen mutation stream and a saved, validated result for its final dispatched
request. It records that result, renews closure, and abandons the partial export using
the existing legacy closeout. The original failure, old seal, destinations and URLs
remain unchanged. It never calls a provider, reruns an import, or reports complete delivery.

This is active recovery, not passive monitoring. Normal runtime recurrence prevention
is P03a.2 and is not supplied by this standalone runner. Production operation requires
separate authorization of the exact packet and current preflight; source implementation
approval is not permission to apply it. No SQL migration or new privilege is required.

## Preparation and compatibility

Use a fresh output directory outside Git and a private target JSON. The target requires
canonical UUIDs for `job_id`, `owner_id`, `session_id`, `stream_id`, `child_id`,
`request_id`, `response_reference`, `closure_reference`; positive integers for `fence`,
`job_version`, `stream_version`, `last_sequence`; and lowercase SHA-256 hex for
`registration_sha256`, `response_sha256`, `closure_sha256`. The runner binds
`manifest_sha256` independently from the verified installed manifest. Optional previous
packet IDs use the existing bounded `previous_packet_ids` contract. Any previous started
packet must be resumed or explicitly investigated; a new packet cannot bypass it.

The response reference names the existing encrypted request-result document, not a
summary or raw response copied into a new file. The closure reference names the original
saved stopped-child seal. The full request/event history, payloads, response protocol,
registration, original digest and ownership must validate. Missing evidence is not success.

Run `scripts/build_saved_result_recovery_packet.py --target <absolute-private-json>
--output <absolute-new-directory>` with the reviewed development interpreter. The builder
copies a fixed inventory, hashes every member and returns packet/launcher SHA-256 values.
It does not connect to SQL or make the output executable approval. Preserve the directory
if interrupted; do not reuse a partially built directory. Never commit or publish a packet
containing operational identities. Transfer and protect it through the existing Windows
ownership/access workflow; verify the separately reviewed launcher hash before execution.

The protected launcher requires Windows PowerShell 5.1 on MINI_AMD, elevated installed
deployment identity, and the installed pinned Python/authority manifest. It stages fixed
files in the protected recovery tree. The Python process runs with `-I -B`, loads the
authenticated installed modules, clears inherited SQL overrides, and uses only the
installed application's dedicated connection configuration. It retains the original Bot
and authority process handles and rechecks their identities before each mutation. It
does not require a normal Bot restart first or alter the installed source. Qualify these
checks against the actual installed package before authorizing production execution.

## Review, execution and restart

`Invoke-SavedExportResultRecovery.ps1 -Action Inspect -PacketSHA256 <reviewed-hash>`
performs active bounded SQL snapshots and full private verification, then writes an
immutable review and prints its token. A fresh inspection can contend with the held
account; it is never installed as a poller. Review identifies the exact partial output
abandonment decision. It is not an account-clear command.

After the exact operational decision is authorized, `-Action Apply` with the same
packet hash and `-ReviewToken` fixes one event/action identity in the protected journal.
It resumes the next unfinished step automatically. Temporary contention backs off at
250/500/1,000/2,000 ms, capped at five seconds, then 30 seconds after a 15-second burst.
No connection/SQL lock is held while sleeping. It reports one waiting transition after
five minutes without progress. Diagnostic output failure cannot invalidate a result.
After the durable verified receipt is saved, final console write/flush failure also
preserves success and prevents a failing interpreter-exit flush. The protected verified
journal remains the completion evidence when console output is unavailable.

Every retry rereads exact SQL state; it never blindly repeats an uncertain mutation.
Connection cleanup must complete before retry eligibility. Closeout intent, including its
private receipt reference, is saved before SQL. A committed closeout with a lost reply
converges to the matching durable receipt. Restarting the tool uses the same protected
journal and token; changed original process/session/deployment binding stops recovery.
Partial or conflicting journal files fail closed and are preserved for investigation.

Success is `PARTIAL_EXPORT_CLOSED` with the exact closeout action ID and zero provider
requests. The old job is failed/abandoned; subsequent normal exports may use the same
URLs. The runner's result does not prove a subsequent export or close every monitoring
incident. P03a.2/P04 own ongoing automatic projection convergence.

## Preservation and rollback

The old closure is never overwritten. A new seal binds the updated complete journal to
the original positive child termination evidence. SQL account exclusion spans the short
ownership snapshot/CAS and the transition's own transaction; private I/O remains outside.
The full verifier is reused for a recovery-only projected closed history before any write,
and verifies real durable closure again before release. Projected evidence never proves
SQL commit. Native tests pin the digest's existing SQL Server GUID encoding.

Stopping/disabling the runner leaves all receipts and reservations intact at their actual
stage. Do not delete events, reverse closeout, reacquire released ownership, or replay an
export as rollback. Preserve the entire packet/journal and both old/new evidence files.
Old installed code reads the standard SQL receipt shapes but cannot be assumed to resume
the new recovery journal. Use the same reviewed runner for a partial recovery.

## Qualification boundaries

Offline tests cover valid and invalid private proofs, changed ownership, restart at each
stage, lost replies, cleanup refusal and optional notification failure. Opt-in native tests
use fresh local disposable databases, real restricted-login procedure bodies, actual DPAPI
under the development identity and immutable fsynced journal files. Cases include all three
lost replies, three-second contention and 177 complete requests. Unrelated table foreign
keys are omitted by the established synthetic fixture; this is not installation validation.
Launcher tests check PowerShell 5.1 parsing, exact hashes and ACL/reparse rejection using
surrogate ACL fixtures. They do not establish the installed machine's custody or liveness.

Before production: verify the immutable reviewed package, actual source/SQL compatibility,
protected directory/identity/process bindings, full saved production proof and exact action
receipt/projection expectations. This is one operational authorization, not confirmations
between the internal recovery stages. Review source changes with `k98-security-review-routing`
and `security-diff-scan`: Scan type Changes, exact Git diff, Deep off.
