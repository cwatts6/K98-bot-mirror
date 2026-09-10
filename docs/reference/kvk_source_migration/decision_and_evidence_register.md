# KVK Source Migration — Decision and Evidence Register

## Current KVK delivery status - 2026-09-10

**S1 is accepted and merged** through mirror PR #263 and production PR #570. Its archived
200-test smoke and restart/startup evidence remain historical S1 results.

**S2A is complete, operator accepted and merged.** SQL [PR #78](https://github.com/cwatts6/K98-bot-SQL-Server/pull/78)
merged as `845a25fe66b1d2365fb38720390b4dadf50baa67`; mirror
[PR #264](https://github.com/cwatts6/K98-bot-mirror/pull/264) merged as
`9fc0255dbaa0cbcb80c63c563657dad90bd5bcec` on 2026-09-10. Review fixes passed 401 static
assertions and 96 disposable SQL rejection cases, with twelve-table rollback verified.

**S2B is complete, accepted and merged:** SQL #79, mirror #265 and private bot #572
merged on 2026-09-10. Final validation passed 265 static assertions and 144 disposable SQL
rejections with 25-table rollback; the seven-file review-fix Changes scan found zero issues.
**S3A is complete, smoke accepted and merged.** Mirror #266 merged at 11:28:48 UTC
(`3154997fa2dfc124da75ee35dca79463c3196a43`); private bot #573 merged at 11:29:18 UTC
(`140fc89765b1d6ec8418ac6f6d039e575419c29e`) on 2026-09-10. At the S3A checkpoint, local mirror main was
`9d08b3bf9e7cac6c95db1c4a120c8bf0aad7475f` after synchronization; SQL main remains
`44afa315dd6cbfe9fec101f2a39a62e534f5b583`. Operator smoke passed 77 tests with operational
logs unchanged and registration 36/100 without drift. The S3A pack/starter are archived.
**S3B is complete, operator smoke accepted and merged.** Mirror
[PR #267](https://github.com/cwatts6/K98-bot-mirror/pull/267) merged at 13:59:47 UTC as
`e915f9727f9492fe4ecc02b5c0d9f3c6e443be13`; private bot
[PR #574](https://github.com/cwatts6/k98-bot/pull/574) merged at 14:01:14 UTC as
`a8ad9f1d81cfb7884a9cdcc0b067c4346a204488` on 2026-09-10.
Operator post-merge smoke on mirror main `e915f972`: import smoke passed, registration
36/100 without drift or duplicates, **36 tests passed in 9.11s** (4 publication + 32 SQL).
Current synchronized local mirror main is `02385a0edc0ec83f77241e02648eabb3b7640ea6`;
local production/main is `a8ad9f1d81cfb7884a9cdcc0b067c4346a204488`; SQL main remains
`44afa315dd6cbfe9fec101f2a39a62e534f5b583`. Both repos were clean at closeout entry.
S3B pack/starter are archived. **Next: S4A Shared Reports and Cards in a new chat, with
separate S4A G3 approval.** Preserve pending S3B closeout docs and both archive moves
for the eventual separately authorized S4A PR; its pack contains the complete manifest.
S3B's latest full-suite rerun stalled around 19% and remains incomplete; the accepted smoke
does not replace it. The earlier 3,764-pass full result is pre-review-fix evidence.
The operator confirms local pulls completed; no changes were pulled to the bot machine.
Repository merges do not establish production SQL deployment or source activation.
Do not repeat S1/S2A/S2B/S3A/S3B as unstarted slices. The [local SQL development reference](../local_sql_development.md) records the reusable K98DEV
instance, retained S2A evidence database and per-slice target authorization requirements.
No production SQL deployment, bot-machine update/restart or source activation is part of this
handoff. Earlier pending/preparation/review-in-progress wording below is historical.

**Date:** 2026-09-07. **Version:** 1.0. **Status:** Planning baseline; current-code validation pending Codex Phase 1.

This file distinguishes desired behaviour from preliminary sample findings and implementation unknowns. It controls interpretation of the earlier assessment. Do not copy superseded recommendations from that assessment into implementation requirements.

## 1. Decision provenance

| Decision IDs | Operator statement / time in UTC | Interpretation |
|---|---|---|
| D01–D03, D07, D12–D13 | 2026-09-07 13:09:58; reinforced 16:33:22 | Audit current import and all outputs; assess a separate route while keeping the old path; player differences versus aggregate selection; prefer existing window/camp-map structures and workflow; channel changes possible but not chosen. |
| D04–D06 | 2026-09-07 15:19:43 | Retain all 36 kingdoms. A separately supplied master-baseline workbook defines eligible players. Ignore later-only governors; no player gain without a starting observation. |
| D08–D10 | 2026-09-07 15:19:43 | Trust imported kingdom/camp data including DKP. Provider has exact tier-death split but cannot export it. Keep one total-deaths player input and existing `WeightDeadsZ`; no extra sheet columns. |
| D11 | 2026-09-07 16:33:22 | Timestamp timezone is always UTC and represents scan start. Similarity with legacy implementation is an audit hypothesis, not a reason to change the requirement. |
| Repository locations | 2026-09-07 14:06:02 | Operator identifies both local repos and corresponding GitHub repos as synced. Codex must verify actual checkout/commit and separately label deployed-state evidence. |
| Audit-first Codex programme | 2026-09-07 16:33:22 | First task validates findings, logic and decisions using Codex's repo/local access; no blanket implementation approval. |

The complete D01–D13 requirements are in the programme pack. Do not interpret “validate decisions” as permission to discard explicit operator requirements. Verify feasibility, find conflicts and propose the minimum correction where needed.

## 2. Supersession register — read before earlier analysis

| Earlier assessment / advice | Current status | Controlling rule |
|---|---|---|
| Recalculate canonical kingdom/camp DKP ourselves. | **Superseded.** | Imported aggregate DKP is authoritative (D08). |
| Require exact T4/T5 split or provider DKP formula before progressing. | **Superseded.** | The provider already has the split and calculates DKP; no need to obtain unavailable fields. Structural/precision validation remains required. |
| Consider extra tier-death weights in `KVK_DKPWeights`. | **Superseded for this change.** | Keep the existing single player-deaths weight. No extra tier-death columns (D09). |
| Ask whether to import only 1198 or all kingdoms. | **Resolved.** | All 36 kingdoms for this KVK (D04). |
| Backfill later-only players to include them in results. | **Superseded as a default.** | Master-baseline whitelist; later-only governors excluded (D05). Missing window endpoints still produce no calculable gain (D06). |
| Timezone and start/completion meaning are unknown. | **Resolved.** | UTC scan start (D11). Exact filename grammar and database mapping are not yet verified. |
| Source DKP mismatch demonstrates incorrect provider values. | **Not a supported conclusion.** | A calculation lacking the source tier split is not a validity test for authoritative aggregate DKP. |
| Source-sheet KVK-16 gaps prove live SQL is missing rows. | **Never verified.** | Read current configuration/database evidence or label unavailable. |
| Public repo listings mean implementation access/audit is complete. | **Not evidence of completion.** | Codex must read the source at actual commits and trace dependencies. |

Preserve the historical assessment unchanged in private evidence for traceability. It is not an active requirements document.

## 3. Input inventory

File references are stable roles for this programme; filenames can later change without changing their meaning. Original bytes and SHA-256 hashes are in the private bundle's `evidence_manifest.json`.

| Role | Original source file | Intended evidential use |
|---|---|---|
| P1 | `1198_auto_pass_lvl4_before_2026-09-05_1526.xlsx` | Example player snapshot at 2026-09-05 15:26 UTC scan start; not designated master roster. |
| P2 | `1198_end_of_zone_5_2026-09-07_0721.xlsx` | Example player snapshot at 2026-09-07 07:21 UTC scan start. |
| A1 | `kdall-stats-26aug4am-to-7sep7am.xlsx` | Authoritative kingdom/camp totals and DKP; exact report-period/scan association remains to validate. Do not infer missing minute precision or a database scan ID from the name. |
| L1 | `1086045_06_26_2026,_11_04_25_PM (2).xlsx` | Legacy input contract example; different period/population from P1/P2/A1. |
| B0 | **Not yet supplied / not yet designated** | Master-baseline workbook controlling eligible Governor IDs. Do not manufacture a workbook or silently choose P1. |

Private bundle also includes the earlier assessment and its original evidence CSVs/manifest. No current repository checkout, database dump or credential material is packaged.

## 4. Preliminary source findings to reproduce

All rows below are **earlier assessment observations**, not new Phase-1 passes. Status starts `pending reproduction`. Original sheet/range references are leads; Codex must validate using current supplied bytes. Diagnostic agreement does not approve semantic interchangeability.

| Claim | Earlier observation | Evidence / method to validate |
|---|---|---|
| E01 | P1: 5,729 governors, 36 columns, `Scan!A1:AJ5730`; P2: 5,720 governors, same headers, `Scan!A1:AJ5721`. | Read headers/data rows; check nonempty keyed records and uniqueness, not just worksheet maximum dimension. |
| E02 | Both player files cover 36 kingdoms despite 1198 prefix; matched IDs 5,682, start-only 47, end-only 38. | Governor-ID set comparisons, kingdom coverage and duplicate checks. This is not master-roster eligibility. |
| E03 | 1198: 175 start, 176 end, 175 matched; no start-only, one end-only. | Source-filtered diagnostic. Do not publish identifiable missing-player records in Git. |
| E04 | A1: 4 camp rows and 36 kingdom rows; `Camp Stats!A1:I5`, valid kingdom table `Kingdom Stats!A1:J37`. | Verify actual keyed rows and both tabs; do not count additional unkeyed cells. |
| E05 | A1 contains nine standalone numbers at `Kingdom Stats!E39:E47`, below a blank row. | Inspect source structure and propose explicit reject/warn/table-boundary policy; no silent valid-record ingestion. |
| E06 | Aggregate magnitudes such as `25.3M` and `4.779B` are stored as abbreviated text. | Read underlying value/type. Keep raw precision and do not infer provider rounding method from one example. |
| E07 | Aggregate columns include total `Dead` and combined `T4+T5DEAD`, not separate tier deaths; supplied `DKP` exists. | Header/type inventory. Combined-count limitation no longer blocks DKP because source DKP is authoritative. |
| E08 | Player `Total Kill Points` differs from aggregate `KP (T4+T5)`. | Distinct metric mapping; inspect all actual consumers before choosing substitutions or labels. |
| E09 | Matched 1198 tier kills: T4 51,499,097; T5 213,208,491; 10/20 tier-KP arithmetic 4,779,160,790; total KP delta 4,780,647,527. | Reproduce exact endpoint subtraction and arithmetic. 10/20 is a diagnostic basis, not confirmation of active KVK-16 player-DKP configuration. |
| E10 | Matched 1198 deaths 25,592,768; healed 226,713,307; current Acclaim 74,140,436. | Reproduce counters and column mapping. No player tier-death breakdown is asserted. |
| E11 | 216 comparisons across 36 kingdoms and six metrics were within one last displayed unit of supplied totals. | Reproduce diagnostic method. One displayed unit is not an approved production tolerance, proof of equal periods or proof of complete roster coverage. |
| E12 | Source camp totals do not exactly equal sums of displayed kingdom values. | Precision-aware comparison only; both directly supplied layers stay authoritative. |
| E13 | Current Acclaim and Highest Acclaim are different; legacy healed field names do not have obviously identical semantics. | Inspect actual values and current field mapping, not just header similarities. |
| E14 | Legacy example has `Basic Data`, `Full Data`, `Summary`, `Summary Full`; earlier data-row counts 15,811 / 9,194 / 32 / 32. | Reproduce inventory and trace which sheets current importer uses. Different KVK sample cannot prove numeric parity. |
| E15 | Legacy extrema/first-last/difference fields are not all reproducible from just two new snapshots. | Field-by-field capability assessment and consumer dependency check. |
| E16 | Inspected matched cumulative combat fields had no negative deltas; power/troop-power reductions occurred. | Reproduce and distinguish valid signed metrics from counter regressions. A clean sample does not eliminate regression-handling requirements. |
| E17 | VIP was zero in every new source row; Alliance could be null. | Validate actual values and whether any shared profile reader could misinterpret provider placeholders. Do not overwrite unrelated player/profile data. |

No requirement is made to obtain more precise aggregate exports before proceeding. Precision is a capability constraint to represent and test, not permission to recalculate authoritative totals.

## 5. Historical configuration observations — not current SQL facts

Earlier read-only inspection of the connected **KVK LIST** reported no KVK 16 rows in `KVK_WINDOWS`, `KVK_DKPWeights` and `KVK_CampMap`, while `ProcConfig` and `KVK_Details` contained KVK 16. Older weights were 10/20/40 for KVKs 13–15. The source reference is recorded in the private historical manifest.

The same inspection showed KVK-15 window scan IDs 10/24 and kingdom daily/ProcConfig values 866/888; KVK-16 ProcConfig values 1090/1112 had nearby but non-identical times to the new files. Treat these as **scan-namespace audit leads**, not authorised assignments or current production constants.

Codex must identify current sources and refresh/import behaviour, inspect stored defaults, and separate checked-in schema from data rows and deployed state. Do not silently add missing records or inherit historic weights.

## 6. Open questions and owners

| ID | Item | First resolver | Blocks |
|---|---|---|---|
| Q01 | Current implementation / consumer graph / post-KS4 structure. | Codex: both local repos and safe tests. | Selecting implementation boundaries; not starting Phase 1. |
| Q02 | Designated master-roster workbook and actual eligible population. | Operator supplies B0; Codex validates shape/IDs. | Master-roster acceptance and production player onboarding, not independent code/source audit. |
| Q03 | Aggregate period interpretation for later windows under existing reporting logic. | Codex traces existing windows/config; operator clarifies remaining provider-period semantics only if necessary. | Aggregate window design/sign-off. |
| Q04 | Exact accepted filename grammar, precision, duplicate/conflict policy and shared logical scan mapping. | Codex investigates current parser/registry and proposes a compatible contract. | New importer design. UTC scan start is already settled. |
| Q05 | Active KVK-16 configuration and actual deployed definitions. | Codex via already authorised read-only evidence, otherwise operator-provided evidence. | Configuration/release readiness. Does not authorise mutation. |
| Q06 | Existing versus new persistence and history co-existence, including same-window mixed-source limits. | Codex evidence-backed option comparison; operator approval. | Architecture and implementation. |
| Q07 | Upload channel topology and operator correction/reprocessing journey. | Codex audits existing route; operator selects proposed changes. | New route deployment, not source audit. |

Do not re-ask about the provider's unavailable exact tier-death split, aggregate DKP authority, 36-kingdom scope, later-only player exclusion, extra death-weight columns or timezone/start convention.

## 7. Evidence and update rules

For each claim, append `verified`, `corrected`, `superseded`, `unverified` or `blocked` with method and an exact source reference. Preserve the original claim and correction history. Do not use an unqualified “confirmed” for desired behaviour as though it proved current implementation.

Source-code evidence: repository + commit + relative path + symbol/line range. Workbook evidence: role + SHA-256 + sheet/range + method. Deployed-state evidence: environment, read date and redacted query/result reference. Negative dependency claims require search scope and caveats for dynamic/external readers.

Phase-1 output files do not yet exist. Codex creates them during the task and links them from the programme. No completion, approval, live import or release is asserted by this initial register.

## Phase 1 validation update — 2026-09-09

This additive record supersedes the initial "pending Codex Phase 1" and "outputs do not yet exist"
status. D01–D13 and the historical supersession table remain unchanged. No design gate is approved.

E01–E17: **verified at the stated diagnostic/structural scope**, with methods, original SHA-256
hashes, ranges and limitations in [phase_1_audit.md](phase_1_audit.md), section 3. E04's valid kingdom
table remains A1:J37 while the actual used range extends to J47. E13/E15 verify source distinction
and inability to reconstruct extrema; they do not prove healed semantic interchangeability.
Additional observations: 21 of 32 camp metric sums differ; VIP is all zero; Alliance is null in
65/80 rows and six cells per player workbook are formula-typed. No formulas were evaluated.
The historical numeric CSVs' described counters/deltas were independently compared, not used
as the source of the recalculation. These results do not identify a master-eligible cohort.

| Item | Current status and disposition |
|---|---|
| Q01 | Local import-to-consumer audit delivered; exact code/SQL references in dependency matrix. Dynamic/external deployed readers remain unverified. |
| Q02 | **blocked: B0 not supplied/designated**. P1 remains only the starting sample. |
| Q03 | **open, narrowed**: current logic adds isolated fighting-window deltas; end-scan association does not make fixed-baseline reports individual-window totals. Operator/provider period semantics remain necessary. |
| Q04 | **verified existing conflict / proposed new contract**: whole-KVK route uses message.created_at, not filename parsing; per-KVK ScanID differs from global SCANORDER. New UTC grammar and explicit source mapping await architecture review. |
| Q05 | **unverified deployed state**: local schema inspected; no authorized read-only DB route established. Historical sheet gaps do not prove current SQL absence. |
| Q06 | **recommendation delivered, approval pending**: source-specific raw/staging and versioned publication with shared compatible interfaces. Direct Windowed-table reuse conflicts with keys, nullability, precision and recomputation. |
| Q07 | **pending later design**: existing channel/attachment and admin routes traced; one/two new-channel choice and correction UI not selected. |

[Decisions/next slice](phase_1_decisions_and_next_slice.md) records the remaining operator decisions.
[Validation log](phase_1_validation_log.md) records checks, per-repository documented security skips
and preservation evidence. Stop after audit review; no runtime/SQL implementation or release.

## Follow-up decisions and B0 evidence — 2026-09-09

This is the latest status; earlier B0-absent/period-open/direction-pending text is historical.

| ID | Updated status |
|---|---|
| Q02 | Supplied and designated: `KVK_16_Baseline.xlsx`; 5,806 unique eligible governors, all 36 kingdoms; 5,410 have both P1/P2 observations. Shape/identity validated offline; no live import. |
| Q03 | Resolved policy: separate per-fight reports; live revisions supersede earlier values for that fight, followed by its final report. A distinct final whole-KVK report is authoritative overall. Do not sum revisions or substitute fight sums for overall totals. |
| Q06 | Operator agreed separate new-source direction. Detailed physical architecture and implementation remain unapproved. |
| Q04/Q05/Q07 | Technical source identity/revision/finalization contract, deployed evidence and admission/correction workflow remain next-design or readiness tasks. Do not reopen settled source rules. |

B0 SHA-256: `d28d58b3505eac2cfaffc144130ce8816f270496dee439842c49fc06064fe147`.
Exact source location, checks, coverage and limitations are in the audit's B0 follow-up.
B0 has no timestamp in its supplied filename or columns. That does not block membership;
UTC scan-start evidence is needed only before treating it as a numerical starting observation.
The private bundle's original README/manifest still describe the earlier four-file package and
were not rewritten. B0 remains at the supplied private Downloads path, outside Git.

Remaining operator action is review/authorization of the next contract-only task when desired.
Current deployed SQL/configuration evidence remains a technical readiness gap. No automatic Phase 2.

## Phase 2 preparation — 2026-09-09

The Phase 2 Contract and Architecture task pack and chat starter are prepared under
`docs/task_packs/`. This is preparation only, not execution or approval of G2/G3. Invoking the
starter authorizes a bounded design/documentation pass ending at G2; exact implementation packs
follow only after architecture approval. Latest B0/per-fight/final-overall/separate-source decisions
remain controlling. Optional report revisions, B0 numerical timestamp provenance and deployed
read-only evidence are staged by need in the pack, not blanket blockers to design.

## Pass 4 times, source evidence and SQL access — 2026-09-09

Latest update supersedes earlier missing-timestamp language. Operator confirms B0 UTC scan start
2026-08-26 04:07. Pass 4 player observations: start 2026-09-05 15:26, middle 2026-09-06 13:04,
end 2026-09-07 07:21 UTC. Source names/hashes and checks are in the latest Phase-1 audit section.
Start/end values match prior P1/P2, though byte hashes differ; the middle scan is additional evidence.
5,433 eligible start/middle pairs; 5,410 start/end pairs. Missing middle does not prevent final gain.
These are player scans, not aggregate report revisions. Only Pass 4 has occurred; later-fight and
final-overall examples can remain synthetic until available. No request for unavailable later data.

Q04 timestamp provenance for B0 is supplied. Naming is ours to design, not provider-fixed.
Re-export deduplication needs an explicit content-equivalence policy alongside original hashes.
Q05 now has operator attestation that local SQL/config repo is synced with production, plus an
RDP access offer if needed. Local definitions suffice for design; no live rows/jobs independently
queried and no RDP used. Do not confuse this evidence distinction with a blocker to Phase 2.
The Phase-2 task pack/starter have been updated; task execution and architecture approval remain
separate from preparation. No code, SQL or runtime action authorized by this evidence update.


## Phase 2A design delivery — 2026-09-09; G2 pending

The current user request authorized this documentation pass, superseding earlier preparation-only
status. [Contract A01–A08](phase_2_contract_and_architecture.md) and
[synthetic scenarios T01–T67](phase_2_acceptance_scenarios.md) are delivered as **proposals**, not
operator-approved or verified implemented behavior. [Evidence/checks](phase_2_evidence_and_validation_log.md)
record unchanged local HEADs, 48 source-path comparisons and matching B0/F1S/F1M/F1E byte hashes.

| Item | Latest disposition |
|---|---|
| Q01 | Phase-1 consumer graph remains the source anchor; focused static drift checks pass. Live external readers/jobs remain unverified. |
| Q02 | B0 designation/time/coverage remain settled; A04 proposes frozen attribution, starting power and explicit versioned corrections. |
| Q03 | Settled per-fight superseding live/final reports and separate final overall; no running-total mode, summed revisions or summed-fight overall. |
| Q04 | A02/A03 propose exact namespaces, unchanged-sheet sidecar mapping, UTC metadata confirmation and v1 semantic re-export digest. Await G2. |
| Q05 | Operator-attested SQL/config parity retained separately from unqueried live rows/jobs. No RDP needed; bounded evidence checklist staged before dependent release. |
| Q06 | A01/A05/A06/A08 propose separate facts, immutable finals/publications and compatible shared consumers/caches; detailed design awaits G2. |
| Q07 | A07 proposes one private intake channel and grouped admin status/final/correction journey; no channel, permission or command provisioned. |

B0 time and Pass-4 middle are supplied; no missing-time or later-fight request is reopened.
S1–S6 are a draft sequence, not executable packs. G2 review permits Phase 2B planning only;
G3 separately authorizes implementation. No gate self-approved; stop for architecture review.


## Player EndScanID clarification — 2026-09-09; G2 pending

The operator confirmed StartScanID=10 with successive player scans 11/12 giving interim
11−10 then 12−10; EndScanID=13 gives final 13−10. An authorized later EndScanID=14 change
is itself the explicit correction and produces replacement final 14−10 when available, without
an extra correction command. Old publications remain immutable audit/rollback versions. A pending
new endpoint must not make the old result appear final against the new configuration.
Sequential IDs belong to accepted distinct player observations in the separate source/KVK registry;
re-exports, scan-content corrections and aggregate uploads do not advance that player sequence.
Validated event times and explicit mappings still govern period selection, not numeric MAX alone.
Player endpoint changes do not change aggregate report selection or grant weight/map rewrites.

The contract and synthetic cases T68–T70 now record this confirmed behavior. Earlier generic
final-freeze wording is qualified by this authorized endpoint-change workflow. The operator's
conditional willingness to approve was not recorded as overall G2 approval: documentation needed
this update. Phase 2B remains exact implementation planning only after G2; G3 separately permits
implementation. No code/test/SQL edits, imports, live actions or implementation packs here.


## Phase 2B delivery and G2 approval — 2026-09-09

Chris Watts explicitly approved: **“G2 approved, please proceed”.** G2 is approved, including
the EndScanID clarification and scenarios T68–T70. This supersedes earlier G2-pending/no-pack
statements as current status; their historical evidence remains intact. Phase 2B planning is
delivered in the [implementation plan](phase_2_implementation_plan.md)
and [planning evidence log](phase_2b_evidence_and_validation_log.md).
Ten bounded task packs and matching starters are prepared. **G3 remains pending per slice; S1 is
the recommended first approval.** No implementation, SQL change, live action, PR or deployment
is authorized by this delivery. S6 prepares readiness evidence and stops at separate G4 approval.

### S2B merged closeout and S3A handoff — 2026-09-10

GitHub verified SQL #79 merged at 09:42:44 UTC as
`44afa315dd6cbfe9fec101f2a39a62e534f5b583`; mirror #265 at 09:42:55 UTC as
`a65f01ca4017f5c5e9bd7a87510fa2386c9414b8`; private bot #572 at 09:43:17 UTC as
`8cc62c30bca6e2f79f6066f38a6b8ac169bef2f2`. The operator confirms all reviews passed.
After the operator's local pulls, SQL main is at its merge and bot mirror main is
`5014266267acdff277d501d72fd12a1348ca864c`; the bot tree matches the accepted mirror merge.
Both working trees were clean and local main hashes matched origin/main before this doc update.
These are observed handoff anchors, not instructions to reset future checkouts.

The operator explicitly confirms no changes have been pulled to the bot machine. No production
SQL deployment, runtime rollout/restart or activation is established by these repository merges.
Both disposable evidence databases remain retained. S2B is closed; no predecessor pack rerun.
S2A/S2B task packs and starters are archived as evidence; active architecture, plan, scenario
and local SQL references remain in place. S3A is ready for scope/G3 in a new chat, not already
authorized or implemented. Its future PR must include this documentation closeout and archive
moves, including any still-untracked documents, after inspecting the exact pending manifest.


## S3A merged closeout and S3B handoff — 2026-09-10

GitHub readback confirms mirror #266 merged at 11:28:48 UTC as
`3154997fa2dfc124da75ee35dca79463c3196a43`, and private bot #573 at 11:29:18 UTC as
`140fc89765b1d6ec8418ac6f6d039e575419c29e`. The synchronized local mirror main is
`9d08b3bf9e7cac6c95db1c4a120c8bf0aad7475f`; SQL main is
`44afa315dd6cbfe9fec101f2a39a62e534f5b583`. Both local repos were clean at documentation
entry. Operator confirms local pulls complete, with no bot-machine pull or restart.

Operator smoke on mirror `d5cf27613e54047efb856f4bc3777ee6923fa14e` passed 77 tests in
3.10s, operational logs unchanged, and command registration 36/100 without drift or duplicates.
The prior implementation/regression results (260 tests) and separate completed production/mirror
Changes reviews remain in the archived S3A pack; those are historical runs, not newly rerun here.
S3A runtime/test contents matched the production candidate. Repository merge is not deployment.

S3A pack and starter are archived with repaired links. All predecessor evidence is retained.
Start S3B in a new chat using its refreshed pack/starter only with explicit S3B G3 approval and
an explicitly named disposable SQL integration target. Existing S2A/S2B evidence databases are
retained and not authorized for reuse/rebuild by this handoff. The bot machine need not be updated
for S3B local development. No SQL connection, service start, production action or successor
implementation occurred in this documentation closeout.

These documentation edits, including untracked archive destinations, remain pending for the
separately authorized S3B PR. Its pack contains the full carried-forward manifest and requires
both sides of renames, repaired links and preservation checks. No commit/push/PR is performed
by this closeout. Security routing: exact Markdown-only skip (status, evidence, links and archive
moves; no runtime/config/permission/data-access effect), plus separate SQL no-change skip.

## S3B merged closeout and S4A handoff — 2026-09-10

**S3B is complete, operator smoke accepted and merged.** Mirror
[PR #267](https://github.com/cwatts6/K98-bot-mirror/pull/267) merged at 13:59:47 UTC as
`e915f9727f9492fe4ecc02b5c0d9f3c6e443be13`; private bot
[PR #574](https://github.com/cwatts6/k98-bot/pull/574) merged at 14:01:14 UTC as
`a8ad9f1d81cfb7884a9cdcc0b067c4346a204488` on 2026-09-10.
Operator post-merge smoke on mirror main `e915f972`: import smoke passed, registration
36/100 without drift or duplicates, **36 tests passed in 9.11s** (4 publication + 32 SQL).
Current synchronized local mirror main is `02385a0edc0ec83f77241e02648eabb3b7640ea6`;
local production/main is `a8ad9f1d81cfb7884a9cdcc0b067c4346a204488`; SQL main remains
`44afa315dd6cbfe9fec101f2a39a62e534f5b583`. Both repos were clean at closeout entry.
S3B pack/starter are archived. **Next: S4A Shared Reports and Cards in a new chat, with
separate S4A G3 approval.** Preserve pending S3B closeout docs and both archive moves
for the eventual separately authorized S4A PR; its pack contains the complete manifest.
S3B's latest full-suite rerun stalled around 19% and remains incomplete; the accepted smoke
does not replace it. The earlier 3,764-pass full result is pre-review-fix evidence.

The operator confirms local pulls completed and no changes were pulled to the bot machine.
No bot-machine restart, production SQL deployment or source activation is evidenced or performed.
S4A local development does not require a bot-machine deployment. New routing remains disabled.

The accepted S3B boundary includes immutable acceptance, atomic publication and four review fixes:
rollback delivery reconciliation with increasing fences; aggregate rejection for equal-endpoint
no-fight windows; complete immutable action replay scope; accepted revision period-scope checks.
All five inline threads were replied to and resolved before merge. The two separate final
five-file Changes reviews, Deep off, completed with zero findings/deferred/open questions:
mirror `308e7130-8e09-45fc-9765-c4c9673fc21f`, private
`97196427-2c4a-40e5-acbd-3f3c3f71c6e9`. Earlier implementation/security evidence is retained.

Preserve the operator-approved endpoint amendment: either StartScanID or EndScanID may change;
a supplied end must be >= start. Distinct imported scans advance both ScanID and UTC scan start,
oldest first; semantic re-exports allocate no new scan. Blank/future end uses the latest eligible
interim; an available end pins the final, and an authorized endpoint update permits replacement
without a separate correction command. Equal endpoints produce zero supported fight scores for
every frozen B0-eligible member, including absent scan members, with aggregates not applicable.
Ordinary missing-data states remain explicit. Aggregate reports and daily SCANORDER stay separate.

The authorized S3B test target was `9SX2VF4\K98DEV` /
`K98_S3B_Disposable_20260910`, including prerequisite schema and synthetic two-connection tests.
Retain this database and the separate S2A/S2B evidence databases; no reuse/rebuild for S4A is
implicitly authorized. S4A uses mocks by default; any SQL integration must first have an explicitly
authorized disposable target and operations. No connection or setup was performed in this closeout.

The supplied transcript shows 36 passed in 9.11s on merged mirror main `e915f972`, import smoke
success and registration 36/100 without drift/duplicates. Its raw attachment stays outside Git.
The current synchronized main contains identical KVK source and these test files to private merge
`a8ad9f1d`. Historical 257 affected regressions passed with logs unchanged. The operator smoke
did not run the log-noise wrapper, so it is not new log-hygiene or full-suite evidence.
The interrupted post-review full suite remains an explicit S4A validation follow-up; investigate
its cause and run the required full suite/log-noise gate without silently expanding runtime scope.

S3B pack and historical starter are archived, with links repaired and delivery history retained.
The S4A pack/starter require all pending closeout documentation, including untracked archive
destinations and both source deletions, in the eventual separately authorized S4A PR.
These edits stay uncommitted for that handoff. No new chat or S4A implementation is started here.
Documentation-only security skip: exact closeout/status/links/archive manifest, no runtime,
configuration, permission, data-access or deployment effect. SQL repository: separate no-change skip.
Runtime pytest/smoke/registration reruns are skipped for this Markdown-only closeout.
