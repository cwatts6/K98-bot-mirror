# Diagnostics Runbook

Purpose: triage errors, crashes, performance issues, offload problems, and telemetry questions.

## Primary Artifacts

- `logs/log.txt` - application log
- `logs/error_log.txt` - warnings and operational errors
- `logs/crash.log` - unhandled exceptions and tracebacks
- `logs/telemetry_log.jsonl` - structured telemetry
- `logs/last_shutdown_info.json` - last clean shutdown summary
- `QUEUE_CACHE_FILE` - live queue state
- `COMMAND_CACHE_FILE` - command signature cache

Exact paths are defined in `constants.py` and `logging_setup.py`.

## Pytest Log Review

Pytest runs are intentionally isolated from production operational logs. Expected negative-path
ERROR/WARNING records remain visible through pytest output and `caplog`, but routine test execution
must not write to `logs/log.txt`, `logs/error_log.txt`, `logs/crash.log`, or
`logs/telemetry_log.jsonl`.

For a saved pytest review artifact, tee the command to a non-production audit file:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests 2>&1 | Tee-Object -FilePath .codex_pytest_audit.log
```

To verify that pytest did not touch production operational logs, run:

```powershell
.\.venv\Scripts\python.exe scripts\analyse_pytest_log_noise.py
```

Use production log files only for runtime diagnostics, deployment health, and bot-machine
operation review, not as the source of pytest negative-path evidence.

## Collect Diagnostics

```powershell
python scripts/collect_diagnostics.py -o diagnostics.tar.gz
```

Include full logs when needed:

```powershell
python scripts/collect_diagnostics.py --include-logs -o diagnostics.tar.gz
```

Upload options are available through:

- `--upload --s3-bucket <bucket> --s3-prefix <prefix>`
- `--upload --artifact-url <url> --artifact-token <token>`
- `DIAGNOSTICS_S3_BUCKET`
- `DIAGNOSTICS_S3_PREFIX`
- `ARTIFACT_UPLOAD_URL`
- `ARTIFACT_UPLOAD_TOKEN`

Keep upload tokens private. The diagnostics script redacts sensitive environment values in the
archive.

## Discord Operator Diagnostic Output

Operator commands use the canonical embed limits plus the diagnostic payload policy in
`core/operator_diagnostic_payloads.py`. Long previews keep complete rows or log lines in source
order and show an exact count-bearing omission marker. When a complete private attachment is
available, its content is redacted before upload and its UTF-8 byte size is checked against the
current Discord destination limit. Page edits replace or clear older attachments.

If the complete redacted attachment exceeds the destination limit, use this runbook and the local
log paths instead of copying raw logs into a broader channel or DM. Do not work around the guard by
renaming, splitting, or posting an unredacted archive. `scripts/collect_diagnostics.py` remains a
separate operator-only CLI path; no Discord command invokes it.

## Telemetry

Telemetry is written through the `telemetry` logger to `TELEMETRY_LOG_PATH`.

Useful searches:

```powershell
Select-String -Path logs\telemetry_log.jsonl -Pattern '"orphaned_offload_possible": true'
Select-String -Path logs\telemetry_log.jsonl -Pattern '"processing_pipeline_summary"'
Select-String -Path logs\telemetry_log.jsonl -Pattern '"maintenance_subproc"'
```

Common telemetry areas:

- processing pipeline summaries
- proc import and post-import stats offloads
- maintenance subprocess events
- orphaned offload markers
- SQL preflight/log-headroom results
- honor and activity import outcomes

## Offload Inspection

Use:

```powershell
python scripts/offload_admin.py list
python scripts/offload_admin.py cancel --id <offload_id> --actor "<operator>"
python scripts/offload_admin.py cancel --pid <pid> --actor "<operator>"
python scripts/offload_monitor.py --once
```

Only cancel work when you understand the import/process being interrupted.

## Live Queue Recovery

`QUEUE_CACHE_FILE` stores queued job state and message metadata. If the bot restarts, queue
helpers reload the persisted state and attempt to rehydrate the queue message. Since Phase 6K,
startup awaits live queue state load/apply before best-effort embed refresh, live queue writes use
the project atomic JSON helper, and stale/deleted queue message metadata is cleared and replaced
during embed refresh while preserving queued job display state where possible.

If recovery fails:

1. Save a copy of the queue JSON.
2. Check `logs/error_log.txt` and `logs/crash.log`.
3. Confirm the queue message/channel still exists and is accessible.
4. Clear stale metadata only after preserving the file for review.

Queue-domain redesign and SQL-backed queue persistence are deferred follow-on programmes after the
completed DL_bot Phase 6 lifecycle work. Treat investigations in this runbook as diagnostics for
the current file-backed model unless a new approved task explicitly changes the persistence model.

## Common Triage Flow

1. Check `crash.log` first for unhandled exceptions.
2. Check `error_log.txt` for operational failures.
3. Search telemetry for the relevant event, filename, `offload_id`, or `pid`.
4. Inspect persisted state under `DATA_DIR`.
5. Run focused smoke/test commands for the affected subsystem.
## Isolated Pre-KVK dispatch diagnostics (Phase 2H)

Use `/prekvk dispatch_test destination:<channel> action:run` to allocate a session and
exercise the real reserve/start/send/accept/commit flow outside seasonal routing.
Use the returned `session:<token>` on later run or status invocations. Status requires a token.
The invocation retains configured ADMIN_USER_ID AND notify-channel/accepted-child-thread rules.
Destination is required: ordinary same-guild text, excluding both production stats channels.
Requester needs view/send; bot needs view/send/embed/history. No fallback or user filesystem path.

New acknowledgements, errors, status and local-time callbacks are ephemeral and disable mentions.
The diagnostic embed is public only in the explicitly chosen destination and disables all mentions.
Existing static permission-denial wrapper text remains private and contains no user/role/everyone
mentions. Local-time buttons are bound to session owner/guild/channel/message and have no DM fallback.
The canonical embed content is unchanged; it uses current report/metadata/honor/event reads.
Appearance iteration works outside season, but unavailable seasonal data is not fabricated.

Storage: `<resolved STATS_ALERT_LOG parent>/prekvk_dispatch_diagnostics/<guild>/<channel>/<token>/`.
Server-issued tokens are 32 lowercase hexadecimal characters. Each session owns `session.json`,
`alerts.csv`, `alerts.csv.dispatch.json` (Phase 2G version 1 including generation),
`message.json`, `alerts.csv.dispatch.lck` and `message.json.lck`.
Root `sessions.lck` coordinates allocation/admission; `operation.json` records operation token,
session, PID/create time and active status. All paths reject redirection/escape. No filesystem lock
is held over Discord awaits. Lock path existence itself is not durable ownership evidence.

Keep all evidence. Capacity is 20 session directories, including incomplete initialization;
admission/inspection rejects state files above 1 MiB. No purge/reset/delete/force/clock options,
TTL stealing or automatic scavenger. Cleanup requires separately approved offline exact paths.
Reopening requires the same owner and destination. Root operation ownership blocks other processes;
unknown owner status fails closed. A positively dead operation owner may be replaced, but underlying
uncertain dispatch attempts remain blocked by the real reservation protocol.

Status is a read-only observation: no lock creation, migration, repair, reservation or receipt recovery.
Run recovers accepted receipts before rendering. Valid same-day messages edit in place; this does not
prove fresh-admission rejection. Missing/foreign messages and edit errors never trigger replacement.
Old-date references clear only isolated state with generation fencing and preserved admission rules.
Reports distinguish sent, edited, guarded, uncertain and failed, and include session, UTC,
destination, durable phase/token and positive receipt when known. A positive receipt with incomplete
projections or failed operation finalization is not a clean success. Never retry uncertain delivery
to make a smoke pass. Read-only guard observation plus deterministic real-store tests prove admission
without deleting state or forcing another live send.

Graceful teardown closes diagnostic admission, cancels/drains its active operation and once-only
filesystem finalizers before client teardown. Restart reopening retains session and receipt;
run refreshes its local-time view. Until reopening, old diagnostic buttons may be unavailable.
Generic tracked-view startup is unchanged. Current content-read executor behavior is unchanged;
this diagnostic does not complete the separate Stats executor audit.

Operator smoke after review and recorded candidate deployment (operator-approved pre-merge production-branch smoke is supported; final main verification remains separate):
1. Record deployed SHA and UTC; capture production journal/CSV/reference baseline.
2. Invoke from the permitted location with explicit diagnostic destination; retain session token.
3. Verify one mention-neutral message, valid payload/button, positive receipt and matching committed
   journal/CSV/reference. Retain link and logs.
4. Inspect status, repeat the same session and verify edit/guard without another fresh publication.
5. Gracefully restart; record SHA, reopen the same session and verify retained identity/projections
   and restored button. Compare production baseline accounting for independent natural traffic.
6. Exercise unauthorized invocation and invalid destination rejection without sending.

No live crash injection, parallel bot processes, deliberate Discord ambiguity or uncertain-state reset.
Diagnostic smoke cannot establish exactly-once or all live failures. Natural calendar/scheduler routing
is a separate Chris Watts observation; Phase 2F's next natural public save also remains separate.

Rollback: stop diagnostic admission and drain operations; preserve all session files, then redeploy
the preceding production commit. No SQL/data reset. A downgrade across Phase 2G additionally requires
stopping all writers, backing up CSV/message state/journal together and reconciling accepted/uncertain
receipts before old code resumes. Keep dispatch stopped when outcomes remain unknown.

## Phase 2H accepted smoke — 2026-09-08

Phase 2H isolated diagnostic smoke passed on deployed pre-merge commit `7794d2ae`. Phase 2G’s real reservation protocol was exercised successfully through isolated diagnostics. Production-state comparison passed for the observed status/edit operations. Natural production calendar dispatch remains separately pending.

Operator acceptance: 2026-09-08, Chris Watts. The Phase 2H pack/starter are archived.
Both Phase 2H PRs (#259 mirror / #566 production) await operator merge and final production-main
deployment/restart verification. The detailed receipt, hashes and limits are in the archived
Phase 2H task pack. Phase 2I Fighting-KVK Diagnostic Parity is the next scope-first task;
no Phase 2I implementation is approved. Phase 2F's natural public-save observation stays pending.

## Fighting-KVK preview sessions (Phase 2I)

Use `/kvk_admin test_embed destination:<channel> action:run`. Retain its issued session token;
later run/status calls use the same destination and token. Status requires a token. This replaces
post_here and the seasonal production test route; resync v1.05 through the normal command workflow.
Invoke as configured ADMIN_USER_ID in notify or an accepted child thread. Destination must be an
ordinary configured-guild text channel excluding STATS_ALERT_CHANNEL_ID and OFFSEASON_STATS_CHANNEL_ID.
Requester needs view/send; bot needs view/send/embed/history. Permission is rechecked before send/edit.

The real fighting metadata/reporting/honor reads and renderer are shared with production. No
seasonal orchestrator, Kingdom Summary, production guard/CSV/journal/message projection or cache
refresh is invoked by the preview. Operational usage/offload logs retain their existing behavior.
All new output disables all mentions. Required fighting data empty/unavailable produces no message;
optional missing honor is reported privately. No fabricated seasonal data. Payload violations reject
the complete grouped two-embed message; the preview does not redesign or further clip appearance.

Storage is `<resolved STATS_ALERT_LOG parent>/kvk_embed_diagnostics/<guild>/<channel>/<token>/`.
Version 1 session.json binds owner/guild/channel/kind=fighting_preview and a server-issued 32-hex token.
publication.json atomically records retained message ID, generations, operation phases, UTC times,
payload digest and receipts. session.lck and root sessions.lck coordinate filesystem writes; root
operation.json records process PID/create-time ownership. No file lock spans network awaits.
Phase 2H's root, schema, capacity, view and reservation stores are unchanged. Shared low-level
strict read/path/atomic-write and shutdown/_io mechanics are reused, not Pre-KVK receipt semantics.

Sent/edited requires a positive Discord receipt plus durable publication commit. Missing/foreign
messages or failed edits never cause replacement. Same-session edits retain identity across UTC
dates and restart; there are no fighting buttons or tracked views to rehydrate. Status reads only,
without locks, creation, migration or recovery. Run can reconcile an accepted receipt without a send.
An ambiguous sending/editing phase blocks run until separately reviewed offline recovery; no-ID
acceptance cannot be reconstructed by retry. A failed private acknowledgement does not undo a send.

Runs serialize within this diagnostic root; competing/unknown owners fail closed. Keep all evidence:
20 directories including incomplete allocations, 1 MiB state limit with preflight history capacity.
No purge/reset/delete/force/clock/path options, TTL stealing or automatic cleanup. Offline cleanup
requires separate approval, stopped/drained writers, exact contained paths, full backups and receipt
reconciliation. Never unlink locks under active writers. At capacity, retain evidence and reject new work.
Graceful teardown cancels/drains the new runner before client teardown alongside the Phase 2H drain.
Once-entered filesystem work completes once before cancellation propagates; no alternate-backend retry.
Existing data-reader executor/connection retries are unchanged and are not a completed executor audit.

Smoke: record reviewed/deployed SHA and UTC; capture production CSV/journal/state, Phase 2H sessions
and relevant tracker/cache baselines BEFORE first run. Run to a non-production destination, retain
token/link/receipt and verify one unchanged two-embed payload with no mentions (or honest unavailable).
Status must not mutate files/send. Repeat run must edit the same ID. Gracefully restart, retain SHA/logs,
reopen status/run and verify identity plus Phase 2H compatibility. Compare baseline throughout, accounting
for independent natural traffic. Safely verify unauthorized/excluded/revoked permission rejection.
No live crash injection, deliberate message deletion, forced duplicates or fabricated SQL/calendar data.
Candidate smoke and final-main deployment verification are separate. This does not prove production
admission, exactly-once or every live failure. Natural calendar dispatch and Phase 2F public save stay pending.

Rollback: close/drain previews, retain sessions/root records and reconcile uncertainty; deploy preceding
reviewed Phase 2H production revision and resync old command schema. New messages remain inert; no SQL
or state reset. A downgrade across Phase 2G separately requires stopping all writers and reconciling/backing
up production CSV/message/journal together. Do not blindly restore a stale snapshot or retry unknown sends.


### Approved historical fighting preview selection (Phase 2I v1.06)

`/kvk_admin test_embed destination:<test-channel> action:run kvk_no:15` starts an isolated,
explicit KVK 15 preview using that season's SQL metadata and real reporting blocks. The optional
integer selector accepts 1..2147483647; omitting it on a new session retains the current-KVK flow.
An explicit selection never falls back to current metadata or Sheets. Missing metadata or fighting
rows returns unavailable without publication. Honor is omitted for all explicitly selected-KVK
previews, and the private response explains why: the existing latest-honor reader is not bound to
that selection. Default/current production renderer behavior and honor handling are unchanged.

Explicit selections create version-2 session manifests with a durable `kvk_no`. Reopen run/status
with the same destination/token and omit `kvk_no` to reuse the saved selection, or supply the same
number. A conflicting number is rejected before dispatch or state changes. Version-1 current-KVK
sessions remain readable and retain their current-selection behavior; they cannot be retargeted.
Use a new session for historical selection. No migration of existing Phase 2I or Phase 2H files occurs.
Status remains read-only and does not query metadata/reporting. Malformed version-2 selections fail
closed. Downgrading to v1.05 or earlier leaves version-2 sessions unreadable; preserve them until the
supporting version is restored rather than rewriting/resetting their manifests.

The selector adds one option to the existing command, not a child or top-level command. Resync the
v1.06 command schema. Runtime delta: command adapter, preview runner/store/renderer, exact-season
metadata helper and lifecycle DAL reader. Tests cover real Pycord integer serialization/invocation,
SQL parameter binding, unavailable metadata, no latest/honor fallback, owner/season binding,
read-only status, reopening and same-message edits. No SQL schema, procedure, config, dependency,
calendar, reservation or production-state changes are required. SQL manifest: no SQL-repository
changes; bot-side read-only parameterized dbo.KVK_Details lookup validated against the SQL source.
Security routing remains Changes-only, Deep off, with final mirror and production target reviews.

Historical smoke: retain the existing unavailable KVK 16 session and production/Phase 2H baselines;
start a new KVK 15 session, verify title/data belong to 15 and honor is omitted, then status, repeat
run and restart/reopen with that token. All edits must retain the message ID and season. A conflicting
KVK selector must reject without sending/editing. Historical publication is not proof of natural
current-KVK dispatch, production admission or exactly-once; the separately pending observations remain.


## Accepted Phase 2I delivery — 2026-09-08

This status supersedes earlier candidate/pending-smoke statements. Chris Watts explicitly accepted
smoke testing as complete. Delivered and tested on the pre-merge production candidate; operator
merges and final main/deployed-head verification remain pending and open the next phase.

Reviewed runtime heads: mirror #260 `06f31a942a1b9b99b17769632beb58a760cb609a`; production #567
`d89e606cf83759bdda4a7b7fdeb96e17aef0d121`. Documentation-only closeout commits follow these heads.
No merge or deployment was performed by this documentation update.

Evidence supplied by the operator: current KVK 16 truthfully returned unavailable with no rows;
historical KVK 15 assembled 5 player, 5 kingdom and 4 camp entries and displayed successfully.
Status at 19:50:52 UTC retained selected KVK 15 and its committed operation; an edit at
19:51:52 UTC committed a new operation. The rejection in the instructed conflicting-selector
sequence was followed by status at 19:54:43 UTC retaining KVK 15 and the same committed operation.
Session tokens, destination identifiers and operation identifiers remain in private operator evidence. The generic rejection
text does not independently identify its cause. Operator reports restart returned the same results
and the capture helper matched the baseline with new diagnostic files created. These are operator
reports; raw message IDs, post-restart receipts and capture files were not independently inspected.

Validation: full mirror 3471 passed, 2 skipped; pinned-dependency matrix 129 passed; production
focused matrix 129 passed; applicable hooks and CI passed. Separate Changes-only, Deep-off reviews
of the two runtime heads covered all 19 changed files with zero findings. Sealed terminal reports
are retained; they are not desktop workbench scan IDs. This Markdown-only closeout has no runtime,
config, SQL, dependency, permission or persistence changes: additional pytest/security scans skipped;
documentation hooks, selector, architecture/deferred/security-routing validation remain required.

Natural production calendar dispatch is expected on 2026-09-09 morning, Europe/London; retain its
actual routing/admission/receipt evidence separately. Phase 2F natural public save remains pending.
Neither observation is closed by diagnostic success. Diagnostics do not prove exactly-once delivery
or all live failure modes. Generic tracked-view timeout and ProcConfig repair remain separate.

Next proposed scope: Phase 2J Ops Diagnostic Convergence, audit first. Preserve all Phase 1–2I
production defaults and existing Phase 2H/2I sessions. No Phase 2J runtime work is approved yet.
