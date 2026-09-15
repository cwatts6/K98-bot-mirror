# S10B closeout and S10C documentation handoff

## Current delivery and next step — 2026-09-14

**S10B code review and repository delivery are complete; merged changes are locally pulled. No
changes have been pulled to the bot machine.** This records repository delivery, not deployment,
activation, a new live smoke or closure of retained operational gates.

Next is **S10C Legacy and Scan Export Adapters, initial review/scope only**:
[task pack](../../task_packs/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S10C%20Legacy%20and%20Scan%20Export%20Adapters.md)
and [starter](../../task_packs/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S10C%20Legacy%20and%20Scan%20Export%20Adapters.md).
The operator requested this documentation closeout and archive preparation. No S10C implementation,
new task, Git publication, SQL/provider/Discord operation, real import/export, bot-machine action,
deployment, activation or predecessor rerun is authorized by this handoff.

## Verified repository anchors

| Repository/state | Exact revision and evidence |
|---|---|
| Mirror PR #278 | [Merged](https://github.com/cwatts6/K98-bot-mirror/pull/278) at 20:13:22 UTC on 2026-09-14 as `b83f1bc8fe667602204b353ff18f9fea30a875d3`; final head `f7a25f3f87ae203e91f597b2bfe5013aef8ffd9f` |
| Production PR #585 | [Merged](https://github.com/cwatts6/k98-bot/pull/585) at 20:13:58 UTC on 2026-09-14 as `40c2e48111ebbe44d58d71269dea63a6dd9388b7`; final head `ba891035acabe6afc99abcd821ab175f83aa93f0` |
| Local Bot main/origin main | `8ae66da6e12b53781c5df0d46a8ee79314cecead`, synchronized from production merge `40c2e481` |
| Local production/main | `40c2e48111ebbe44d58d71269dea63a6dd9388b7` |
| SQL main/origin main | `3776dfa6b0892a8800d236fdf111c4d2f93c3813`, accepted and merged SQL #85; no S10B SQL delta |

Both repositories were clean at closeout entry. The operator confirms local pulls and explicitly
confirms no bot-machine pull. Local refs and exact delivered contents were checked. These are
comparison anchors, never reset instructions; preserve any later pending work.

## Exact delivered S10B content proof

The [S10A handoff's final pending table](s10a_implementation_and_s10b_handoff.md#exact-current-pending-bot-paths)
and [S7 S10B manifest](integration_implementation_manifests.md#s10b) define the delivered union.
For each merged PR, all paginated GitHub `filename` and `previous_filename` entries were compared
with every required path. Their union matched all **60 physical identities**; all **58 destination
blob hashes** matched the respective final PR head, local merged Bot main and production/main.
These counts summarize the path/blob comparisons; they do not substitute for them.

Both S9B starter/pack moves are represented by provider `previous_filename` and archive destination.
The S9B starter's base blob is `d00332e532a2982d95cb089ba7bcd9d196581586`; the pack's is
`df7412d3501da466b7c82bf1efe1452f8bd13358`. Both S10A pack/starter archive destinations were
delivered; their never-tracked active source paths were absent at the exact S10B bases
`8e60e78d850a92b6ff84c6b870b8f0c6c5254806` (mirror) and
`289bc87e1379941fd6ddafe1a18bb5e7a993d09d` (production), as recorded in the preceding handoff.
Do not require fictitious S10A rename entries or carry already-delivered documents as missing.

Production review correction `ba891035` was also applied to mirror as `f7a25f3f` before merge.
The four-file correction has identical stable patch ID `c33c779dd46276df6ecfd9698c9f1315e78c030d`;
all final PR file contents matched across repositories. No production-only correction remains.
Mirror command-governance and production command-governance/quality/scan checks passed; all review
threads were resolved. The merged delivery includes the whole mandatory documentation grouping.

## Delivered behavior and retained validation

S10B supplies durable job/resource CAS, fair account admission, immutable intent discovery and
generation loading, retained attempts/parts, private spool validation and durable provider request
budgets. Running A is not retargeted when B arrives. Registration-aware discovery retains partial
fan-out work; intent status transitions use CAS. HTTP-date cooldowns use SQL UTC, and uncertain
completion/cooldown checkpoints retain claims. The final review fix loads and compacts one pinned
period before reading the next, sharing the established compact merge and separate overall behavior.
Final compact output still scales with export size; no new live peak-memory result is claimed.

Production composition remains closed even if EXPORT_COORDINATION_ENABLED is true; the merged slice
does not wire legacy/scan clients into common admission. S10C owns those adapters. S10D/E own later
pool/recovery/rollover behavior and S11 owns deployment inventory and operational proof. Job state,
lease age, process loss or a callback timeout alone cannot release uncertain resources.

Final production correction validation: **4,433 passed / 66 skipped (179.64 s)** through the full
offline log-isolation runner; production operational logs unchanged. Focused export/delivery tests:
**135 passed**. The mirror backport reran the focused tests (**135 passed, 13.45 s**) and checked
identical source/test blobs and patch; the full suite was not unnecessarily repeated on identical
code. Architecture, deferred-items, security-routing, test selection, smoke imports, registration
(36 top-level commands, no drift), Ruff, Black and whitespace checks passed.

Security evidence remains separately identified: full S10B Changes/Deep-off scan
`6c3284aa-7c5f-4647-9299-de5feb5771c0`; mirror review correction
`42cd2d95-a259-4596-9dc7-1786b83314d6`; production compaction correction
`ad6fa8fd-01f6-4d6c-a387-d1c0b64692dc`. All completed with no findings or deferred candidates;
the final correction's two-source-file review was preserved through exact backport parity. Detailed
targets/digests and historical results remain in the [preceding handoff](s10a_implementation_and_s10b_handoff.md).
These are retained implementation results, not new tests or scans of this documentation closeout.
The four opt-in SQL tests were not executed; offline tests do not prove live SQL concurrency or
provider truth. No predecessor execution was rerun or implied by merge.

## S10C boundary and preserved contracts

The [S10C pack](../../task_packs/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S10C%20Legacy%20and%20Scan%20Export%20Adapters.md)
reproduces the exact S7 **26-path** Bot source/test boundary. Review automatic/manual legacy and
scan adapters, immutable multi-result snapshot capture with committed provenance, shared writer
admission and actual gspread/google-api request pacing. Keep SQL session admission outside
UPDATE_ALL2's own transactions, pass ownership to nested helpers, and never cross provider requests
with SQL transactions. Snapshot/capture failure must not relabel advanced mutable outputs.

Preserve the complete S7 temporal contract: running immutable A, eligible pending-only coalescing,
daily SCANORDER/history, replay/repair identity, account fairness, deterministic resource sets,
owner/fence/version CAS, server-UTC reservation/completion/cooldown and uncertain claim retention.
Preserve fixed season source and independent stats/targets/publication/roster/history/daily consumers;
supplied overall/B0 and authoritative aggregates/DKP; UTC starts, unused scans, movable within-season
windows, exact 11-10/12-10/final13-10/authorized14-10 chain, sealed input/CAS, matched UpdateID and
explicit counterpart attestation. No mixed sources, summed-fight overall, silent legacy fallback,
SourceRouting.Enabled-only activation or new top-level command. S10D/E/S11 implementation is separate.

## Retained evidence and open gates

S6-OPS01/PERF01/CAP01 remain open for their documented operational components. Preserve both uncertain
publications `e19c89ac-7977-5f28-ae4c-031807cd1728` and `54a2480a-26fb-5bad-a3f5-9321525a731c`,
all receipts, registered file IDs and retained databases/files. Do not probe, repair, delete, clear,
reuse, or reinterpret them from this closeout. Keep the accepted 5,806-player/ten-period S6 benchmark
and its exact limits in the [release evidence](release_evidence_log.md),
[readiness record](release_readiness_and_rollback.md), and archived S6 pack.

S8A's six-script/VERIFYONLY evidence, S8B's accepted 50-case smoke and actual restore, the separate
offline runner, and S8C's seven local operator checks remain distinct. See the
[S8A closeout](s8a_closeout_and_s8b_handoff.md), [S8B closeout](s8b_closeout_and_s8c_handoff.md),
[S8C closeout](s8c_closeout_and_s9a_handoff.md) and [S8C smoke record](s8c_folder_intake_smoke_evidence.md).
None becomes live Discord, current provider, bot-machine or deployment acceptance by association.

## Archive and documentation delivery rules

Only the completed S10B pack and starter move to `docs/task_packs/archive/`; reference documents,
runbooks, evidence and retained data stay available. Existing S9B/S10A archive destinations remain
delivered history. Relative links are repaired and historical instructions explicitly remain historical.

| S10B archive source at closeout base | Exact base blob | Required archive destination |
|---|---|---|
| `docs/task_packs/Codex Chat Starter - KVK Source Migration S10B Shared Export Coordination Worker and Durable Budget.md` | `30c56ca8dc871a73ac48145ad1b414ce2af4ff3b` | `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S10B Shared Export Coordination Worker and Durable Budget.md` |
| `docs/task_packs/Codex Task Pack - KVK Source Migration S10B Shared Export Coordination Worker and Durable Budget.md` | `17c05c2d0dc68c1c79ce9c94f96f765dc346243c` | `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S10B Shared Export Coordination Worker and Durable Budget.md` |

The next S10C Bot implementation PR must contain every pending Bot path below, both archive move
sides, this closeout, the S10C pack/starter and any subsequent scope/implementation documents.
Reconcile fresh Git status and expand this table if the task creates more documents. Verify exact
GitHub `filename` AND `previous_filename` coverage, or exact already-merged commit/content or
absent-at-base proof, before handoff and again at promotion. Counts alone are insufficient.
No standalone documentation PR or mixed-repository PR. This grouping is settled.

## Exact pending Bot documentation manifest

At this closeout: **47 physical Bot documentation paths**. Together with the distinct 26-path S7
S10C source/test boundary, the initial S10C Bot union is **73 physical path identities**. The exact
rows control delivery; reconcile and extend the union for approved scope changes rather than using counts.

| Action | Exact Bot path | Delivery |
|---|---|---|
| Modify | `README-DEV.md` | S10C Bot implementation PR |
| Modify | `docs/reference/ENV_REFERENCE.md` | S10C Bot implementation PR |
| Modify | `docs/reference/README.md` | S10C Bot implementation PR |
| Modify | `docs/reference/canonical_command_reference.md` | S10C Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/decision_and_evidence_register.md` | S10C Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/integration_contract_and_consumer_matrix.md` | S10C Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/integration_implementation_manifests.md` | S10C Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/phase_2_acceptance_scenarios.md` | S10C Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/phase_2_contract_and_architecture.md` | S10C Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/phase_2_evidence_and_validation_log.md` | S10C Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/phase_2_implementation_plan.md` | S10C Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/phase_2b_evidence_and_validation_log.md` | S10C Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/post_s6_handoff_log.md` | S10C Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/post_s6_integration_requirements.md` | S10C Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/release_evidence_log.md` | S10C Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/release_readiness_and_rollback.md` | S10C Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/s10a_implementation_and_s10b_handoff.md` | S10C Bot implementation PR |
| Create | `docs/reference/kvk_source_migration/s10b_closeout_and_s10c_handoff.md` | S10C Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/s8a_closeout_and_s8b_handoff.md` | S10C Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/s8b_closeout_and_s8c_handoff.md` | S10C Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/s8c_closeout_and_s9a_handoff.md` | S10C Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/s8c_folder_intake_smoke_evidence.md` | S10C Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/s8c_operator_work_instruction.md` | S10C Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/s9a_closeout_and_s9b_handoff.md` | S10C Bot implementation PR |
| Modify | `docs/reference/kvk_source_migration/s9b_closeout_and_s10a_handoff.md` | S10C Bot implementation PR |
| Modify | `docs/reference/local_sql_development.md` | S10C Bot implementation PR |
| Modify | `docs/reference/runbook_shutdown.md` | S10C Bot implementation PR |
| Modify | `docs/reference/runbook_startup.md` | S10C Bot implementation PR |
| Delete (archive source) | `docs/task_packs/Codex Chat Starter - KVK Source Migration S10B Shared Export Coordination Worker and Durable Budget.md` | S10C Bot implementation PR |
| Create | `docs/task_packs/Codex Chat Starter - KVK Source Migration S10C Legacy and Scan Export Adapters.md` | S10C Bot implementation PR |
| Delete (archive source) | `docs/task_packs/Codex Task Pack - KVK Source Migration S10B Shared Export Coordination Worker and Durable Budget.md` | S10C Bot implementation PR |
| Create | `docs/task_packs/Codex Task Pack - KVK Source Migration S10C Legacy and Scan Export Adapters.md` | S10C Bot implementation PR |
| Modify | `docs/task_packs/KVK Source Migration - Programme Pack.md` | S10C Bot implementation PR |
| Modify | `docs/task_packs/README.md` | S10C Bot implementation PR |
| Modify | `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S10A Shared Export Coordination SQL Foundation.md` | S10C Bot implementation PR |
| Create (archive destination) | `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S10B Shared Export Coordination Worker and Durable Budget.md` | S10C Bot implementation PR |
| Modify | `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S7 Integration Contract and Implementation Planning.md` | S10C Bot implementation PR |
| Modify | `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S8A SQL Foundation.md` | S10C Bot implementation PR |
| Modify | `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S9A Public Routing and Availability.md` | S10C Bot implementation PR |
| Modify | `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S9B Stats Target Card Context and Admin Dispatch.md` | S10C Bot implementation PR |
| Modify | `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S10A Shared Export Coordination SQL Foundation.md` | S10C Bot implementation PR |
| Create (archive destination) | `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S10B Shared Export Coordination Worker and Durable Budget.md` | S10C Bot implementation PR |
| Modify | `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S7 Integration Contract and Implementation Planning.md` | S10C Bot implementation PR |
| Modify | `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S8A SQL Foundation.md` | S10C Bot implementation PR |
| Modify | `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S9A Public Routing and Availability.md` | S10C Bot implementation PR |
| Modify | `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S9B Stats Target Card Context and Admin Dispatch.md` | S10C Bot implementation PR |
| Modify | `docs/task_packs/archive/README.md` | S10C Bot implementation PR |

## Separate pending SQL documentation

| SQL-repository path | Delivery |
|---|---|
| `docs/SQL_DELIVERY_LOG.md` | Next authorized SQL PR |
| `migrations/README.md` | Next authorized SQL PR |

These two documentation updates record accepted/merged S10A and S10B delivery without changing SQL.
Keep them pending in `C:/K98-bot-SQL-Server`. Include both with an independently approved S10C SQL
delta if one proves necessary, otherwise carry to S10D's SQL PR. Do not manufacture a schema delta,
create a standalone docs PR, or put SQL documents in the Bot PR. S10C's current S7 manifest reserves
no SQL implementation. The SQL repository has its own history, review and publication boundary.

## Closeout validation and authority

This change is documentation/status/navigation and task-pack archival only. Security routing is a
documented documentation-only skip for both repositories; no executable, configuration, dependency,
permission, query or persistence behavior changes. No new security scan, runtime pytest, SQL/provider/
Discord execution or benchmark is warranted for this closeout. Validate documentation links, exact
pending manifest, archive coverage, whitespace, architecture/deferred/test-selection/security-routing
scripts and separate repository status. Leave this handoff pending for the eventual implementation
PRs; do not stage, commit, publish, deploy, activate or create a new task from this closeout.

Closeout checks passed: exact 47-path pending Bot manifest and 26-path S7 S10C table parity;
architecture (zero Python changes), deferred-items (45 present Markdown files), security-routing
(zero errors/warnings), test selection, local link resolution and whitespace in both repositories.
Runtime pytest, smoke imports and command registration are deliberately skipped for this documentation-only
patch; their retained implementation results above remain unchanged. No SQL validator or SQL execution
is needed for the two status-only SQL Markdown edits. All closeout changes remain unstaged/uncommitted.
