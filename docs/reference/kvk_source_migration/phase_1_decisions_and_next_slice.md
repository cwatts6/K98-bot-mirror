# Phase 1 — decisions and recommended next slice

Date: 2026-09-09. Recommendation only. No architecture, implementation or release approved.

## Settled requirements

D01–D13 remain intact: preserve legacy and compatible workflow; all 36 kingdoms for this KVK; designated B0 whitelist independent of window endpoints; no gain without a valid starting observation; player total-deaths DKP with one WeightDeadsZ; supplied kingdom and camp metrics/DKP authoritative; no player/camp rollup replacement; no detail-summary DKP equality test; UTC filename scan start; unchanged Windows/Camp Map sheet structures unless an evidenced exception is approved. A source filename prefix is never a population filter. The unavailable provider death split/formula is not a decision or blocker.

The audit disproves several compatibility assumptions: current intake uses upload time and Full Data, current baseline grows, missing endpoints fall back, aggregate DKP is recalculated, and several readers add windows. See C01–C34 in the dependency matrix and the audit's source ledger.

## Storage options grounded in current contracts

| Option | Actual benefits | Actual constraints | Recommendation |
|---|---|---|---|
| Extend/reuse existing Raw, Baseline and Windowed tables | Existing DAL/export paths and keys; bigint counters already present | Windowed PKs omit source/revision; metrics NOT NULL; DKP FLOAT; no combined tier-death or precision field; legacy recompute deletes all rows for KVK and derives both aggregates; readers recalculate DKP; baseline writer expands roster | Reject direct reuse for source facts. Adding columns alone does not fix writers/readers or preserve history. |
| Separate source raw/staging, with shared reporting interfaces over explicit versioned publication | Keeps legacy data and code readable; reuses reporting blocks/rendering/export plumbing; source semantics enforced before publication | Requires source/period/availability/version metadata in serving contract and coordinated DAL/consumer changes. “Shared” cannot mean writing into current unversioned tables without redesign | **Preferred.** Source-specific immutable facts and publication generation; adapt shared interfaces only where semantics match. |
| Fully isolated new-generation storage, processing, commands, rendering and exports | Strong source isolation and straightforward retention | Duplicates command/permission/formatting machinery and lifecycle; makes every fix cross-generation; mixed stats-card dependency still needs an explicit boundary | Keep isolated storage/publication aspects, avoid wholesale duplicate UI implementation. Use if approved compatibility requirements cannot be met through adapters. |

No current Windowed DKP computed column prevents direct assignment; the incompatibility is procedural and reader-side recomputation, FLOAT precision and missing identity/availability. Adjacent `STATS_FOR_UPLOAD`/`EXCEL_FOR_KVK_n` contain many independent target/profile/history fields and completion proof. They are not an alternative table into which the 36-kingdom source can safely be copied.

## Proposed contract for architecture review

1. A designated B0 version fixes eligible Governor IDs per KVK, with original hash and provenance. Store eligibility independently from per-window observations. A player needs membership and both usable endpoints for each metric. P1 is not a default B0. Preserve rejection/coverage counts privately and publish honest aggregate availability, not identifiable excluded-player lists.
2. Preserve each imported file's content hash, source kind, scan start UTC and timestamp precision, upload/import time and diagnostic outcome independently. New player observation IDs, aggregate report IDs and revisions are not KVK scan IDs. Do not infer mapping from sequential arrival or clock proximity.
3. Keep existing Windows and Camp Map sheet columns. Introduce an approved sidecar mapping from `(KVK, logical scan/window endpoint, source kind)` to the exact observation/report revision. Validate whole-KVK `ScanID` against its own namespace. A new logical registry must not collide with `KVK_Scan` or use daily `SCANORDER`; exact ownership and migration of any existing window assignments require G2 approval. Do not manufacture a player observation merely to allocate an aggregate scan.
4. Validate both A1 tabs as one aggregate batch: keyed table boundary, all 36 configured kingdoms, unique records, four uniquely resolved camps, required parseable metrics and original precision. Recommend an explicit warning for A1's nine unkeyed tail cells with an auditable ignored-range count, rejecting malformed records inside the table. This policy is proposed, not implemented. Reject unknown or ambiguous camp names; normalize case/whitespace only.
5. Preserve abbreviated numeric text, expanded Decimal value and last displayed unit. Choose decimal SQL capacity from field ranges during G2; do not infer exact provider rounding or hidden digits. Sort by supplied values and use deterministic identity tie-breaks while showing limited precision; do not claim sub-unit ordering accuracy. Aggregate DKP is selected directly, independent of weights. Keep total and combined tier deaths separately; aggregate total-KP is unavailable where only tier-KP exists.
6. Build a candidate publication only after required player/aggregate inputs and configuration versions satisfy the approved period contract. Atomically select a publication revision, then refresh dependent readers/caches/exports. Readers must consume one selected generation, not independently choose latest from each stream. Missing an optional report should produce explicit unavailable state if that partial-publication policy is approved; it must not silently reuse a stale report as simultaneous evidence.
7. Completed windows select exact frozen endpoints/reports; corrections create a new revision and explicit reselection. Open windows may choose the latest complete, valid mapped observation with its actual time displayed. Do not retain current future-end capping for closed windows. Equal-start/end/no-fight windows must not receive unrelated cumulative aggregates; proposed aggregate state is not applicable/unavailable until the period policy approves otherwise.
8. Freeze or record weight/map/roster versions used for player calculation. Re-running a file should not rewrite completed history because configuration changed. A same-hash retry should return the existing import outcome; changed bytes for the same observation should enter a correction workflow. Same content under a renamed file must not allocate a fresh logical endpoint automatically.

## History, coexistence and rollback

Preserve old KVK facts with their original source and metric basis. Two-snapshot data cannot reconstruct legacy intervening minima/maxima, per-player first/last update history, or absent endpoints. Aggregate precision cannot be recovered by copying rounded text into an integer; exact tier deaths remain unavailable. Do not backfill zeros to pass an old non-null schema.

Cross-KVK history can display both generations only with explicit basis and availability. Comparisons/ranks need compatible metrics and periods; unrelated old/new samples are not a parity gate. Same-window legacy/new endpoint splicing is prohibited by the proposed contract unless a separately approved, same-counter calibration proves it valid. Choosing one source for players and the provider source for kingdom/camp is intentional and required; equality of their DKP is not expected.

Legacy fallback can select the last valid legacy publication **if legacy observations for that period exist**. It cannot synthesize a current legacy report from the new files, recover unavailable precision, restore unobserved players or retract already sent Discord messages/downloaded sheets. Keep original new observations and version history even when selecting an older publication. A bot rollback alone may leave changed SQL selection, caches and external exports behind; release rollback must coordinate all of them. No legacy deletion is proposed.

## Recommended next task — Phase 2 contract/design only

After operator review, prepare a focused contract and architecture pack resolving Q03, exact logical-scan mapping, B0 onboarding, unavailable-field presentation and source publication. Include synthetic examples for a later fighting window, fixed-baseline aggregate, missing start/end, no-fight window and one corrected import. This is documentation/design work, not migration scripts or an operational importer.

Proposed next-task authoring manifest (not created in Phase 1):

- Bot: `docs/reference/kvk_source_migration/phase_2_contract_and_architecture.md` (new), programme/register and relevant indexes (updates).
- SQL: no writes for that contract-only task; validate candidate objects against `sql_schema/KVK.KVK_Scan.Table.sql`, `KVK.KVK_Windows.Table.sql`, `KVK.KVK_CampMap.Table.sql`, `KVK.KVK_DKPWeights.Table.sql`, the three Windowed tables and ingest/recompute/export definitions.

After G2/G3, the first plausible **implementation** PR-sized slice is offline player/aggregate parsing and immutable validation models with no SQL, route registration or publication. Proposed exact bot paths: new `kvk/schemas/new_source_schema.py`, `kvk/models/new_source_observation.py`, `kvk/services/new_source_parser.py`, `tests/test_new_source_parser.py`. Reuse safe integer/UTC/text conventions after semantic review, not the Full Data expected-header contract. No runtime import of `kvk_all_importer` is necessary for this offline slice. Synthetic fixtures only. This slice itself still requires approval and a fresh Changes security-routing decision.

Subsequent slices, individually approved:

| Slice | Candidate file/object boundary | Key gate |
|---|---|---|
| Source persistence, publication disabled | SQL new reviewed migration (date/sequence allocated at approval), companion snapshots provisionally `KVK.KVK_SourceObservation.Table.sql`, `KVK.KVK_SourcePlayerSnapshot.Table.sql`, `KVK.KVK_SourceAggregate.Table.sql`, `KVK.KVK_MasterRoster.Table.sql`, `KVK.KVK_SourceScanMap.Table.sql`; bot new `kvk/dal/new_source_import_dal.py` | Proposed names only; approve keys/types/retention and isolated transaction/retry/correction tests before DDL. Never deploy snapshots as migrations. |
| Publication and source selection | Proposed SQL `KVK.KVK_SourcePublication.Table.sql` and generation-bound facts; new `kvk/services/new_source_publication_service.py`, `kvk/dal/new_source_reporting_dal.py` | Exact frozen endpoints/report period; no zero baseline; atomic selection and restart recovery. Final physical fact-table names deferred to G2. |
| Separate upload admission | `DL_bot.py`, new `upload_routes/kvk_source_route.py`, `bot_config.py`, `constants.py`, new source import service/audit tests, `docs/reference/ENV_REFERENCE.md` | Channel topology chosen; no accidental legacy/fallback dual route; disabled-by-default activation. |
| Shared reports and cards | `kvk/dal/kvk_reporting_dal.py`, `kvk/services/kvk_reporting_service.py`, `stats_alerts/embeds/kvk.py`, `kvk/dal/kvk_stats_card_dal.py`, `kvk/services/kvk_stats_card_service.py`, related renderers/tests | Authoritative aggregate DKP, clear KP/period labels, source-matched context, absent-value behavior and existing payload limits. |
| Exports/operations | `kvk/services/kvk_export_service.py`, `gsheet_module.py`, `kvk/dal/kvk_admin_dal.py`, `kvk/services/kvk_admin_service.py`, `commands/stats_cmds.py`, `tests/test_kvk_export_service.py`, `tests/test_kvk_admin_service.py` | Cumulative report selection replaces inappropriate sums; versioned diagnostics; compare sheets distinguish unavailable from zero. |

Do not bundle target/history/daily-profile migration into those slices without a separately approved scope. Their current data sources are independent, even though services share names and metadata. Future exact manifests must be rechecked for source drift and approved before writing code.

## Validation and release outline

Phase 1 actual results are in the validation log; proposed tests below have **not** been run against an implementation.

| Test family | Required cases and relevant existing coverage |
|---|---|
| Parser/source | Exact headers, duplicate/invalid IDs, all kingdoms, null/formula-typed text, unknown camp, stray tail, incomplete aggregate tab, integer range, abbreviated Decimal precision, malformed suffix, UTC minute/seconds grammar; current `test_kvk_all_schema.py`, `test_kvk_all_importer.py`, `test_kvk_all_import_service.py` protect legacy only. |
| Roster/windows | Missing B0 blocks roster acceptance; later-only ignored; eligible missing start/end unavailable; genuine zero valid; equal endpoints; incomplete intermediate scan; signed power versus combat regression; exact closed and bounded live selection. `test_kvk_all_recompute_sql_contract.py` currently asserts legacy fallback; it is not new-source acceptance. |
| SQL/retry/correction | Transaction rollback at every stage, same-hash rename/retry, conflicting correction, concurrent allocation, source namespace collision, persisted publication after restart, no partial two-tab publication. Use disposable SQL test data only. |
| Reporting | Supplied aggregate DKP survives all readers; camps not summed; total/tier KP distinct; no cumulative reports added as later windows; precision ties; B0 rank denominator; mixed card context; unavailable versus zero. Existing reporting, stats-card DAL/payload, rankings and export tests provide consumer anchors. |
| Regression/permissions | Legacy import and historic exports; KS4 stats/targets/history unaffected; configured-channel/role checks and owner-bound views; multiple attachments; diagnostic and export side effects run once. |
| Cache/release | Generation key invalidation, atomic selection, stale/final policy, old-cache protection, no reset of daily send claims, partial export failure, coordinated fallback with no source splicing. |

Later release order: verified read-only deployed inventory/config → reviewed additive SQL migration with new source disabled → parser/DAL/admission code disabled → isolated imports and shadow publications → private consumer/export validation → separately approved activation → operator observation. Split bot/SQL Changes reviews at exact revisions with Deep off. Test and document rollback before activation. Phase 1 has **no deployment steps to execute**.

## Refactor findings and deferred scope

Within proposed migration: extract new source selection/parsing into services/DAL; replace aggregate recomputation and implicit summing where source semantics require it; make missing/period/precision metadata explicit; avoid extending root importer/export monoliths with a second domain implementation. No Phase-1 runtime fix.

Existing Stats/KVK History/offload and ProcConfig reliability debt is already tracked in the active deferred register/WS1 programme; do not duplicate or implement it here. Legacy `_aggregate_windowed_dfs` generic numeric summation also sums starting power and groups by display name; capture separately for a future legacy export review. No vulnerability discovery or risk acceptance is implied.

## Remaining operator decisions and stop point

1. **Source-period decision:** do later kingdom/camp exports isolate each requested fighting window, or remain cumulative from a fixed baseline? If cumulative, approve the proposed cumulative-period labels and unavailable individual-window aggregates. Selecting an end scan alone cannot resolve this.
2. **Missing evidence:** supply/designate B0 when available, and provide current bounded deployed SQL/configuration evidence (or an already-authorized safe read-only route). These block their dependent acceptance/release checks, not the completed local audit. Do not backfill later-only players.
3. **Design approval:** review the recommended source-specific storage/shared-interface direction and authorize the contract-only next task if desired. Channel topology and detailed correction UI can be settled there, before deployment; no channel action is requested now.

**Stop here for operator review. No automatic Phase 2, architecture approval, implementation, PR creation, import or deployment.**

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
