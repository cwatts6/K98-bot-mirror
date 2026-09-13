# KVK Source Migration — Phase 2A contract and architecture

## Current status — S7/S8A complete and merged; S8B next, 2026-09-13

S7's approved contract/manifests and S8A's SQL foundation are complete and merged.
The operator confirms successful smoke acceptance and local pulls; **no changes have
been pulled to the bot machine**. Retained S8A evidence includes six successful disposable
scripts; the later runner input fix has offline validation only. No fresh post-merge
SQL run, production runtime deployment or activation is claimed.

**Next: start S8B Bot Source and Matched Update Services in a new chat, review/scope first.**
Use the [S8B pack](../../task_packs/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S8B%20Bot%20Source%20and%20Matched%20Update%20Services.md) and [starter](../../task_packs/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S8B%20Bot%20Source%20and%20Matched%20Update%20Services.md).
Read the [canonical closeout, merge evidence and exact S8B carry-forward manifest](s8a_closeout_and_s8b_handoff.md).
Do not reopen settled S7 decisions or repeat S8A implementation. Further SQL execution
requires exact target/backup/row-preview/operation approval; S8B implementation needs its
own approval after scope review. Public routing remains S9 work; SourceRouting.Enabled
alone does not implement it. S6-OPS01/PERF01/CAP01, both uncertain publications and all
retained databases/files remain preserved. Earlier dated sections are historical evidence.

## Historical delivery — 2026-09-12 post-S6 closeout

**S6 evidence/rehearsal delivered, accepted and merged; feature activation remains blocked.**
Mirror [#272](https://github.com/cwatts6/K98-bot-mirror/pull/272) merged at
19:20:50 UTC as `016df1e61c8017556a7e8ba8374d31375aebfb74`; production-repository
[#579](https://github.com/cwatts6/k98-bot/pull/579) merged at 19:21:34 UTC as
`a8c9c515066ca6ef079120b76dd160e3389badab` (reviewed/final head
`b9c84751d3cc1deaba0a5772ab45d89263fcb398`). Mirror review fix `fa1f4733` records
the missing public routing consumer. Bot local main/origin main is
`a2f148fa9bd4fb367fd46d0500a768c14fee915b`; SQL main/origin main remains
`44afa315dd6cbfe9fec101f2a39a62e534f5b583`. Both were clean at this update's entry.

Operator reports merged and deployed locally, with nothing pushed to production.
GitHub confirms the production-repository merge above; **no production runtime or
bot-machine deployment, source activation, or fresh post-merge smoke is claimed**.
Local deployment is operator-attested; exact running process/config was not checked.

All preceding slices remain accepted. S6-OPS01/PERF01/CAP01 retain their open
operational components; accepted measured evidence is not pending reapproval.
The newly agreed requirements are fixed source per KVK for all affected outputs,
matched-pair public publication, confirmed reuse of an unchanged correction
counterpart, import-triggered serialized/latest-pending exports, export-only
recovery, retained input/publication history and safe output reuse after each KVK.
These are requirements, not claims of implemented behavior.

**S7/S8A are complete and merged; S8B is next.**
Follow the current status above; do not rerun predecessors or start later implementation packs.
Carry every path in the post-S6 handoff manifest into the next separately authorized
slice PR, including both S6 archive move sides. No Git publication, SQL/provider
execution, restart, production promotion or activation is authorized by this update.
Earlier dated blocks below are historical and do not select the next task.

[Settled requirements](post_s6_integration_requirements.md); [handoff and exact manifest](post_s6_handoff_log.md); [S7 pack](../../task_packs/archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S7%20Integration%20Contract%20and%20Implementation%20Planning.md).

2026-09-09. **Proposed architecture for G2 review. Not approved or implemented.**
The operator authorized this bounded documentation pass only. G2 permits Phase 2B planning;
G3 separately permits an implementation slice. Historical pack instructions do not extend that authority.

Read with [acceptance scenarios](phase_2_acceptance_scenarios.md),
[evidence and validation](phase_2_evidence_and_validation_log.md), and the
[decision register](decision_and_evidence_register.md). C01–C65 refer to the unchanged
[Phase 1 dependency matrix](phase_1_dependency_matrix.csv).

## 1. Scope and recommended decisions

Use source-specific immutable observations and aggregate reports, a frozen B0 roster, and
versioned publications behind shared reporting services. Preserve the entire legacy route.
Do not insert new facts into legacy Raw/Baseline/Windowed tables: their keys omit source and
revision, required metrics cannot express absence, DKP uses FLOAT, and recompute deletes/rebuilds
the KVK partition. Merely adding columns cannot repair those semantics (C08–C24).

| Design ID | Recommendation and consequence |
|---|---|
| A01 | Separate source storage under KVK; reuse services/rendering through a version-2 report envelope. Legacy SQL objects keep their meaning. |
| A02 | Sequential accepted player-scan IDs in a separate source/KVK registry, explicitly bound to observations and unchanged Windows rows. Event metadata and window configuration determine endpoints; daily SCANORDER remains separate. |
| A03 | Byte hash plus versioned semantic digest; equivalent re-exports add evidence aliases, not observations/revisions/publications. Changed values require reviewed correction. |
| A04 | B0 fixes eligibility and player kingdom attribution; snapshot CampMap and one approved weight set per KVK. Exact start/end per metric; no zero or alternate-period fallback. |
| A05 | Live fight reports supersede selection. Retain immutable final versions; an authorized player EndScanID change is itself an explicit endpoint correction, with no separate correction command. Aggregate-final corrections remain explicit and separate. Overall aggregates come only from their separate final report. |
| A06 | Atomic publication pins both streams and configuration, permitting truthful partial availability while live. Stream finality is separate from complete-period finality. |
| A07 | One private new-source intake channel, authorized operators, explicit metadata confirmation and admin-only final/correction actions. No channel provisioning now. |
| A08 | Versioned reads/caches/exports; latest selected fight is normal fighting display, overall is explicitly selected and unavailable until supplied. Daily claims remain unchanged. |

Settled requirements remain controlling: all 36 kingdoms for KVK 16; later-only players excluded;
player DKP uses total deaths and WeightDeadsZ; kingdom/camp values and DKP are supplied authority;
no provider formula/split request, no player rollup or kingdom-sum replacement; UTC scan start;
Windows and Camp Map sheet columns unchanged. Running-total mode is outside this design.

## 2. Identity and namespace contract

All identities below are proposed. IDs are stable database-owned values, never filenames.
SourceKey is the case-sensitive allowlisted value `snapshot_report_v1`; `legacy_full_data` is separate.
KVK_NO is a positive SQL int, not inferred from dates. Reject ambiguous season assignment.

| Identity | Unique key / owner | Meaning |
|---|---|---|
| Artifact | SHA-256 of original bytes / evidence store | Immutable private original; names and attachment IDs are aliases, not identity. |
| Import attempt | UUID / admission service | One request plus actor, guild, channel, attachment, received UTC, outcome and artifact reference. Retry key is guild/message/attachment/action. |
| Player observation | `(SourceKey, KVK_NO, ScanStartUTC, TimePrecision, EventDiscriminator)` / ingestion service | One whole player scan event, not one player or fight. Distinct simultaneous genuine events require explicit operator event discriminator; default discriminator is `main`. No inferred collisions. |
| Observation revision | `(ObservationID, RevisionNo)` / DAL | Immutable typed cells and source digest. One selected revision, previous revisions retained. Timestamp/season corrections create a replacement observation identity with a supersedes link. |
| Player fact | `(ObservationRevisionID, GovernorID)` | Observed values; identity is positive bigint GovernorID. Names never join keys. |
| Period | `(SourceKey, KVK_NO, PeriodKey)` / configuration service | `fight:pass4`, later configured fight keys, `overall`, or `no_fight:<key>`. Stable key survives a display-name change. |
| Aggregate report | `(SourceKey, KVK_NO, PeriodID)` | One logical report family with successive revisions. Fight and overall are different report families. |
| Aggregate revision | `(ReportID, RevisionNo)` / DAL | Both tabs, declared coverage start/end UTC, as-of UTC, live/final designation and revision provenance. Revision number orders acceptance history, not event time. |
| Logical scan | `(SourceKey, KVK_NO, LogicalScanID)` / source registry DAL | Positive int allocated sequentially under a transaction lock for each newly accepted distinct player observation, after source/KVK/time validation; binding created atomically. Re-exports, corrections and aggregate uploads do not allocate another player scan. |
| Logical binding | `(MappingVersionID, LogicalScanID)` | Exact observation identity; publication pins its revision. Aggregate report association is to PeriodID, never obtained by inventing a player scan. |
| Roster | `(KVK_NO, RosterVersion)` | Frozen B0 members plus B0 observation/revision and attested time provenance. |
| Publication | UUID plus `(SourceKey, KVK_NO, PeriodID, Generation)` | Immutable selected inputs, facts, metric states, configuration and calculation-version identity. |
| Active selection | `(KVK_NO, PeriodID)` plus monotonic SelectionVersion | Explicit source and publication pointer; compare-and-swap prevents lost updates. Rollback advances selection version even when selecting an older generation. |

Use UUID foreign keys between new entities and composite season/source validation to prevent
cross-KVK links. Publication is the reproducibility unit; current pointers alone are not history.
Source activation is an explicit per-KVK routing record, disabled by default; absent historical
routing retains legacy behavior. An activated new source that has no data returns unavailable,
never silently falls back to legacy.

### Unchanged Windows/Map structure and explicit mapping

Keep `KVK_Windows!A1:F`, `KVK_CampMap!A1:D` and `KVK_DKPWeights!A1:D` unchanged.
Existing SQL Windows has int StartScanID/EndScanID, a start >=1 check and end >= start check,
but no foreign key proving those scans exist. Do not reinterpret historical legacy rows globally.
Capture a versioned copy of the relevant Windows rows with SourceKey and mappings in the sidecar.
For new-source KVKs those integers address the new logical registry only through the source-aware
resolver. Legacy readers continue resolving KVK.KVK_Scan. Equal integers in different namespaces
do not identify equal observations. No writes to KVK_Scan to make the mapping look compatible.

Operator example: Pass 4 StartScanID=10; newly accepted distinct player observations receive
11, 12, 13, then 14. These are **illustrative IDs, not actual configured KVK-16 IDs**. Retain
the explicit observation/time binding for each ID. A delayed older event can receive a larger
ID but does not become the live endpoint merely because of its number or arrival order.
Select live progress by validated event UTC within the period; exact configured final endpoints
also require valid temporal ordering. Reject int exhaustion; never renumber published identities.
Existing KVK-16 IDs/mappings require validation before activation. Daily SCANORDER,
PRE_PASS_4_SCAN and KVK_END_SCAN remain separate; aggregate uploads do not advance player ScanID.

Live windows require an exact configured start. Null or not-yet-available end allows live selection only
from accepted observations explicitly associated with that period and later than its start,
bounded by a configured close time when known. Greatest scan-start time wins; ties/conflicting
revisions need explicit selection. A non-null end is an exact slot: if it is absent, final output
is unavailable; no future-end cap or nearest scan. Live previews may still use a separately
labelled intermediate endpoint without pretending to have satisfied that final slot. These are
normal interim player results, not restricted to an admin preview.

### Operator-confirmed EndScanID workflow

| Available observation / window setting | Selected player calculation |
|---|---|
| StartScanID=10; scan 11 available; end blank or not reached | 11 minus 10, interim |
| Scan 12 available; end blank or not reached | 12 minus 10, replacing the prior interim result |
| EndScanID=13 and scan 13 available | 13 minus 10, final for that configured player window |
| Authorized EndScanID change to 14; scan 14 available | 14 minus 10, replacement final; previous version retained |

The authorized, validated Windows configuration update **is the explicit endpoint correction**.
After its normal import/processing, the service snapshots the changed endpoint and publishes a new
generation; it does not require a separate finalize/correct command for this player-window action.
Record the authorized configuration change provenance, old/new EndScanID and affected publication.
Unrelated weight/map changes in the same import do not gain automatic historical-rewrite authority.
This rule changes the selected endpoint, not the contents of an already accepted observation.

If 14 is pending, show the current configured endpoint as pending and the selected usable interim
endpoint explicitly. The retained scan-13 result remains final only for its previous configuration;
it cannot be labelled final against EndScanID=14. Requests must compare desired configuration
version with publication configuration so a failed rebuild cannot appear current/final. When 14
arrives and validates, resume publication without a second correction confirmation. Retries are
idempotent by configuration version/period/input revisions and remain CAS guarded.
Each player needs scan 10 and the selected endpoint; no intermediate-scan requirement or fallback.
Changing the player endpoint does not select, revise or relabel an aggregate report. If coverage
differs, preserve explicit stream timestamps/coverage and finality rather than invent agreement.

## 3. Practical metadata and deduplication

Recommend filenames `kvk16_players_20260905T1526Z.xlsx` and
`kvk16_pass4_totals_live_20260906T1304Z.xlsx`. Seconds variant is `YYYYMMDDTHHMMSSZ`;
minute timestamps persist with seconds 00 plus precision `minute`, which is not claimed seconds
accuracy. Filename time always means scan start. Aggregate period start/end and final status
require separate explicit metadata; filename scan time alone cannot prove its coverage.

At upload, show one metadata confirmation: source kind, KVK, fight/overall, scan-start UTC,
coverage start/end for aggregates, as-of UTC, live/final, and optional correction target/reason.
Defaults may come from the strict filename or the already selected period, but conflicting
metadata blocks acceptance. Store confirmed metadata in SQL as the sidecar; no extra workbook
sheet or operator-authored JSON is required. Record who confirmed each override and when.
Existing names and terminal download suffixes such as ` (1)` are accepted as original names;
strip only that suffix before attempting the known timestamp grammar. Unknown or ambiguous
names use explicit metadata confirmation, never upload/file time. Preserve the original name.

B0 remains `KVK_16_Baseline.xlsx` with its original hash. Its scan start is explicitly attested
as 2026-08-26 04:07 UTC. F1S/F1M/F1E are 2026-09-05 15:26, 2026-09-06 13:04 and
2026-09-07 07:21 UTC. They are three player observations; none is an aggregate revision.
A1 is a format example whose individual-fight assignment is unverified; quarantine it from
production period selection unless independently designated. No final overall or later fight is awaited.

### Semantic digest v1

Keep original SHA-256 regardless of equivalence. After structural validation, hash a canonical
UTF-8, length-delimited serialization including parser-schema version, sheet identities, canonical
headers, cell type tags and all recognized keyed cells sorted by numeric GovernorID/Kingdom/CampID.
Include optional/profile cells even if not published; a changed name or Alliance is not silently
discarded. Numbers normalize through Decimal (integral 1 and 1.0 equal); empty cells normalize
to null, distinct from zero. Text preserves case and Unicode codepoints with normalized CRLF to LF;
do not case-fold names. Camp resolution uses a separate trimmed, whitespace-collapsed casefold key.
Formula-tagged content remains distinct from literal text; never compare only cached results.
For aggregate numbers include value, raw display token and displayed unit: `1.0M` and `1.00M`
have different precision and therefore different digests. Preserve original text outside the digest too.

Ignore ZIP metadata, styles, row order, sheet order, trailing empty rows and approved unkeyed tail
annotations in this digest, while retaining their raw artifact and diagnostic counts. Unknown
columns/tabs or novel populated tail content need schema review and cannot be deduplicated away.
Digest equality is meaningful only for the same schema version and compatible confirmed identity
metadata. Same artifact reused at a different claimed time/period is an identity conflict pending
explicit review, not automatically a new observation. A different true event may have unchanged
counters; acceptance requires its independently confirmed event metadata, retaining that decision.

Same identity + same semantic digest = attach evidence alias, return existing accepted outcome,
no new revision/publication/export. Same identity + changed digest = pending correction, show
private changed-field counts, require target revision and reason. Same hash/digest with live→final
designation is an explicit finalization state event, not a duplicate preventing finalization.
F1S/P1 and F1E/P2 are expected re-export-equivalent under v1; Phase 1 proved cell-value equality,
not execution of this as-yet-unwritten canonicalizer. A canonicalizer upgrade never retroactively
merges identities or reselects history; compare under the original version or reviewed migration.

## 4. Roster, players and calculations

Freeze B0's 5,806 eligible governors and all 36 kingdoms. These are KVK-16 evidence counts,
not global importer constants. Retain later-only raw observations privately for audit, but exclude
them from published player facts/ranks. Publish only exclusion/coverage counts in diagnostics.
Membership is independent of numerical baseline usability. A reviewed roster correction creates
another roster version with a diff/reason and explicit affected-publication plan; never auto-grow
or delete members because a later scan omitted them. Historical selections remain reproducible.

Attribute each eligible player to B0 kingdom throughout the KVK, with camp from the publication's
frozen CampMap. Retain observed kingdom changes as diagnostics rather than moving contributions.
Name comes from selected end observation, then start, then B0, clearly display-only. No profile
writes to daily systems. Aggregate kingdom/camp attribution remains that report's validated mapping.

For each metric require valid exact start and end observations of the same source/schema basis.
Delta = end minus start. A missing start is not replaced by B0 or the middle; missing end is not zero.
The middle is usable for start→middle live progress, never required for start→end. The verified
5,433 live pairs and 5,410 final pairs may differ; do not add subinterval cohorts. 396 eligible
members without both final endpoints remain eligible but unavailable, not zero-activity players.

Power and Troops Power deltas may be negative. Negative cumulative combat/heal/Acclaim deltas
are `counter_regression` with both values retained privately; the affected metric and dependent
derived metrics are unavailable until corrected. Other valid metrics remain usable. Zero is valid
only after two valid observations produce zero. Do not clamp, absolute-value, or infer resets.

Player DKP = X × delta(T4 Kills) + Y × delta(T5 Kills) + Z × delta(Dead total).
Use the existing three coefficient meanings, including only one WeightDeadsZ. Snapshot one
operator-confirmed current-KVK row for the season; record source EffectiveFromUTC and exact
coefficient representation. Because import defaults EffectiveFromUTC to import time, do not
pretend it proves game-effective time or silently select another season's row. Recommend one
approved weight version across fights and overall; future changes require explicit recalculation
version/correction. Missing weights means DKP unavailable while other metrics remain available.
Convert finite FLOAT values through their round-trip decimal string, retain that source string,
validate representability in decimal(38,12), and reject lossy conversion rather than round silently.
Calculate with sufficient Decimal precision and store DKP decimal(38,6); if a result cannot fit
exactly, block that calculated field/version pending a reviewed precision change. No binary-float
arithmetic in new calculated facts. 10/20/40 examples are synthetic, not active KVK-16 evidence.

Recommend B0 Power as the stable `starting_power`, separately from fight-start power. Zero/missing
B0 power does not manufacture zero DKP: valid combat DKP remains calculable, while DKP/power
ratios are unavailable for nonpositive/missing denominator. This intentionally departs from the
legacy positive-power DKP gate and is part of A04 for G2 review. No new target-setting semantics.

Player overall-to-date is **B0 numerical observation → explicitly selected latest accepted player
observation**, labelled with actual endpoints. B0 time is supplied, so that design is feasible;
5,417 paired at Pass 4 end is coverage, not a final-KVK result. Final player overall pins a separately
designated KVK-end observation. Overall never uses sums of fights or per-player first/last available
fallback. Aggregate overall stays unavailable until its final report, even if player overall exists.

Rank each metric over B0 members with that metric available in the same publication; include
genuine zeros, exclude unavailable values. Sort value descending then GovernorID ascending;
ordinal rank and population are returned together, percentage = rank/population ×100, labelled
top-position percent. Overall player rank basis remains T4/T5 KP (10×T4+20×T5), with the eligible
usable cohort stated; no comparison to kingdom-only targets or another cohort's numerator.

## 5. Field dictionary and availability

Common persisted counter range is integer 0..9,223,372,036,854,775,807 (bigint), with signed
power deltas in bigint range. Arithmetic uses a wider intermediate and rejects overflow. Missing
source metrics are null with status; no coerced zero. IDs require positive integral values;
ambiguous or precision-lost Excel numeric IDs are rejected, not rounded. Decimal/text integers
must parse losslessly; booleans, NaN/infinity, dates, formulas and fractional count values are invalid.

Required identity/header errors, duplicate IDs, unknown kingdom and malformed keyed rows reject
the candidate. Missing/invalid optional numeric cells can be retained as field-level unavailable
with counts; missing required schema headers reject the workbook. No silent name truncation.
Names/Alliance/Civilization use nullable nvarchar(256); overlength labels become unavailable with
diagnostics and raw retention. The parser schema lists all 36 observed player headers; extras
require reviewed schema evolution. Existing legacy aliases are not an implicit new-source schema.

| Source fields (all 36 player headers accounted for) | Units / typed value | New reporting rule |
|---|---|---|
| Governor ID; Kingdom | positive bigint; positive int | Required identity; kingdom in approved scope. |
| Name; Alliance; Civilization | optional bounded literal text | End label or raw profile only; no cross-system profile update. Formula-typed Alliance is quarantined as unavailable text, not evaluated/cached. |
| Power; Troops Power | bigint power points | End values and signed delta; B0 starting power separate. |
| T1 Kills; T2 Kills; T3 Kills | bigint kills | Retain counters and optional explicit tier deltas; not substituted into T4/T5 metrics. |
| T4 Kills; T5 Kills | bigint kills | Exact delta; `kills_gain` = T4+T5 only, explicitly labelled. |
| Total Kill Points | bigint points | Exact total-KP delta; distinct from computed tier-KP. |
| Dead | bigint troops | Total deaths delta; player DKP Z input. Player T4/T5 death split and combined tier deaths unavailable. |
| Healed | bigint troops | Observed counter delta, labelled source healed; not legacy intervening maximum. |
| Acclaim; Highest Acclaim | bigint points | Separate counter deltas; only Acclaim supplies public acclaim_gain. Highest never substitutes for current. |
| Ranged Points; RSS Assistance; Alliance Helps; RSS Gathered | bigint source units | Raw only; no new reporting/profile semantics inferred. |
| Tech Power; Building Power; Commander Power | bigint power points | Raw only; no implied extrema. |
| City Hall; VIP; KvK Played; Autarch Times; Most KvK Kill; Most KvK Dead; Most KvK Heal; AoO Joined; AoO Won; AoO Avg Kill; AoO Avg Dead; AoO Avg Heal | nonnegative integral raw counters/levels | Raw only. VIP zero retained as supplied placeholder, not evidence of actual VIP or a profile overwrite. Invalid optional cells unavailable. |

For aggregates, Kingdom Stats keys are Camp + KD; Camp Stats key is CAMP. Resolve each name
uniquely through the frozen CampMap after trim/casefold/whitespace normalization. Require every
configured kingdom and camp exactly once (36/four for the supplied scope), and agreement between
kingdom row camp and map. No kingdom/camp membership filtering based on eligible player coverage.

| Both aggregate tabs: required metric | Type / unit | Semantics |
|---|---|---|
| T4 Kills; T5 Kills | decimal(38,6), kills | Supplied counts, including abbreviated precision; no player replacement. |
| KP (T4+T5) | decimal(38,6), points | Supplied tier KP, not Total Kill Points. Do not regenerate from rounded kills. |
| Dead; T4+T5DEAD | decimal(38,6), troops | Distinct total deaths and combined tier deaths, both retained. |
| Healed | decimal(38,6), troops | Supplied report metric; no exact legacy healed-extrema equivalence claim. |
| Acclaim | decimal(38,6), points | Supplied current Acclaim report value. |
| DKP | decimal(38,6), points | Supplied authoritative DKP; independent of player weights, no recomputation. |

Aggregate values are nonnegative, less than 10^32 with at most six fractional digits after
expansion; reject overflow/loss rather than rounding. Required aggregate blanks/invalid values
reject both tabs atomically. Each cell retains raw nvarchar(128), Decimal expanded value,
precision kind (`reported_abbreviated`/`reported_numeric`) and displayed unit decimal(38,6).
Accept strict decimal literals with optional K/M/B/T multiplier, case-insensitive, and optional
well-formed thousands groups; reject expressions and ambiguous locale separators. Preserve raw
tokens and spreadsheet number formats as provenance. Exact numeric source cells are exact only
to their stored representation; no claim about undisclosed provider accuracy.

Example `25.3M` → 25,300,000, displayed unit 100,000; `4.779B` → 4,779,000,000,
unit 1,000,000. Expansion is not new measurement precision. Default display/export keeps raw
abbreviation and an approximation label. Machine exports may include expanded Decimal strings
with raw token/unit alongside; never cast through FLOAT or fill missing digits as exact evidence.
Sorting uses expanded reported values and identity tie-breaks; rounded rank positions do not
claim hidden precision. Equality to player sums, camp-to-kingdom sums or reconstructed DKP is
not an acceptance test. No assumption about provider rounding direction or error interval.

Only the contiguous keyed aggregate table is data. A blank separator followed solely by unkeyed
annotations is warning-only with ignored range/count recorded (A1 has nine E39:E47 cells).
A keyed row after the separator, malformed row inside the table, unexpected tab, duplicate key
or populated unknown column blocks acceptance. Formula identities reject the workbook; formula
numeric cells are invalid (required aggregate cells reject both tabs; player metric cells become
unavailable). Optional text formula content is preserved only privately as inert raw evidence, rendered unavailable.
No macros, formulas, links or workbook code execute; v1 admission is XLSX only with bounded ZIP
expansion/row/cell/size limits to be tested in the first approved slice.

Metric state vocabulary: `available`, `missing_start`, `missing_end`, `invalid_source_value`,
`counter_regression`, `unsupported`, `missing_configuration`, `not_applicable`.
Report state adds `not_received`, `validation_failed`, `live`, `final`, `corrected_final`.
Never collapse any unavailable state to zero. Player extrema, per-player capture timestamps,
aggregate total KP, aggregate Highest Acclaim and player tier-death details are unsupported.
Derived healed×20 can remain an explicitly labelled calculated field; tanking/ratio output is
suppressed unless numerator, denominator and metric basis are all available and compatible.
Do not feed aggregate tier KP into a helper expecting total KP under the same old label.

## 6. Revision, finality and publication rules

An aggregate candidate is received → validated or rejected → accepted-live / accepted-final.
Acceptance records actor, reason, expected previous selection and as-of/coverage provenance.
Rejected candidates never change selection. For an open fight, a newer validated live as-of
may supersede the active live revision after metadata acceptance. Older arrivals are retained
as history and do not win by arrival time. Equal as-of with changed content requires correction.
Every normal live report covers that fight start through its declared live end; final report
covers the declared entire fight. Actual player scan starts may differ and remain labelled.

A final aggregate locks its report family. New live or backdated uploads cannot replace it.
Admin final-correction explicitly names the selected final revision, gives a reason and chooses
a validated replacement (which may have the same or corrected as-of/period metadata). It creates
a corrected-final revision, remains final, retains predecessor, and atomically selects a new
publication. No normal reopen-to-live action is recommended. Incorrect fight assignment moves
through a reviewed supersedes/retraction event and independent new period, never silent retagging.

Player finalization pins exact start/end observation revisions for each configuration version.
An authorized EndScanID update follows the workflow above and selects a replacement final once
available, without a separate correction command; old versions remain immutable. A corrected player observation
does not mutate any pinned final; show affected publications and require explicit corrections.
Live dependent periods may rebuild against the accepted correction via generation checks.
Final aggregate can be accepted without final player observations and vice versa: publish the
final stream plus explicit unavailable/live other stream. Mark the **whole publication final**
only when required configured streams are final, or admin explicitly records a final unavailable
stream with reason. Partial coverage of individual B0 members is still shown honestly in a final.

Overall aggregates have a separate report family, accepting final/corrected-final only. Before
receipt, display “Overall kingdom/camp report not yet supplied”; never populate Overall or
ALL_WINDOWS from fights. Baseline/equal-endpoint no-fight periods produce zero player delta only
for valid identical observations and no combat rank; aggregate state is `not_applicable`.
No-fight periods cannot accept a fighting or cumulative report.

### Atomic storage and recovery

1. Admission records an attempt and validates privately, without changing selection. Original
   bytes are stored durably under a generated content-addressed path outside Git; verify durable
   presence/hash before SQL references them. Orphan files are harmless retained evidence.
2. One SQL transaction stores an accepted observation revision and all its player rows, or an
   aggregate revision and **both** kingdom/camp row sets. Uniqueness checks serialize concurrent
   aliases/corrections. Parsing and external network work stay outside this transaction.
3. Service builds immutable candidate facts from explicitly pinned inputs/config snapshots.
   Candidate completeness/count/digest validation occurs before selection; incomplete candidate
   rows are never queried as published facts. Large builds can stage in bounded batches.
4. A short transaction locks the selection scope, compares expected SelectionVersion and all
   referenced config/input selections, marks the complete candidate publishable, swaps its pointer
   and inserts a durable notification/outbox event. No legacy recompute is called. Stale builders
   must rebuild from current inputs; do not retry a blind pointer overwrite.
5. Readers resolve one publication at request start and fetch its immutable facts. Publication
   after that point does not mix player/kingdom/camp generations. SQL commit precedes cache/export
   work. An outbox key `(PublicationID, DestinationKind, DestinationID)` deduplicates retry intent.

Crash before acceptance commit leaves no accepted facts; retry is safe by attempt identity.
Crash after fact commit leaves accepted-but-unpublished data; resume candidate building, not
re-import with a new scan. Crash after pointer commit returns the already selected publication
on retry and resumes outbox work. Recovery queries durable states, never infers rollback from
timeout, absent process or in-memory locks. SQL key constraints plus transaction locks protect
concurrent workers; no claim of cross-service exactly-once external delivery.

## 7. Proposed physical entities and layer ownership

These are candidate names/types for architecture review, **not existing SQL objects or DDL**.
New objects use KVK schema, additive reviewed migrations plus reference snapshots later.
No legacy object alteration, ProcConfig procedure insertion or new UDT is needed just to design.
All new UUIDs use uniqueidentifier; audit UTC uses datetime2(0), timestamps carry explicit precision.
Hashes use binary(32), enums constrained varchar(32), version counters positive int/bigint.
Every entity's source/season references must match; logical constraints below require SQL-backed
enforcement in Phase 2B design, not only application assumptions.

| Candidate object | Principal key / payload and constraints |
|---|---|
| KVK.SourceArtifact / SourceImportAttempt | ArtifactHash PK; private generated location nvarchar(512), size bigint, original aliases in attempts. AttemptID PK, unique replay key, actor and outcome; no public file contents. |
| KVK.SourceObservation / SourceObservationRevision | ObservationID PK, unique source/KVK/time/precision/discriminator, selected RevisionID and monotonic selection version guarded by CAS. RevisionID PK, unique observation/revision; semantic hash/version, artifact reference, supersedes, acceptance state. |
| KVK.SourcePlayerSnapshot | PK revision/governor; kingdom int, name nvarchar(256), dedicated bigint counter columns from dictionary, per-field availability; optional raw profile cells retained without daily-profile writes. |
| KVK.SourceRoster / SourceRosterMember | RosterID PK; B0 revision FK, approved scope hash, version/reason. Member PK roster/governor, B0 kingdom and nullable B0 power. |
| KVK.SourceConfigVersion | ConfigVersionID PK; KVK, validated immutable Windows/Map/Weights snapshots, source row/hash provenance and explicit approval. Child typed snapshot rows mirror existing column types; coefficient strings plus decimals retained. No cascade from mutable config imports. |
| KVK.SourcePeriod / SourceLogicalScan / SourceScanBinding | PeriodID PK, unique source/KVK/key; type and declared bounds. Scan PK source/KVK/logical-int. Binding PK config-version/scan; observation FK. Period records bind exact Windows name and start/end slots within that config version. |
| KVK.SourceAggregateReport / SourceAggregateRevision | ReportID PK unique source/KVK/period; RevisionID PK unique report/revision; as-of, coverage bounds, live/final, predecessor and metadata approver. |
| KVK.SourceKingdomReportRow / SourceCampReportRow | PK revision/kingdom or revision/camp; required eight Decimal metrics, raw tokens/units and validated map identity. Both tabs share revision and commit. |
| KVK.SourcePublication / SourcePlayerResult | PublicationID PK; unique source/KVK/period/generation; exact observation revisions, aggregate revision (nullable), roster/config/calculation versions and manifest hash. PlayerResult PK publication/governor; nullable metrics and statuses, rank cohort counts. Aggregate facts reference immutable report rows, no duplicate computed aggregate authority. |
| KVK.SourceSelection / SourceRouting | Selection PK KVK/period with SourceKey, PublicationID and SelectionVersion. Routing PK KVK; selected source, displayed fight and activation version. Disabled by default; updates audited/CAS guarded. |
| KVK.SourceAction / SourceDelivery | ActionID and actor/expected-version/reason/old-new IDs. Delivery PK publication/destination-kind/destination-ID; pending/confirmed/failed/uncertain, receipt and retry history. |

Indexes: unique natural identities above; observation revision/governor for endpoint joins;
publication/governor and publication/kingdom/camp/metric for bounded reporting; report/as-of for
live selection; outbox state/created UTC for recovery. Compute player ranks once per generation.
No speculative performance claim: measure representative cohort size, locks and plans in isolated
SQL validation later. Keep accepted originals/revisions/config/publications through programme
closeout and agreed retention thereafter. Cleanup may remove abandoned staging only; referenced
facts, originals, final history and delivery evidence cannot be deleted by legacy cleanup.

Proposed Python responsibilities follow the existing `kvk/` package: schema/models for pure
parsing contracts; services for metadata/roster/revision/calculation/publication policy; DAL for
parameterized persistence, locks and generation-bound reads; upload route for admission only.
Existing reporting/export services receive source adapters. Commands/views perform authorization,
defer, call services and present receipts; no SQL or calculation logic. Keep new domain logic out
of DL_bot.py, gsheet_module.py and Commands.py beyond thin adapters. Exact filenames/manifests
belong to Phase 2B; this table does not authorize creating those modules or migrations.

## 8. Shared consumer contract and migration map

Recommend `ReportSnapshotV2`: schema_version, SourceKey, KVK_NO, PeriodID/type/label,
PublicationID, SelectionVersion, generation, roster/config/calculation IDs, independent player
start/end/as-of and aggregate coverage/as-of/revision/finality, overall status, coverage counts,
metric definitions/units/precision/status, and the established named reporting blocks. Decimal
values cross JSON boundaries as strings. Missing blocks include reason; never use an old default
zero or indistinguishable empty list. DAL resolves pointer once; service owns interpretation.

Legacy adapter retains legacy values and labels its source/basis; do not advertise reproducible
new-generation history for mutable legacy recompute. Reuse block names and renderer packing,
not naked tuple positional assumptions. Unsupported V2 consumers fail clearly for the new source.
An explicit requested period never falls back to another KVK/fight. Default fighting report uses
the operator-selected active fight (latest finalized fight stays visible until another is selected),
not the sum of configured fights. Overall is separate explicit selection.

Resolve the active routing version, requested/default PeriodID and selected PublicationID in one
DAL transaction before loading facts. An activation/displayed-fight change must verify its target
selection exists and update routing atomically; a concurrent switch cannot splice two periods.

| Phase 1 IDs | Affected surface / owning layer | Required new-source behavior |
|---|---|---|
| C01–C07 | Intake, parser, audit / route + services + DAL | Separate XLSX admission and durable metadata; legacy Full Data unchanged; best-effort ImportAudit supplements authoritative state. |
| C08–C14 | Ingest/baseline/recompute / new DAL + calculation service | Source facts, fixed roster, exact endpoints, immutable outputs; never call legacy recompute for new data. |
| C15–C19 | Aggregated functions, FightingDataset, overall rank / source-aware DAL | Preserve legacy objects; bypass sum functions for new reports. New rank uses same-publication usable B0 cohort; no direct union of incompatible schemas. External readers require inventory before cutover. |
| C20–C25 | Twelve named Top/own-summary blocks / reporting DAL/service | Player metric ranks from selected player facts; kingdom/camp DKP directly supplied, never coefficients or rollups. Return precision and availability; remove new-source missing-Acclaim→0 behavior. |
| C26–C28 | Fighting embeds and post-processing dispatch / renderer + orchestration | Same envelope for all blocks, explicit fight/live/final and each as-of. Preserve packing, visibility, receipts and daily three-post policy. Daily processing trigger is not new-source freshness proof. |
| C29–C34 | Ten SQL export sections, binder, Sheets / export service + DAL | Version schemas deliberately: scan log becomes explicit observation/revision provenance, Windows/config come from publication snapshot, player/kingdom/camp Windowed/Full sections are selected period facts, negatives become typed diagnostics. Keep section names only with V2 contract; no positional legacy misbinding. |
| C32–C34 | ALL_WINDOWS/comparison/per-fight tabs / export service | Per-fight columns select one revision each; blanks/status for unavailable. Overall selects separate final aggregate; player overall is B0→end, never fight sums. Legacy generic summation not invoked. Key groups by IDs, display names only labels. |
| C35–C39 | export_all/recompute/list_scans/window_preview/test_embed / admin service + DAL | Source-aware explicit diagnostics. Recompute means candidate rebuild against pinned inputs, cannot modify finals without correction. Scans display namespace/revisions/time. Export/preview pins publication and preserves isolated-session behavior. |
| C40–C43 | Mixed /kvk stats card / card service + DAL | Retain kingdom-only main stats/targets. Whole-KVK camp/rank appears in a separately labelled context block with period, source and cohort; suppress if renderer cannot show distinction or requested player/metric unavailable. Never use whole-KVK rank to imply rank of the card's independent numerator. |
| C44–C60 | KS4 cache, outputs, history, rankings, targets, /me, /stats player, daily exports, standalone KS/calendar | Independent; preserve sources and lifecycle. Do not migrate or populate from whole-KVK source. C54 versioned-cache idea and C64 text escaping may be reused without changing their owners. |
| C61 | Config import / source configuration service | Existing sheet importer unchanged in this phase; capture and validate committed config snapshots before selecting a new generation. Import completion alone cannot prove postcommit effects or source readiness. |
| C62 | Legacy cleanup | Does not own new retention or rollback. |
| C63 | Daily-scan lifecycle | Preserve dispatch eligibility; whole-KVK observations never allocate daily scans or mark lifecycle complete. |
| C65 | Startup/cache scheduling | Recover durable selections/outbox without automatic recompute/final reselection or public resend. |

Whole-KVK history browsing retains source/period and exact new publication links. Cross-KVK
comparison requires identical metric definitions, period kind, cohort basis and weight basis;
otherwise show side-by-side labelled facts with comparison/rank unavailable. No mixed-source
start/end within a window. No retrofitted extrema, heal-history equivalence or missing tier deaths.
The independent `/kvk history` source is unchanged; this design does not promise to populate it.

## 9. Cache, delivery and rollback

Cache keys include schema/source/KVK/period/PublicationID/SelectionVersion; immutable publication
includes roster/weight/map/endpoint/report identities. Selection changes invalidate pointer caches;
read the authoritative pointer per new request so lost notifications cannot cause indefinite stale
success. A warm old payload may be shown only with its explicit old generation/as-of/stale status;
never serve it labelled current after a failed refresh. On restart load durable selections, not
MAX scan. Request-held views remain pinned and labelled; refresh resolves a new envelope wholesale.
Final/correction actions revalidate expected selection, actor and period instead of trusting a view.
Do not purge independent player/target/history caches or reset CSV daily send claims.

SQL publication success, export completion and Discord delivery are different receipts. Re-export
duplicates do not enqueue work. A new publication can enqueue export refresh; normal public posts
still obey existing cadence/admission. Automatic correction announcements are not introduced.
Retry external writes by destination/publication; stale queued work cannot overwrite a newer
destination generation. Use a serialized destination worker and recheck selected generation.

Sheets cannot atomically change multiple remote files. Recommend write new generation tabs/files
privately, verify expected sections, then update the discoverable manifest/link to completed output.
Label incomplete exports and keep the previous complete link; never expose partial tabs as current.
Retry known idempotent ranges with RAW values. Discord accepted/uncertain outcomes use receipt
reconciliation; never create a replacement merely because a response timed out. Existing daily
claim ownership and preview session rules remain binding. New receipt integration must be tested
in the later consumer slice; this is no general dispatch reliability redesign.

Rollback preference: stop new intake/publication/delivery writers; retain backups and durable
receipts; select the last validated new-source publication with a new SelectionVersion; invalidate
dependent caches and reconcile pending destinations. For source fallback, choose legacy only
where retained legacy facts actually cover the requested period, explicitly label source and
coverage, and validate compatible consumers. If none exists, keep last valid new result visibly
stale or return unavailable. Do not claim uninterrupted replacement history.

Older bot code unaware of the source must not continue public delivery after activation: first
disable affected reads/delivery or restore verified legacy routing and caches. Keep additive SQL
and original data; dropping tables is not routine rollback. Bot-only downgrade cannot undo SQL
selection, frozen versions, downloaded exports or sent messages. Preserve/reconcile uncertain
receipts before retries. Config snapshots survive later replace-imports, and legacy recompute
cannot overwrite new facts or selections because it never addresses these objects.

## 10. Operator journey and scope of future interface changes

Recommend one private intake channel distinct from legacy, admitting one workbook per confirmation.
Only configured uploader role plus existing KVK admins may create candidates; channel ACL alone
is insufficient. Server/channel/type/size checks occur before parsing; actor/guild privileges are
rechecked before acceptance. Finalization, roster/config changes, correction and source activation
remain KVK-admin-only. No player-level error rows posted publicly; private feedback gives counts,
field names, intended period and precise state (“validated”, “accepted”, “published”, “export failed”).

Journey: upload → metadata/coverage preview → accept live → status receipt. Next same-fight live
report supersedes the selected live values after validation. End of fight: select exact player
endpoint through EndScanID and mark aggregate final separately; review stream finality/coverage.
Later EndScanID changes use the normal authorized configuration workflow above. Correct source-content final:
name final receipt, upload replacement or select corrected player revision, give reason, inspect
impact and confirm against current selection. The original final remains available by revision.

Recommend one future grouped `/kvk_admin source` entry for status/resume/finalize/correct via
an action option and receipt identifier; upload confirmation can use short-lived owner-bound
controls. This proposes **one grouped subcommand, zero new top-level commands**, not registration
now. Phase 2B must check canonical command reference, version/usage/safety decorators, permissions,
option inventory and existing diagnostics before fixing its exact surface. Persist work in SQL;
expired controls resume via receipt, not a persistent view as sole state. No role/channel creation
or public command change is authorized by this design.

## 11. Draft slice sequence, evidence and G2 review

This is a feasibility sequence, not executable implementation packs or approved manifests.

| Draft slice | Boundary / dependency | Acceptance focus |
|---|---|---|
| S1 | Pure offline schemas/parser/metadata/digest models; no routes, SQL or publication | Re-export equality, strict identities/precision, formula safety, synthetic cells; existing importer unchanged. |
| S2 | Additive SQL facts/config/selection contracts, publication disabled; after S1/G3 approval | Separate SQL review; constraints, transactional both-tab acceptance, concurrency and restart in disposable SQL. |
| S3 | Bot DAL and pure calculations/candidate publication, source disabled; after S2 | Exact endpoints, roster/cohorts, weights, CAS/final correction and crash recovery. |
| S4 | Shared reporting/export/card adapters and generation-aware reads; after S3 | All mapped consumer contracts, unsupported/precision labels, legacy and independent-system regressions. |
| S5 | Private intake/admin journey and durable delivery integration; after S3/S4 | Permissions, receipts, retries, partial exports, no daily-claim reset; disabled by default. |
| S6 | Separately authorized configuration onboarding/shadow and controlled release | Live readiness inventory, rollback rehearsal, operator smoke; no activation through an ordinary import. |

Before dependent implementation/release: capture redacted current KVK-16 Windows, CampMap,
Weights and Details row values/version; both scan namespaces and exact mappings; committed config
import receipt; migration history/module hashes; relevant Agent job steps/schedules and external
readers; channel/role inventory. Use authorized read-only evidence only, never credential discovery.
Operator-attested SQL/config parity is recorded; actual live rows/jobs were not independently queried.
No RDP is needed for G2. Optional aggregate live/final examples can validate metadata when available;
synthetic cases suffice now and no later fight/final overall is requested.

Refactor disposition: new source policy belongs in services/DAL; no fixes now. Legacy summation/name
grouping debt is already captured in the deferred register. ProcConfig WS1 is separate and no design
prerequisite is proved; new publication readiness must validate its own committed config snapshot.
No new unrelated debt, helper or runtime change. Proposed reuse: named export binder mechanics,
ImportAudit observability, canonical embed limits/packing, safe_defer/permission conventions and
RAW/formula-safe export conventions after contract tests. Do not reuse legacy null-to-zero rules,
upload timestamp, baseline growth or non-versioned deduplication.

**G2 review:** approve or revise A01–A08 as one architecture packet. The material discretionary
choices are B0 attribution/starting power with DKP independent of power, explicit partial-live
stream display with frozen finals, and the single private intake/admin correction journey. The
recommendations above resolve the engineering choices; no source-policy questions are reopened.
Approval permits Phase 2B to prepare exact implementation plans only. **Stop at G2: no self-approval,
Phase 2B packs, code/tests, SQL, imports, processing, exports, Discord actions or deployment.**


## Phase 2B delivery and G2 approval — 2026-09-09

Chris Watts explicitly approved: **“G2 approved, please proceed”.** G2 is approved, including
the EndScanID clarification and scenarios T68–T70. This supersedes earlier G2-pending/no-pack
statements as current status; their historical evidence remains intact. Phase 2B planning is
delivered in the [implementation plan](phase_2_implementation_plan.md)
and [planning evidence log](phase_2b_evidence_and_validation_log.md).
Ten bounded task packs and matching starters are prepared. **G3 remains pending per slice; S1 is
the recommended first approval.** No implementation, SQL change, live action, PR or deployment
is authorized by this delivery. S6 prepares readiness evidence and stops at separate G4 approval.

## 2026-09-12 post-S6 operator contract amendment

The settled requirements in [post-S6 integration requirements](post_s6_integration_requirements.md)
supersede conflicting earlier recommendations in this document. In particular A06
no longer permits publishing a new partial player/aggregate pair to ordinary public
readers: retain the last complete eligible generation while the pair is incomplete,
with honest waiting/stale labels. Independent private acceptance and diagnostics
remain supported. A fixed per-KVK source identity must not be conflated with the
serving-enabled flag; disabling new-source serving does not authorize legacy fallback.
Spreadsheet reuse after KVK does not erase immutable input/publication history.

Authorized EndScanID updates remain corrections in their own right. Pairing and
counterpart confirmation must not add a separate player correction command or
silently replace aggregate authority. This is an approved behavior amendment,
not proof that existing code implements it. S7 designs the transitions and exact
separate-repository manifests before subsequent implementation approval.
