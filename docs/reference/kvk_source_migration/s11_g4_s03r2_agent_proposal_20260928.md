# S03R2 — SQL Agent job/step and schedule metadata

PREPARED, NOT APPROVED OR EXECUTED. Exact query `.codex_artifacts/s11-g4-capture-preparation-20260926/commands/S03R2.sql.txt`.

SHA256: `bff3cf03ceec57b76deaf5dcbe3d3771d0606c34e2b471ef874686c27d0a6b2c`.

## Target and purpose

Existing SSMS connection on MINI_AMD, current database ROK_TRACKER, accepted SQL ORIGINAL_LOGIN MicrosoftAccount\cwattsconsulting@outlook.com. The explicitly authorized read target is this instance's msdb Agent catalogs: dbo.sysjobs, dbo.sysjobsteps, dbo.sysjobschedules and dbo.sysschedules. It includes all jobs regardless of enabled state or step database, since external/cross-database steps may matter to writer inventory. No USE/new connection. Chris Watts remains operator/reviewer/abort owner. Windows/UI identity remains separate. H14 executable hash is historical; S03R1's different SSMS PID label leaves native continuity unverified and is not silently adopted.

S03R1 identified SQL Agent session labels but not job effects. This separates the held S03 Agent portion from the completed session query. Job/step result: job ID/name/enabled, step ID/subsystem/database, command byte count and SHA256 of installed UTF-16 bytes only when command length <=1 MiB. No command text, secrets/credentials, proxy configuration, output-file contents, history or execution. Hashing reads command content internally; it is not a claim that no content is accessed. Hashes are retained evidence, not permission to recover or publish command content.

Schedule result: job ID/name, schedule ID/name/enabled, frequency type/interval/subday/relative/recurrence fields and active start/end dates/times. These additional relative/end fields avoid incomplete recurrence interpretation. Native Agent date/time fields have no timezone annotation here; do not label them UTC. No next-run calculation or historical execution guarantee. Job IDs and schedule IDs bind later source reconciliation without relying on names alone.

No source implementation is missing merely because this installation evidence is missing. Retained command S03 is the query basis; local deploy-source search found no matching Agent catalog references and does not prove any jobs absent. No migration or job definition executes.

## Guards, bounds and effects

Preserve the exact S03R1 prefix including isolated transaction/count/implicit guards, accepted target/login, VIEW DEFINITION and database CONTROL, session SETs, identity row and sysadmin observer gate. Its existing error text says session observer visibility; S03R2 reuses that gate for full Agent metadata visibility. This requires an already privileged observer; no grant or future application privilege is approved. Failure may follow the identity row: preserve partial output and stop.

Four result sets: one identity row; zero to 65 job/step rows; zero to 65 job/schedule rows; one completion row. Each 65-row result is an independent sentinel for a 64-row budget. LEFT JOIN retains jobs without steps (null step fields); schedule INNER JOIN means jobs without attached schedules have no row. Such absence does not rule out manual/event invocation. Shared schedules produce one row per attachment. These are not atomic inventories across statements.

One attempt, one batch, 128 KiB total output, ten-second current-tab timeout, fifteen-second operator cutoff, one-second session lock timeout, MAXDOP1 per metadata SELECT. Individual command hash eligibility <=1,048,576 bytes. A step command above that limit returns length plus null hash and requires stop; no larger read approved. Missing step is distinct from a present step with missing command/hash, which also stops. TOP and per-value hash guards do not hard-bound catalog scans, sorting or total CPU/memory/I/O; worst-case output-eligible command payload is 65 MiB, not a guaranteed execution read limit.

Effects: catalog/internal command reads, hashing, audit/resource/locking activity, scalar assignments, retained NOCOUNT ON/LOCK_TIMEOUT1000/DEADLOCK_PRIORITY LOW and editor/history/autorecovery. No job start/stop/alter, session control, SQL data/schema/permission changes, application procedure, provisioning, backup/restore, import/export, provider/Discord call, deployment/restart or Git publication.

## Execution and stop conditions

Fresh twenty-minute exact approval window required. Same existing SSMS session only; no new connection requested; five-second connection timeout unestablished and invisible automatic reconnect cannot be excluded. Stop if session is unavailable, target differs, unrelated editor work exists, or reconnect/auth/certificate prompt appears. No settings/TLS/client changes.

Replace only previous capture text with the complete batch. Verify marker `S03R2 Agent metadata completed`; confirm existing ten-second timeout and execute full batch, not selection. Start timing before Execute. Cancel at fifteen seconds; report if still running, without claiming cancellation proves server quiescence.

Stop on guards/errors, identity/visibility mismatch, either sentinel, oversized/unhashable present command, unexpected/truncated results, output >128 KiB, missing completion or timeout. Do not interpret hash mismatch against source as authorization to change jobs. No retry, pagination, cap increase, broader inspection, raw command dump, KILL, reconnect, grant/revoke or COMMIT/ROLLBACK/state repair. Preserve all four result sets, empty headers, errors and timing. No following operation inherits approval.

## Validation and proof status

Local static comparison to held S03 and successful S03R1 guards; explicit catalog targets, IDs, numeric schedule fields, per-command hash limit and separate row caps reviewed. No live syntax/catalog validation. Documentation/inert metadata preparation retains security-routing skip; no runtime implementation, permission/job change or PR. Runtime/predecessor tests, PR validators and security discovery are inapplicable.

Job metadata/hashes do not prove step effects, dependency closure, execution context, writer exclusion, owned drain, termination or no delayed effects. All seven typed G4 proofs and actual restore remain incomplete; rollout/G5 remain unapproved. Preserve pending/recovered work, isolated hotfix, single-account/admin-owned operation, fresh output/equivalent reports, deferred memory cause, withdrawn collector and separate KVK/view issues.
