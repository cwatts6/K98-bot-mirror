# P02 D5c worker/global acceptance and delta/player deferrals

Status: worker/global native deferrals accepted. The next two approved blocked
calls passed 184 offline checks and completed Changes review; ready for handoff.
No new approval, demand, runtime correction or deployment is included.

## Accepted native evidence

Receipt `d5c-worker-global-blocked-result-d742f1aaff394b549507635d52ea0b0a.json`
matches SHA256 `C47F11806B49C8B28C691D5782BBB02044C1A6EFDCFF272628C4C3DF6C9D4979`.
Independent adjudication verified 40 statements, 82 rows and 48 command units.
Both actual worker calls returned without a child entry; each test holder was
identified, granted and released. All 19 pending fields, five other completed
jobs, original first error 15247, candidate definitions, permissions, ownership,
backup state and resource gates remained unchanged. The post_import plan handle,
cache birth, last execution and count stayed identical. All five worker guards
were NoLock, transactions zero, all three connections disposed and both the
captured work birth and unique application actors independently absent.

Create-new acceptance: `.codex_artifacts/p025/d5c-worker-global-blocked-acceptance.json`.
Full host elapsed 0.9552346 seconds debits one: **1,460 native seconds remain**,
including the unchanged 1,000-second later reserve. **21 inputs remain consumed**;
zero new inputs. Two of five blocked-worker calls are complete. The single
actual-child allowance remains unused. Do not repeat completed packets.

## Next concrete execution packet

Use the same exact isolated copy, authenticated console, generation-2 request
`468fc60f-8424-4637-b576-99717c7ad062` and unchanged candidate procedures.
On the labelled holder connection acquire Exclusive/Session ownership of
`K98:TargetPublication:DeltaPreprocessing`. On the separate preflighted work
connection invoke `dbo.usp_RunMaintenance @Kind='post_import'` once. Require no
result, unchanged complete pending preimage, zero transaction, all five worker
guards NoLock and identical child-cache evidence, then release the holder once.

Only after every first-case check and release succeeds, perform the same fixed
sequence for `K98:StatsForUpload:Publish`. Authoritative source in
`C:\K98-bot-SQL-Server\sql_schema\dbo.usp_RunMaintenance.StoredProcedure.sql`
shows these guards precede the running claim and child call. These are blocked
calls three and four of the five approved by the operator. Schema-reader
deferral and the at-most-one actual-child packet remain separate.

Reuse the accepted wrapper with exact manifest/file/VM/session/database/source
protection, history, candidate, permission, resource and cleanup gates. Add fresh
equality against the accepted post_import cache identity and six child counters
before dispatch. Refuse unresolved prior connection custody before opening SQL;
never clear retained handles. These additions consume no SQL statements. Original
scripts, failed receipts, admission history and completed evidence remain intact.

Exactly 40 SQL statements plus eight reserved control units; maximum 126 rows,
512 per result/2,048 total, one-MiB receipt, three-second statement timeout,
zero-wait locks, 30-second work/42-second cleanup admission, 45+10-second outer
stop/join and 60-second manual stop. Fixed VM resources/isolation and C:/Q: eight
GiB reserves, log below 70 percent and version store below 512 MiB remain.
Two SQL actors plus one observer maximum, with observer after actor disposal.
Worker disposal precedes holder disposal; uncertain worker close retains holder
custody and stops. No release/close retry, demand replay, direct child call,
import/report/backup dispatch, permission/setting change or new input is allowed.

Packet three of the approved five maintenance packets covers both cases; the
remaining schema and actual-child packets still fit that sequence. Missing cache
or changed plan birth is a refusal, never evidence of no execution. If any child
entry unexpectedly occurs, preserve the result and reconcile the single-child
allowance before any further work. No success can be claimed from intent alone.

## Validation and review decision

Run the offline PS5.1 validator using injected readers/actors only. Cover inherited
identity/budget/state/cache/release/closure failures, both exact lock parameters,
accepted preflight counter/cache drift and unresolved custody refusal. Preserve
any first failed offline log and validator. No native rehearsal during preparation.

Security decision: **Changes**, Deep off, exact four-file review snapshot based
on `c876d4037a77cee57560e70f234b3e7362a9a152`: new wrapper, validator, manifest and
this document. SQL access and physical ownership warrant review; no repository
audit. Review all files and directly supporting SQL source. No SQL source change.
Run architecture, deferred, security-routing and explicit-path test selection.
Full application pytest/smoke/command-registration/native fixtures are skipped:
this packet changes only test orchestration and must not bootstrap unrelated
application or native workloads. No new deferred optimisation is introduced.

After completed review, hand off the hash-pinned packet once in the existing
elevated console. Capture full host elapsed time. On error/incomplete output,
stop without retry, reset or evidence deletion. Adjudicate before further work.

Offline validation passed **184 checks**. Two initial harness failures were
PowerShell singleton/nested-array shaping in the new negative-test fixtures;
both validator versions and failed logs are preserved separately. The correction
keeps fixture collections as arrays before mutation. No executable control was
weakened and no native attempt occurred. Final log:
`.codex_artifacts/p025/d5c-delta-player-blocked-offline-final.txt`.

## Completed review and handoff

Changes scan `69908620-f188-415d-a908-6ed59e6fc4ab` completed with zero findings
and all four files covered. Base `c876d4037a77cee57560e70f234b3e7362a9a152`,
head `9377de7dd2a08def407c1224313561ee4b21e964`; Deep off. Independent review
covered the complete wrapper and validator; parent review covered the manifest
and plan plus authoritative SQL context. Final draft save was confirmed before
completion, and sealed findings/coverage were read back. Measured usage:
1,524,423 total tokens, including 1,501,952 cached input tokens.

Architecture (zero changed Python files), deferred (one Markdown file), security
routing (zero errors/warnings), explicit-path test selection and review-snapshot
whitespace checks passed. The broader suggested suites are skipped for the
bounded reasons above. All four files matched the snapshot before this status
record; executable and manifest bytes remain unchanged. Original HEAD/index and
existing runtime changes were preserved. No packet intent/result exists yet.

Script SHA256 `9A1E24C9EA465176EF579DCF93F5664625DF2794D3E8E0120F8CFF327CCDB4FD`.
Manifest SHA256 `5eaf2fad533cecece592576f6041187051bde761746dede11b42450ac64d7212`.
Run once in the existing D5bReports console; adjudicate before further work.
This review-status addition and reconciliation-ledger update change no executable
or security boundary and do not require a second Changes scan.
