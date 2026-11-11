> **Final merge and D5 continuation, 11 November 2026:** Private [PR740](https://github.com/cwatts6/k98-bot/pull/740) merged at `ef8aee342fbe2d91c9e8aaef34c0df6b54570803` (10:41:16 UTC), reviewed head `8b6879bf`, after all four checks passed and all four documentation threads were fixed/resolved. Final quality retry: 13,249 passed, 1,458 skipped, 19 warnings and eight subtests; import smoke and registration passed. The first final-head attempt failed the unchanged Personal Stats drain test at line 63; four focused tests and one same-head full retry passed without code changes. Root cause remains unproven and is required D5 evidence, not closed by retry. See the [D5 scope and handover](Startup%20Import%20Export%20Reliability%20-%20P02%20D5%20Scope%20and%20Handover%20-%202026-11-11.md) and [final review/validation receipt](https://github.com/cwatts6/k98-bot/pull/740#issuecomment-6793565436). Mirror PR534 aligned all 15 remaining checkpoint banners. Bot scan `e350717c-3367-4d49-a0a9-f4d113112888` covered `5ec55e3b..7cefa991`, zero findings across 94 files; the later Markdown-only delta has a precise documented skip. No deployment occurred. Earlier merge-ready and pending-CI statements below are historical.

# P02 D4 delivery and D5 handoff

Status: D4 source delivery and integration audit complete. The user authorized
D4a-e source delivery and mirror/SQL merges, then a combined private production
PR through merge readiness only. D5/D6 and operational acceptance remain open.

## Scope delivered

| Slice | Result | Evidence and limits |
| --- | --- | --- |
| D4a: installed and consumer census | Bounded source, SQL and host collectors; exact installed Bot/updater/startup reconciliation; scheduled/internal/manual caller dispositions. | Bot PR525/526/528/529/530/531; private SQL v3 and host v2 receipts; read-only MINI_AMD follow-up. 874 source files and 841 protected pins reconcile, plus 14 updater members. Inventory is scoped and does not prove absence of arbitrary future callers. |
| D4b: dependencies and permissions | Direct-child admission, guarded backup routing, authoritative sequence/wrapper references, effective configured identity checks; approved legacy retirement. | Bot PR527; SQL PR151/152/153. Hidden/denied wrapper metadata refuses, no fallback after uncertain dispatch, no new grants. Three old public roots retain their definitions/data and refuse clearly after installation; UPDATE_ALL2 and daily Rally importer continue. |
| D4c: versioned SQL package | Fixed 30-object successor with four maintenance ledgers, all six kinds/children, producer intent and receipt integration, same-transaction migration outcomes. | SQL PR154, merged SQL `ba5c6acbefba0eb89cb18842a7f6c6811096759b`. Exact predecessor/postimage/dependency checks and native rollback/commit/resume tests. Existing captures/claims/backup rows/sequence state preserved. |
| D4d: combined updater and startup | Exact installed-to-final transition, all three protected startup contracts, fixed SQL binding and existing resumable updater upgrade. | Bot PR532, reviewed source `49588b7c`; validation below. Registry adds one complete 79-member entry; all 88 old entries remain, byte cap unchanged. Candidate upgrade is required before normal combined preparation. |
| D4e: integration audit | Original findings, equivalent callers and action census reconciled; separate qualification, deployment and recovery owners retained. | This handoff and the final exact-head review/validation receipts. Source delivery does not establish deployment or whole-flow acceptance. |

## Decisions and compatibility

The user approved retirement of dbo.UPDATE_ALL, dbo.UPDATE_RALLY_DATA and dbo.TEST
if caller checks passed. Bounded installed SQL, task, source and catalog checks,
plus the user's no-manual/external-use statement, satisfy that condition. Their
old definitions are archived; refusing stubs preserve data and prevent partial
legacy mutations. This is a supported-behaviour change only for direct calls to
those three roots. No recorded recent use was found; cache/history visibility is
not a complete last-use history and cannot prove perpetual non-use.

The registry needed a bounded extension. One final combined entry covers D2/D3
and D4 together; per-slice historical entries alone cannot admit the installed
jump. No general registry redesign, historical hash rewrite or byte-cap increase
was needed. New source contracts require explicit D4 lineage over Phase 1.

All four ledgers receive stable constraint names without changing their business
schema or seed semantics. New D4 installation creates eight initial rows only;
historical backup work and old serialized captures are never adopted or cleared.
Once SQL commits, recovery is forward-only from the same verified release receipt.
No old Bot/policy fallback, reverse bigint-to-float conversion or age-based replay
is permitted by this package.

## Original obligations and remaining owners

This table closes D4's integration responsibility, not every underlying programme
finding. Accepted P01/D2/D3 work stays accepted unless new evidence shows a defect.

| Finding | D4 coverage and next owner |
| --- | --- |
| F01 | Exact delivered factory/budget source included; D5 actual player workload and cost. |
| F02 | Existing stream/effect evidence preserved; P03 exact result/closure settlement, no resend. |
| F03 | Passive read and mutation-lock contracts included; D5 both ownership orders. |
| F04 | Recheck, group/batch and accepted-action reconciliation included outside action count; P03/P04 semantics remain. |
| F05 | No history/failure evidence erased; P04 projection and original-failure convergence. |
| F06 | Existing completed-stage binding preserved; P03/P04 continuation and projection, no replay for observation. |
| F07 | Restricted diagnostic capability checked; D5 known-holder exercise, historical attribution remains unknown. |
| F08 | Protected startup and physical drain retained; D5 integrated regression, P01.1 remains accepted. |
| F09 | Observer/global ownership identity contracts included; D5 contention, P03 retained CFG-51421 work. |
| F10 | Preview and action-time mutation checks remain separate; P03 exact binding. |
| F11 | Passive status/Refresh unchanged; P01.3 accepted, broader P04 remains. |
| F12 | Observation selector/authentication source pinned; D5 saturation and shutdown. |
| F13 | No expiry/release by age introduced; P04 incident/waiting/progress classification. |
| F14 | Season SQL prerequisites retained; D5 stale tuples and both lock orders. |
| F15 | Capture/report generations preserved; P03 original-intent cache continuation. |
| F16 | Alternate backup caller/profile audit and one-request acknowledgement contract complete; D5 faults/cost. |
| F17 | Import/audit/refresh/delivery separation retained; P01.4 natural limits remain, no broad importer rewrite. |
| F18 | Final-stage receipts and optional upkeep in fixed SQL package; D5 actual combined child work. |
| F19 | Notification journal untouched; P04 admission/capacity/history, no deletion to free space. |
| F20 | Shared file ownership and late cleanup source pinned; D5 equivalent-caller physical failures/restart. |
| F21 | Configuration ledgers/direct/typed callers covered; D5 actual child work. |
| F22 | Six maintenance kinds/children and direct-child guards covered; D5 overlap and cost. |
| F23 | P01.5 calendar audit separation retained with natural limits. |
| F24 | P01.5/P01.6 custody retained, D2/D3 adoption pinned; D5 combined drain; deferred performance unchanged. |
| F25 | P01.5 primary/auxiliary outcomes retained; no cache redesign. |
| F26 | Explicit factory profiles and no automatic fallback preserved; D5 alternative-factory failures. |
| F27 | Existing 51961/51966 refusal contracts retained; P04 waiting-versus-conflict classification. |
| F28 | Cancellation/linked proof retained; P03/P04 settlement and convergence. |
| F29 | Separate Rally XLSX attempt-versus-success identity remains P03; legacy-root retirement does not close it. |
| F30 | Optional CSV separation and required custody retained; P01.4 natural limits remain. |
| F31 | Scoped consumer/caller checks and approved retirement replace unsafe legacy entry routes; active modern/importer contracts retained. |
| F32 | First failures and exact uncertain cleanup remain intact; D5 combined fault/restart qualification. |

All C01-C16 source families remain mapped: C01/C08/C14 retain P01 acceptance;
C02/C03/C05/C13/C15 cover player/configuration/factory/custody; C04/C11 cover
import/report/maintenance and legacy consumers; C06 retains P03 result/closure and
D2 scheduling; C07/C10 cover recovery, scheduled/manual and shutdown callers;
C09/C12 retain P04 history/notifications and P01.4 outcomes; C16 retains D2
snapshots and P04/F27 classification.

The fresh static action reconciliation is exactly 73/73 pairs, 52 distinct action
names across 22 kinds, four empty kinds, with zero missing or extra pairs. Generic
Recheck, group approval, historical/evidence batches and outcome-worker paths are
separately retained; an empty action set does not prove passivity. No automatic
action or blanket reapproval was added. Action-time evidence remains mandatory.

The fresh 41-root source census records 1765 Bot Python and 811 SQL files. Its
schema-definition detector still reports sequence/wrapper roots as missing:
their authoritative qualification references deliberately live outside deployable
schema snapshots and must not be mistaken for installable objects. Native and
installed dependency checks, not lexical census status, close those contracts.

## Final tuple and validation receipt

Bot D4a-d mirror PRs 525-532 are merged; D4d final reviewed source is
`49588b7c584842c520536f30a4547101a9d8be91`. SQL source PRs 150-154 are merged;
SQL documentation PR155 merged at `5520daacb0da6dcd2527219241ac36ee25843a11`.
The SQL payload remains pinned to `ba5c6acb`; the documentation successor does
not change its bytes. The private promotion PR records its exact final Bot head,
mirror equivalence, final CI and review rather than treating this source handoff
as deployment authority.

Validation evidence:

- Complete Bot regression run: 13,398 passed, 1,265 skipped, eight subtests passed
  and 43 failures in historical expectations/fixtures. All 43 were corrected and
  passed an exact rerun with production operational logs unchanged. The corrections
  preserve every historical hash and byte limit, update the current release/count,
  accept the D4 selector in test mocks and independently authenticate the complete
  D4 postimage before unchanged historical-chain assertions. No runtime change
  followed the original D4d source review.
- Broader corrected transition suites: 1,928 passed; activation scope: seven;
  reader capabilities: 15. Original focused updater/startup cases: 255; final
  D4 release cases: 23, including the complete packet/seed wiring case added after
  the full run was collected. A later clean private CI run is a separate gate;
  the initial full run is not represented as a single all-green run.
- Private offline tuple qualification authenticates 841 installed source pins,
  14 updater members, all three contracts and seven fixed SQL payload files.
  Thirteen installed/upgraded/partial/foreign refusal checks and 16 independent
  startup-observation/permission checks pass. Windows PowerShell 5.1 fixtures
  pass updater replacement 30, orchestration 11 and source custody 39 cases.
  Administrative ACL/task/control evidence is substituted where documented;
  this does not qualify actual host custody or install the candidate package.
- Architecture, deferred-item and security-routing validators, import smoke,
  command-registration, Ruff, in-process Black and whitespace checks pass.
  No command, broad permission or activation-flag change is introduced.
- D4d Changes scan `29526432-f231-4b74-8e22-edb38759f0e6` covers
  `311c7709..3b6feb91`, all 18 files, zero findings. The subsequent 38 test-only
  files were inspected separately and routed to a documented no-runtime-effect
  skip; the sealed scan is not represented as covering newer test commits.
  SQL PR154 Changes scan `247247c4-a99d-4334-8b69-1beeb706232b` covers all
  18 SQL changes with zero findings and retained native qualification. SQL PR155
  has final-head code review, two passing checks and zero unresolved threads;
  documentation-only security/runtime validation skips are recorded on its PR.

The source census was refreshed at Bot `49588b7c`; SQL source bytes are unchanged
by PR155. The recovery action census is unchanged because no runtime action table
changed. Both receipts remain private evidence, separate from installed-use proof.

The fixed SQL migration, profile/script digests and installation/recovery sequence
are in the D4d combined-transition record and SQL PR154 documentation. Private
receipts retain raw identities, definitions and job binding; none are public PR
attachments. A generated updater package is a candidate artifact, not proof that
MINI_AMD has installed it. No runtime operation occurred during D4 source delivery.

## D5 qualification and release holds

D5 owns the final combined D1-D4 candidate: compare all 14 output sets and detailed
state, exact numeric/rounding deltas and old queued payloads; run actual relevant
maintenance children, both lock orders, observer saturation and known holders;
exercise cancellation, lost ACK, commit/rollback/reset/close uncertainty, restart,
shutdown and scheduling. Simulated business calculations or provider responses
are not real-child/provider acceptance. The unrelated opt-in
test_stats_report_continuation_sql diagnostic fingerprint assertion remains
visible and must not be weakened or misclassified as a D3 failure.

Retain RCSI off, at least 8 GiB free memory and disk, log below 70 percent for
optional statistics, and version store below 512 MiB. Use warmup then at least five
balanced OFF/ON pairs: overall median ON <= OFF * 1.20 + 1000 ms, each report stage
ON <= OFF * 1.20 + 250 ms. Short observers retain three-second statements, zero
row-lock wait and bounded 30-second held metadata snapshots. The 1800-second
rehearsal cap is not a Bot timeout increase. The single 21-input allowance is
consumed; no new copy or expanded allowance is authorized. Revalidate local host,
VM and session readiness before native work. Preserve failed SQL 3961 evidence;
managed-reader exclusion does not qualify arbitrary readers or ad-hoc DDL.

D6 requires separate deployment approval after D4/D5, exact final production/SQL
revision and fresh installed source/updater/seed/effective-identity and path/ancestor
custody checks, including documentation paths. File settings are not proof of the
running process's inherited environment. Verify drain and receipts before any
same-release continuation; never force a second start or replay committed SQL.
D7/P05 retain exercised whole-flow/provider and natural acceptance. P03 actual
retained-work blockers and essential P04 corrections precede the first normal
import/export. Zero incidents is neither a safety gate nor proof of health.
