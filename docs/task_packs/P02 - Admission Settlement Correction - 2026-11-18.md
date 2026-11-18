# P02 admission settlement correction

## Approved scope and evidence boundary

Continue the approved offline correction from the 18 November handoff. Reduce
spurious startup refusals while preserving durable business outcomes, ownership,
no-replay rules and first-failure evidence. This work authorizes no production or
VM action, diagnostic rerun, restart, recovery, SQL change or provider action.
Publication and deployment remain separate. Reuse the existing private-promotion
checkout; preserve its unrelated untracked qualification scripts and task packs.

The 05:48 predecessor refusal and 08:36 successor refusal are distinct. Saved
observations reproduce the predecessor's rejection of valid deferred KVK indexes;
adding only the two approved index definitions to an offline comparison recreates
the old fingerprint exactly. This strongly supports the earlier compatibility
defect as the 05:48 cause, but the original exception detail is missing. The new
observer admits a deterministic overlap between bot and updater; simulation proves
reachability in both orders, not the historical 08:36 holder. The ordinary MGE
commander-choice row correction is not a supported cause. Deferred maintenance,
exact SQL identities and fingerprints remain accepted and unchanged.

Source baseline is `cc343e46b416402eed457997d3d0b9d15f06aa23`; its tree is identical
to the retained deployed private release `72acadedbf9a1c6a55adadfada44ebf586e408f7`.
This is offline Git/evidence verification, not a fresh production observation.
SQL source was inspected at `b924cedd53e29dd88c0e9e7b66208b4fdc1e53ba`; no SQL files
change. The installed contract's retained SQL pin remains
`8a7aace75c55a6d17c9051edef9026dc25355af8`.

## Independent design challenge and caller census

- A journal certifies protected pair publication, not bot admission settlement.
  The old verifier queried SQL even before pinning successor process handles.
- Waiting for a generic online or full-startup line can accept stale or degraded
  startup. A fixed sleep does not establish settlement. The correction correlates
  the initial result with the exact journal's bot manifest hash, PID and native
  creation value, inside the release's bounded start-log interval.
- Logs remain application-owned observations. A result only permits the separate
  source/native/SQL verifiers to run; it never replaces them or authorizes effects.
  Missing, stale, malformed, duplicated, disabled or failed results cannot pass.
  A failure followed by a later success remains a failure for this release.
- The initial startup wrapper emits only after the actual synchronous installation
  call settles, including its finally/cleanup. It uses existing `drain_thread`;
  cancellation does not detach an installation worker. `retry_recovery_admission`
  retains its existing separate behavior and cannot overwrite initial evidence.
- `VerifyStart`, `ApplyStart`, `VerifyReadiness` and `AwaitReadiness` all use the
  same sealed verifier. Exit 11 means pending publication/admission only. Hard
  verification errors are no longer swallowed and retried by `ApplyStart`.
  Existing 120-second start and 180-second readiness observation bounds remain.
- `Check-Readiness` waits for its existing online/startup markers before invoking
  successor verification, avoiding repeated SQL checks while unrelated startup
  phases are unfinished. Pre-drain SQL verification is retained.
- The explicit readiness-closeout verifier also checks initial admission for
  source policies containing this protocol. Historical pinned closeouts retain
  their prior scope. Standalone `verify_bot_sql_contracts` remains a deliberate
  diagnostic/qualification API, not a successor-readiness bypass.
- The automatic startup issuer verifies the fixed installation contract; it is
  not the competing application observer. `run_bot.py`/issuer process creation,
  journal publication, restart and ownership behavior do not change.
- Export/recovery/outcome workers are registered after admission returns. They can
  still contend with the later updater observer. Such contention remains a hard
  verification failure, with no new lock retry, shared observer lock, second
  start, business replay or readiness certificate.

## Architecture and diagnostics

`services/runtime_admission_diagnostics.py` owns one optional startup observation
in the existing log. The bot lifecycle adapter invokes it; composition records
fixed stage names around manifest/source checks, all SQL contracts, recovery
isolation, authority readiness, construction, replacement registration and final
publication. Existing `recovery_health.failure_detail`, `failure_record` and
`operation_evidence.optional` supply bounded frames, exception-chain types and
driver codes. Known reason labels never render arbitrary exception prose, locals,
connection strings or credentials. Formatter, identity-read and logging failures
do not replace installation results/exceptions. The outer warning is optional too.

No new persistent ledger, poller, SQL grant/schema/index, configuration policy,
command/view logic or provider operation is introduced. The existing Exclusive
Session zero-wait schema observation still excludes Shared transaction producers
and Exclusive maintenance. No transaction or connection-custody behavior changes.
Helper reuse and caller analysis resolved the in-scope logging/sequencing defects;
no additional unrelated refactor is included.

## Release compatibility

The installed updater needs the reviewed new verifier, source runner and exact
`p02_admission_settlement_v1` four-file runtime transition. The registry preserves
all 92 historical entries and the existing 232,448-byte bound. Only this fixed
93rd family is added. Runtime source hashes are exact LF identities; the new
module is explicitly absent at the predecessor. Partial families and unknown
bytes are refused. Tool-source copies still require exact installed-tool bytes.
No seed SQL-contract amendment, migration, activation or recovery step is selected.

Do not execute old readiness stages against the failed incarnation to make the
previous release green. A later correction release requires the normal reviewed
source/seed/start/readiness sequence and fresh host/custody evidence. The old
failed admission and completed source/seed/start receipts remain historical facts.

## Validation and review

Tests cover scheduled/deployment emission, both observer arrival orders through
the real schema helper with a deterministic lock model, failed/missing/stale/wrong
incarnation results, post-admission worker contention, bounded waiting, no second
start, original exception identity, chain codes/frames, secret omission and
optional logging failures. Final generated updater payloads are hash-checked;
their actual PowerShell action bodies run in Windows PowerShell 5.1 with effects
and clock substituted. Isolated Python exercises the packaged verifier without
application or SQL imports. Native SQL/full Discord overlap remains unproven.

Initial existing regression batch: 456 passed. Initial new behavior batch: 28
passed. Packaged harness initially failed five cases because extracted script
blocks lacked `$PSScriptRoot`; the fixture now supplies its explicit temporary
root. A registry reserialization exceeded its unchanged byte limit and caused
108 failures/71 passes; original compact formatting was restored, preserving
every historical entry. A subsequent historical count assertion needed the new
family accounted for (1 failure/59 passes). The corrected updater/maintenance
batch passed 143 tests. These failed intermediate results are not erased.

Architecture, deferred-items, security-routing and explicit test-selection gates
passed. Registration remains 36 top-level/102 grouped. Import smoke initially
failed under the unconfigured sandbox output encoding; the isolated test-mode,
UTF-8 invocation passed. Full offline regression and final review results belong
in the additive release handoff, not in historical qualification receipts.

Security routing: exact Bot Changes review, Deep off, from the baseline above to
the immutable correction commit. SQL has no patch, so a SQL Changes review is a
documented no-diff skip. No full-codebase or deep audit is selected. Local
implementation review also uses the K98 PR-review checklist.

Additional review coverage executes the actual on-ready callback with effects
substituted, its real drain helper and the new observation wrapper. Worker
registration follows the settled result on both success and failure, including
failure of the outer optional warning. The initial fixture assumed a module-level
Pillow `show` attribute (2 failed/90 passed); that fixture assumption was corrected
and the complete callback/registry batch passed 92 tests. Historical transition
tests now count the single added entry while retaining all historical slice and
member hashes. No accepted history or earlier test failure was rewritten.

Two formal Changes setup attempts could not initialise this worktree, reporting
`Review changes requires a non-bare Git worktree with a resolvable HEAD.` Git
independently confirms both commits and the non-bare worktree. No scan ID or sealed
report exists, and the mandatory security gate remains incomplete. The additive
offline release handoff records this blocker and the manual review separately;
it must not be presented as merge/promotion approval.

The broad offline run also identified an unrelated SQL-checkout byte issue:
19 unchanged reconstruction tests reject CRLF `reviewed_sources.json` bytes;
an in-memory LF comparison matches their immutable historical hash exactly.
The SQL checkout and pins were not changed. The separate deferred item and retained
failure receipt are in the additive handoff under
`.codex_artifacts/p02-admission-correction-20261118/`.

## Preserved programme accounting

`Qualification-Completion-v1/adjudication-01.json` remains the accounting owner:
setup remaining 400; native 563 (grouped 389); Windows 42 (grouped 13); control 0;
prior control reservation 32; observed insertion intents 7; generated reserved
91,244 and remaining 908,756; historical rows 95 and inputs 21. No refunds or
resets. Offline work spends none of these allowances. Lab administrator identities,
credentials, lineage projections and connection settings never apply to production.

E1's closed attempt stays closed. Retained E2 work must not be replayed. E2-E4
remain paused pending deployment/readiness and separate receipt-driven approval.
P02 D7, actual P03 blockers, essential P04 corrections, P05 combined acceptance and
earlier natural observations remain open. A future normal end-to-end acceptance
uses a newly generated user stats file through Discord and standard destinations;
do not generate that file or start provider work for this correction.

## Mirror PR review follow-up

PR541 identified that the installed pair verifier also serves historical and
ordinary source-only successors that predate the admission marker. Its settlement
check now follows the authenticated successor policy's source inventory, matching
the closeout verifier. New-protocol successors still require settlement even when
SQL verification is not requested; historical successors retain requested SQL
checks and propagate refusal without retry. Five new regressions cover those
branches. Admission/qualified/reader/closeout tests passed 113 cases; direct
verifier/archive/package/transition regressions passed 237. Both runs left
production operational logs unchanged. Earlier results remain preserved.

This updates updater package bytes, so the earlier rehearsal installer and tool
hashes are historical. Rebuild from the final reviewed commit before release;
current host/custody and private-main binding requirements remain unchanged.
