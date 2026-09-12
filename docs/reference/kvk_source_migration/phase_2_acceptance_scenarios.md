# KVK Source Migration — Phase 2A synthetic acceptance scenarios

## Current delivery and next slice — 2026-09-12 post-S6 closeout

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

**Next: S7 Integration Contract and Implementation Planning**, documentation/read-only
scope after explicit S7 approval. Do not rerun predecessors or start later packs.
Carry every path in the post-S6 handoff manifest into the next separately authorized
slice PR, including both S6 archive move sides. No Git publication, SQL/provider
execution, restart, production promotion or activation is authorized by this update.
Earlier dated blocks below are historical and do not select the next task.

[Settled requirements](post_s6_integration_requirements.md); [handoff and exact manifest](post_s6_handoff_log.md); [S7 pack](../../task_packs/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S7%20Integration%20Contract%20and%20Implementation%20Planning.md).

2026-09-09. Proposed executable-test requirements for G2 review, **not test implementation or
passing runtime evidence**. All player/kingdom/camp identities and numbers below are synthetic.
Source coverage counts in the evidence log are observations, not fixtures or universal constants.
Rules and ownership follow [the architecture contract](phase_2_contract_and_architecture.md).

## 1. Worked player example

Synthetic roster R1 contains P-A, P-B, P-C, P-D (symbols stand for positive IDs in future fixtures),
attributed to B0 kingdoms K-A/K-B. P-X is a later-only outsider. Config W1 has synthetic X=10,
Y=20, Z=40; these are **not verified active KVK-16 coefficients**. P-A B0 power is 100,000,000.
F-start, F-middle and F-end are three observations of the same fight, not aggregate revisions.

| Player / observation | T4 | T5 | Total deaths | Total KP | Power |
|---|---:|---:|---:|---:|---:|
| P-A start | 100 | 200 | 50 | 6,000 | 100,000,000 |
| P-A middle | 120 | 230 | 55 | 6,850 | 99,000,000 |
| P-A end | 140 | 250 | 60 | 7,500 | 98,000,000 |

Start→middle: T4=20, T5=30, deaths=5, tier KP=800, total KP=850, DKP=1,000,
power delta=-1,000,000. Start→end: T4=40, T5=50, deaths=10, tier KP=1,400,
total KP=1,500, DKP=1,800, power delta=-2,000,000. The DKP/power fraction is 0.000018
using B0 power, before any presentation scaling; never sum starting power across intervals.

P-B has identical valid start/end counters: publish genuine zero. P-C lacks start: unavailable
even if B0 and middle exist. P-D has start/end but no middle: final gain is valid. P-X has all
observations: excluded from facts/ranks. With P-A/P-B/P-D having valid tier KP, rank population
is 3, not the four-member roster or five observed players. Missing total KP alone does not
remove a valid tier-KP rank; missing T4/T5 does. Ties use the underlying numeric GovernorID.

## 2. Worked report/revision example

Synthetic Pass-X report family has two live revisions and a final. Both tabs are always together.
For one kingdom, supplied DKP is 1.20M → 1.35M → 1.40M. Selected displayed values are
1.20M, then 1.35M, then 1.40M, **never 3.95M**. A supplied camp final of 2.90M remains
2.90M even when rounded kingdoms sum to 2.89M. Player DKP disagreement does not reject either.

Another synthetic fight final supplies 0.80M. The final overall report supplies 2.50M: overall
must show 2.50M, not the fight sum 2.20M. Before overall arrives it is not_received, not zero.
An admin correction changes the first final to 1.41M with reason and predecessor; the previous
1.40M publication remains reproducible, and overall still reads its separate 2.50M report.
No arithmetic reconciliation can overwrite those supplied authorities.

## 3. Identity, parsing and metadata cases

| ID | Input / precondition | Expected persisted/selected outcome | Future owner |
|---|---|---|---|
| T01 | Exact artifact retry, same attachment/action or renamed upload | Existing acceptance returned; alias attempt retained; no duplicate facts, generation or external intent. | Parser/admission/DAL |
| T02 | Different ZIP/style bytes; every keyed value and confirmed event equal | Same semantic digest v1; second artifact alias, one observation revision. Model real F1S/P1 and F1E/P2 relationship with synthetic cells. | Offline parser |
| T03 | Reordered rows/sheets with unchanged typed cells | Digest unchanged after canonical sorting; duplicate IDs still reject before hashing. | Parser |
| T04 | Same event/time, one T4 value changed | Pending correction; previous selection intact until authorized target/reason; new revision afterward. | Revision service |
| T05 | Same event/time, name/formula type/precision changes only | Different semantic digest; no silent equivalence. Optional labels may change through correction, never identity joins. | Parser/service |
| T06 | Same artifact presented under another fight/time | Identity conflict, no automatic new scan. Reviewed true distinct event may be accepted with provenance, even if counters equal. | Metadata service |
| T07 | Older live upload arrives after newer live as-of | Retain history; newer as-of remains selected. Arrival/revision number does not determine latest. | Selection DAL |
| T08 | Equal scan-start events or second timestamp claimed for minute observation | Ambiguity requires explicit event/precision provenance; no nearest-time merge. | Metadata service |
| T09 | `kvk16_players_20260905T1526Z.xlsx`, optional terminal ` (1)` | 15:26 UTC, minute precision; upload time and filesystem timestamps irrelevant. Seconds variant preserves seconds precision. | Parser |
| T10 | Invalid calendar date, ambiguous legacy filename or name/metadata conflict | No guessed timestamp; explicit valid metadata confirmation required; conflicts reject acceptance. | Metadata service |
| T11 | UTC times on either UK DST transition | Same UTC observation and identity throughout; no ±1-hour conversion. | Parser |
| T12 | Valid B0 with no filename time; operator supplies 2026-08-26 04:07 UTC | Membership accepted separately; numerical use pins attested time/revision, not file timestamp. | Roster/metadata |
| T13 | Duplicate/negative/fractional/precision-lost ID; unknown kingdom; formula identity | Reject candidate before fact selection; no rounding, no partial admission. | Parser |
| T14 | Formula-typed Alliance, blank Alliance and VIP=0 | No formula/cache evaluation; Alliance unavailable with private raw provenance, null distinct from empty numeric zero; VIP does not overwrite profiles. | Parser/export |
| T15 | Formula numeric cell, NaN, infinity, overflow, malformed integer | Required aggregate rejects both tabs; player metric unavailable with diagnostic; derived dependent field unavailable. Invalid identity rejects entire file. | Parser/calculation |
| T16 | `25.3M`, `4.779B`, `1.0M` versus `1.00M` | Expanded values 25300000/4779000000 and units 100000/1000000; differing precision tokens do not deduplicate. Raw precision survives DAL/cache/export. | Parser/DTO/export |
| T17 | One missing aggregate tab, duplicate camp, missing kingdom or camp-map conflict | No aggregate revision accepted/selected; previous report remains selected and labelled with its old as-of. | Parser/DAL |
| T18 | A1-shaped blank separator and nine unkeyed tail numbers | Warn with ignored range/count; 36 keyed kingdoms, not 45; no player-row leakage. A keyed row after separator instead rejects. | Parser |
| T19 | Unknown column/tab, oversized ZIP expansion, unsupported XLS/CSV | Fail closed with structural reason; no fallback legacy import or workbook execution. Exact limits set/tested in approved S1. | Admission/parser |
| T20 | Canonicalizer v2 deployed after v1 observations | No automatic historical merge/reselection; retain v1 digest and revision identity. | Model/service |

## 4. Players, periods and authority cases

| ID | Input / precondition | Expected facts and display | Future owner |
|---|---|---|---|
| T21 | Worked P-A endpoints and W1 | Exact DKP 1800, tier KP 1400, total KP 1500, signed power -2000000; independent metrics preserved. | Calculation |
| T22 | P-C missing start but present B0/middle/end | Fight gain missing_start; neither B0 nor middle substitutes. | Calculation |
| T23 | Eligible player missing end; another missing both | No zero activity; explicit availability and coverage counts. | Calculation/reporting |
| T24 | P-D start/end but absent middle | Final gain available; no all-three-observation requirement. | Calculation |
| T25 | Later-only P-X has very high gain | No published player fact/rank or denominator inclusion; private excluded count only. | Roster/ranking |
| T26 | P-B valid zero delta | Available zero and eligible rank; distinct from missing or failed scan. | Calculation/ranking |
| T27 | T4 decreases while T5/power valid | T4 regression and DKP/tier-KP unavailable; signed power and independent T5 remain valid; no clamp/absolute value. | Calculation |
| T28 | B0 power zero, valid endpoints/weights | DKP valid under proposed A04, power ratio unavailable. Missing weights instead makes only DKP/dependent values unavailable. | Calculation |
| T29 | Config later imports another weight/map version | Existing final publication unchanged. New selection requires explicit validated config version; no latest-row mutation of history. Authorized EndScanID changes are the distinct correction case T69, not permission to apply unrelated config changes. | Config/publication |
| T30 | Player changes name/kingdom after B0 | Single GovernorID fact; B0 kingdom attribution retained, end display label selected, diagnostic records move; camp report not recomputed. | Calculation/export |
| T31 | Logical ID 220 also exists as legacy ScanID and daily SCANORDER | Resolver uses SourceKey/KVK/config mapping only; no collision, namespace inference or shared allocation. | DAL/resolver |
| T32 | Configured closed end absent; later unrelated scan exists | Final missing_end, no MAX cap or nearest match. Explicit live preview retains separate label/end. | Resolver |
| T33 | Open fight start present, accepted middle associated to it | Start→middle live result; end remains pending. Later unassociated observation cannot become live endpoint. | Resolver |
| T34 | Baseline/no-fight start=end and valid observations | Zero player delta, no combat rank, aggregate not_applicable; unrelated aggregate rejected for that period. | Resolver/service |
| T35 | Worked aggregate revisions and camp disagreement | Select latest accepted revision only; directly supplied DKP/camp values retained. No equality gate with player rollup. | Reporting DAL |
| T36 | Overall report absent, fights final and player B0→latest available | Player overall-to-date separately labelled; aggregate overall not_received; no fight sum and no implied KVK completion. | Reporting/export |
| T37 | Separate final overall supplied, or corrected fight afterward | Overall value stays its own selected report; corrected fight does not alter it. | Period service |
| T38 | A1 format sample has unverified fight coverage | Retain as evidence/candidate; cannot publish as Pass 4 solely from similar arithmetic or filename. | Metadata |
| T39 | Player end and aggregate as-of differ within same fight | Coherent publication pins both and labels each actual time/coverage; no artificial simultaneous logical scan. | Report DTO |
| T40 | Request finalization with final aggregate but missing player final | Aggregate final may display; player stream explicitly live/unavailable; complete-period final waits or records reviewed final-unavailable reason. | Finalization |

## 5. Corrections, transactions, consumers and recovery

| ID | Fault/action | Expected selection / retry behavior | Future owner |
|---|---|---|---|
| T41 | Live upload after aggregate final | Preserve final; late live retained/unselected. No reopen. | Revision service |
| T42 | Same content explicitly marked final after live | Finalization event pins same content; dedup does not swallow state transition; one final publication intent. | Revision service |
| T43 | Admin corrects selected final with reason and expected revision | New corrected-final/publication selected atomically; old final retained. Stale expected revision conflicts without writes. | Service/DAL |
| T44 | Player correction touches multiple finalized publications | Corrected observation retained; finals remain pinned until explicitly reviewed individually; live rebuilds CAS guarded. | Service |
| T45 | Roster correction adds/removes member | New roster version and impact preview; no automatic historical rewrite, no ordinary later-scan roster growth. | Roster/publication |
| T46 | Crash during kingdom insert before camp insert | Acceptance transaction rolls back both; neither half becomes selected. Retry uses same attempt. | SQL DAL |
| T47 | Crash after accepted facts, before candidate completion | Durable accepted state remains; resume candidate build; incomplete candidate never served. | SQL/service |
| T48 | Crash after pointer commit before acknowledgment/cache event | Retry discovers committed publication/outbox; no duplicate generation or extra public send. | SQL/recovery |
| T49 | Two builders from selection v7, one player and one aggregate update | One CAS succeeds; loser rebuilds from new pointer and includes both updates rather than overwriting winner's stream. | Publication DAL |
| T50 | Two identical concurrent uploads/corrections | SQL uniqueness and expected-version checks permit one logical acceptance; loser returns duplicate or conflict, no second selection. | SQL DAL |
| T51 | Config changes while build runs | Frozen source inputs remain stable; stale build cannot select. Rebuild against the validated desired configuration; authorized EndScanID correction may select a replacement under T69. Historical final versions remain unchanged. | Publication DAL |
| T52 | Reader starts at G4; G5 selected between Top/player/camp reads | Every block returned from G4; next request G5. No mixed generation within a response. | Reporting DAL |
| T53 | Cache notification lost; process restarts | New request reads authoritative selection and correct version key; no successful-current label on old cache; restart does not recompute finals or reset claims. | Cache/recovery |
| T54 | Request-held view G4 receives refresh/correct after G5 | Refresh replaces whole envelope; correction rejects stale expected selection and rechecks current actor privilege. | UI/service |
| T55 | New aggregate reader, export binder or renderer sees absent total KP | Explicit unsupported; no tier-KP substitution, null→zero or legacy DKP recalculation. Contract-version mismatch fails clearly. | Consumer adapters |
| T56 | ALL_WINDOWS/comparison tabs contain two fights and absent overall | Fight columns select individual reports, blanks/status for missing, overall unavailable; no summation or default-zero pivot. | Export service |
| T57 | Partial remote Sheets write then timeout | Current manifest/link remains previous verified export; incomplete generation labelled private; retry same ranges/generation. No all-sections-success claim. | Export delivery |
| T58 | Stale queued G4 export runs after G5 selection | Destination serialization/version recheck blocks stale overwrite; G5 remains discoverable. | Delivery worker |
| T59 | Discord send/edit result uncertain | Retain uncertain receipt and reconcile; no blind replacement or fresh claim. New source selection does not reset existing daily three-post counter. | Existing delivery adapter |
| T60 | /kvk stats main KS4 metrics plus new B0 overall context | Main metrics unchanged; separate labelled context/cohort/as-of or suppressed context. Never represent rank as rank of independent numerator. | Card service |
| T61 | Legacy recompute runs while new source active | Only legacy tables change; new pointers/facts intact. Legacy browsing/exports retain values and source semantics. | Regression SQL/DAL |
| T62 | /kvk history/targets/rankings, /me, daily exports and standalone KS | Independent KS4/target/history/calendar sources and caches unchanged; no new-source profile/VIP writes. | Regression owners |
| T63 | Unsafe name/formula-like text in CSV/Sheets/Discord | Literal inert text, RAW Sheets, CSV prefix protection, safe mentions/packing; no workbook evaluation or path from filename. | Parser/rendering/export |
| T64 | Uploader loses role, wrong guild/channel, other user acts on receipt | Reject before acceptance/final action; SQL workflow remains intact; no public private-row diagnostics. | Admission/UI |
| T65 | New-source rollback to older valid publication | SelectionVersion increases, caches refreshed, pending destinations reconciled; originals/finals retained. | Recovery |
| T66 | Legacy fallback requested without legacy observations for period | Explicit unavailable/stale retained new result; no fabricated legacy report or source splice. Old-bot downgrade blocks affected delivery until routing safe. | Recovery |
| T67 | Cross-KVK history has different DKP/metric/cohort basis | Label separate facts; comparison/rank unavailable unless genuinely comparable. No absent legacy precision/extrema filled with zero. | Reporting |
| T68 | StartScanID=10; successive accepted scans 11 and 12; EndScanID blank or 13 not yet available | Publish normal interim 11−10 then 12−10; replace rather than add. New distinct player scans advance registry; duplicates/re-exports/corrections/aggregate uploads do not. A delayed older event cannot win by larger ID. | Registry/resolver |
| T69 | EndScanID=13 with scan 13 present; later authorized config update to 14 with scan 14 present | Final 13−10 then replacement final 14−10 through normal config processing. No extra finalize/correct command; new config/publication version, old final retained, weights/map not implicitly changed, aggregate selection unchanged. | Config/publication |
| T70 | Authorized EndScanID=14 update while 14 absent, processing fails or two updates race | Desired endpoint/config marked pending; old 13 result not labelled final against 14. Usable interim endpoint explicit. Arrival of 14 resumes validated idempotent publication; stale builders cannot overwrite newer config/selection. | Config/recovery/cache |

## 6. Validation allocation and limits

S1 covers T01–T20 with pure synthetic models; later service tests cover T21–T45. SQL transactions,
constraints and concurrency (T46–T52) require a disposable SQL Server validation environment,
not mocks alone. Cache/consumer/delivery/permission/regression cases T53–T67 combine deterministic
service tests with separately approved private smoke and fault injection. Retain existing legacy
tests, especially `test_kvk_all_recompute_sql_contract.py`, as legacy expectations rather than
changing them to approve new semantics. Existing reporting/export/card tests are regression anchors.

No fixture, test file, workbook, SQL data or application state was created by this document.
Worked arithmetic is document evidence only; actual safe document check results are in the
[validation log](phase_2_evidence_and_validation_log.md). Optional real aggregate revision samples
can follow; no unavailable later fight or final overall report is required to review these cases.
**Stop at G2.**

## Post-S6 acceptance additions — required, not executed

These supplement the original T01–T70 evidence without changing historical results.
S7 assigns exact test files; later implementation validates these at its own revisions.

| ID | Scenario and required outcome |
|---|---|
| S7-T01 | Fixed legacy/new source selected before KVK; cross-source import and mid-KVK change rejected; restart retains choice |
| S7-T02 | Every affected ordinary public output selects chosen source; no diagnostic injection required; disable/unavailable never silently changes season source |
| S7-T03 | Player-first and aggregate-first acceptance both wait; only compatible complete pair advances public publication and export intent |
| S7-T04 | Wrong KVK/period/coverage/revision pairing fails closed; adjacent upload time cannot pair reports |
| S7-T05 | One-side correction reuses exact counterpart only with validity confirmation; original input remains immutable; no extra player ScanID for aggregate/semantic duplicates |
| S7-T06 | Failed/missing second upload leaves last complete eligible output with honest age/pending state; first-ever pair shows waiting; stale endpoint config cannot leave old final labelled current |
| S7-T07 | B0/no-fight/overall/config-only paths have explicit compatible rules; no fabricated aggregate or fight-sum overall; authorized EndScanID 14 yields 14−10 without extra correction command |
| S7-T08 | Complete publication and export intent commit atomically; kill before/after commit cannot lose or duplicate eligible work |
| S7-T09 | New complete B/C arrive during export A: A finishes, latest C follows; B inputs/publication persist although its pending export was coalesced |
| S7-T10 | New-source, all-KVK and scan-data automatic/manual callers across processes cannot perform conflicting writes; pacing, fairness and SQL/provider lock boundaries are verified |
| S7-T11 | Restart/worker loss/late completion preserve pinned generation and durable queue; uncertain grant/pointer outcome blocks unsafe advancement and survives restart |
| S7-T12 | Admin export-only queues without import/recalculation; repeated request is idempotent; unauthorized user rejected; existing running/confirmed status is explicit |
| S7-T13 | Damaged confirmed output rebuild is separately explicit and audited; does not counterfeit import/publication history or bypass uncertainty reconciliation |
| S7-T14 | Rollover fences old-season writers, resets stale tabs safely, reuses eligible pool and preserves input/publication/receipt history; current/quarantined uncertain files cannot be silently reused |
| S7-T15 | Capacity/receipt exhaustion leaves current output intact; no evidence truncation; no assumption that initial pool size is a lifetime guarantee |
| S7-T16 | Full consumer matrix includes caches, scheduled/indirect readers and live stale views; daily SCANORDER/claim ownership and authoritative aggregate precision remain unchanged |

All cases above are planned coverage only. Existing S6 measurements are retained at
their exact tested revisions; no new runtime test pass is asserted by this amendment.

## S7 contract traceability — planning delivered, tests not executed

S7 documentation/read-only approval is recorded. See the
[exact S7-T01–T16 test allocation](integration_implementation_manifests.md#8-test-plan-with-actual-outcomes)
and [complete contract](integration_contract_and_consumer_matrix.md). Existing T01–T70
results remain accepted at their tested revisions. Public behavior amendments are:

- T36: incomplete overall remains privately inspectable; public overall waits for its
  separate matched overall report or labels a previously complete output as previous.
- T40: final aggregate alone cannot advance ordinary public selection; stream acceptance
  remains independent, paired public eligibility is separate. No generic final-unavailable
  substitute bypasses normal matched combat publication.
- T49/T51: candidate association is an explicit sealed update, not whichever two selected
  stream revisions happen to be latest; public CAS prevents stale builders.
- T58: never-started stale pending export is coalesced; already running A finishes before
  latest complete pending C. Destination/epoch fencing prevents late older overwrite.
- T66: a fixed new-source season disables to unavailable/labelled previous output, never
  changes source to legacy. Historical legacy seasons retain their own choice.
- T68–T70: matched counterparts gate public selection while exact 11−10, 12−10, 13−10
  and authorized 14−10 remain unchanged. Counterpart validity can be confirmed in the
  normal endpoint/config action; no second player correction command is introduced.

These are future implementation assertions, not fresh passes or predecessor reapproval.
