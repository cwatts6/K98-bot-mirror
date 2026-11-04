# P01.2a closeout and carried obligations

Accepted by Chris Watts on 4 November 2026 after Report 73 validation. This closes
the delivered P01.2a reporting/evidence correction, not the whole reliability
programme or its outstanding business incidents. Tracker evidence: E66-E69.

Next: [P01.2b handover and scope](Startup%20Import%20Export%20Reliability%20-%20P01.2b%20Handover%20and%20Scope%20-%202026-11-04.md).
The [agreed scope](../Startup%20Import%20Export%20Reliability%20-%20Scope%20-%202026-11-02.md)
and [tracker](../Startup%20Import%20Export%20Reliability%20-%20Tracker%20-%202026-11-02.md)
remain authoritative for requirements and progress. Earlier readiness/acceptance
holds are historical; they are not instructions to repeat accepted work.

## Delivered sequence

| Delivery | Repository evidence | Outcome and limit |
| --- | --- | --- |
| Initial evidence bundle | Mirror #482 / private #722; `07bc9d6ebd5964f9bf660822f03a932a2472d966` | Implemented passive combined reporting, outcome/milestone/publication contract. Report 70 exposed shared-deadline suppression; initial deployment did not close acceptance. |
| Diagnostic preservation and combined failure correction | Mirror #483 / private #723; `b31f022cb1338386a6711a596270c1c15f399bb7` | Preserved diagnostics independently of incident scanning and qualified long-running ownership. Report 71 retained evidence but revealed incorrect unknown startup actors. |
| Evidence-contract correction | Mirror #484 / private #724; `1f54cbb325ce5cbaf18d7495dc58005c66d6bf91` | Known startup actor/origin, malformed verification, producer-event loss, unknown stages, counter/eviction provenance and actual-reader compatibility addressed together. Report 72 still exposed bounded projection/progress gaps; acceptance remained open. |
| Bounded collection with recoverable progress | [Mirror #485](https://github.com/cwatts6/K98-bot-mirror/pull/485) / [private #725](https://github.com/cwatts6/k98-bot/pull/725); `67c4e12a8ecf0c25280770860480ac65a6826602` | All private CI passed; exact-head reviews and separate Changes scans completed; comments dispositioned/resolved, including late mirror naming feedback. User deployed and Report 73 demonstrates the corrected contract. |

Final installed updater manifest SHA256:
`b7dd6757ea4405ff7e89b5f5290d4d046bf410688b4e06536d994ed9c55b81a7`.
The operator's final explicit Git executable check confirms the private target,
and updater status reports no active update. The deployment receipt preserves
degraded import/export freshness; it does not certify provider delivery.
P03a.1 and P01.1 remain accepted. P03a.2 source/startup acceptance remains separate
from its outstanding whole-flow functional acceptance.

## Production acceptance evidence

The hashed validation receipt (private evidence: `.codex_artifacts/startup-import-export-review-20261102/p012a-recoverable-qualification-20261104/report73-validation.json`)
identifies the exact ZIP, ordinary report, updater transcript and runtime log inputs.
It is passive supplied-file validation, not a live SQL/provider query.

- Report 73 ZIP: CRC and all five component byte counts/SHA256 values match.
- Incident collection retains 850 of 17,747 incidents through cutoff
  `2026-11-04 16:38:18.781000`. It reports `incident_collection_time_bound`, 16,897
  omitted incidents, 85 reads and 28.298 seconds of read time. The last retained
  incident equals the continuation cursor; aggregate counts equal 850.
- Ordinary part 2 adds 100 unique incidents at that same cutoff, with no overlap:
  950 supplied incident rows in total. Part 2 is the expected first ordinary
  continuation after a nonempty ZIP. More parts remain. These artifacts are
  consistent with the reviewed cursor contract; they cannot independently prove
  no intervening database rows or completeness of the entire census.
- All eight startup rows/references survive both formats. Current startup
  boundaries identify `actor=system`, including parent and represented child work.
- ProcConfig is pending in the independently frozen ZIP diagnostics, then verified
  settled/completed-after-deadline at `16:38:22.676672+00:00` in the later report.
  The logs record commit acknowledgement and task completion. These snapshots
  intentionally do not pretend to be one transactional observation.
- The ZIP exports all 512 retained operation roots, not every historical operation.
  Rolling detail, child omissions, capacity eviction and provenance remain explicit.
  No first-failure-bearing operation exists in this sample: first-failure retention
  relies on controlled regression evidence, not a newly induced production failure.
- Monitor is fresh in the ZIP; the later completed result is 106.619 seconds old
  while a current cycle is progressing, last progress about 0.047 seconds earlier.
  The previous cycle completed in 73.453 seconds with 29 waiting checks and zero
  failed checks in the log. Detail trimming is declared partial, not hidden failure.
- Supplied log interval `16:27:19.081` to `16:40:38.154` contains no ERROR lines,
  traceback or heartbeat-block warning. This bounded interval does not prove the
  absence of future lag or identify the historical gateway-delay cause.

Normal follow-through: observe completion of the progressing monitor cycle at the
next ordinary check. No extra restart, import/export, repair or injected failure is
required. Ordinary admission preview is explicitly `source_invalid_or_bound`;
admission observations are retained in the ZIP. Empty event cache and
`waiting_for_events` remain truthful states, not evidence to manufacture.

## Qualification retained for unobserved branches

| Gate | Evidence |
| --- | --- |
| Final local correction | 113 focused passes; two real 125-second combined worker/monitor/deadline/cancellation cases pass, including repeated cancellation and competing admission. Operational-log guards pass. |
| Full suites | Mirror: 11,344 passed / 1,114 skipped / eight subtests; the two later startup-neighbour cases pass in the focused run. Private: 11,347 passed / 1,113 skipped / eight subtests. Private promotion script did not independently run the operational-log wrapper; do not relabel it. |
| Private CI | Linux: 11,180 passed / 1,280 skipped / eight subtests. Windows: 315 Python compatibility tests and seven native PowerShell 5.1 scripts pass; log guard passes. Gitleaks passes. Dependency warnings are retained, not failures or fixes in this slice. |
| Review challenge | 66 report/bundle tests rerun for late review points. Conservative compression overhead and unavailable-component descriptor semantics checked; naming suggestion resolved as non-blocking without claiming a source fix. |
| Security | Final mirror Changes scan `0275fbeb-7542-4558-9540-e299db7fcd5a` and private Changes scan `4beebfb6-79a0-4d10-996b-f41ba78e6189` sealed with zero findings; committed source hashes match. |
| Resource gates | 100 matched 18,000-incident pairs: candidate p50/p95/p99 1.995/2.641/2.809 seconds, extra RSS 28.17 MiB. Both variants share collector/redactor: this isolates assembly, not old/new native SQL. Five UI builds meet unchanged event-loop gates. Full-bound reconstruction/retention extra RSS 124.56 MiB meets 256-MiB gate. Failed pilots remain retained; limits were not relaxed. |
| Governance | Architecture, deferred-item, security routing, selector, inert smoke, registration and configured changed-file pre-commit checks pass. No SQL/config/dependency/command-registration delta. |

Diagnostic continuation/frozen-byte retry and combined cancellation were not naturally
exercised in Report 73. Their controlled qualification is retained; production
acceptance does not claim new live execution of those branches. Native SQL holder
and installed-profile qualification are not replaced by these results.

The final [recoverable report task pack](P01.2a%20Recoverable%20Report%20Correction%20-%202026-11-04.md)
retains Q01-Q12/R1-R6, precise budgets, source boundaries and failed experiments.
The [evidence-contract correction](P01.2a%20Evidence%20Contract%20Correction%20-%202026-11-04.md)
and [first correction](P01.2a%20Report%20Acceptance%20Correction%20-%202026-11-03.md)
retain their own earlier evidence. Final private artifact root:
`C:/discord_file_downloader/.codex_artifacts/startup-import-export-review-20261102/p012a-recoverable-qualification-20261104/`.
Keep `report73-validation.json`, `both-pr-closeout.json`, `private-ci-final.json`,
`promotion-equivalence.json`, `final-source-hashes.json`, `final-handoff.json`,
the full/focused/combined logs and cost/bounds samples. Local preservation is not
proof of remote backup; carry these paths and hashes into the next chat.

## Learnings that later packets must apply

1. Qualify complete entrypoint-to-producer-to-storage-to-download flows using realistic
   populations. A helper passing or JSON parsing is insufficient: eight valid startup
   rows must not disappear when a default depth/node/byte limit is reached.
2. Bound memory, CPU, archive bytes and work admission, while preserving useful progress.
   The 30-second report budget limits new collection work; it does not cancel an
   entered SQL read, settle a worker or shorten business operations lasting minutes.
3. Freeze independent diagnostics before potentially slow incident collection. Keep
   accepted bytes/count/hash/cursor atomic and retain a contiguous prefix. No skip,
   rescan or invented completeness when time, size or a later row fails.
4. Distinguish observer deadline/cancellation, physical settlement, child booleans,
   parent return and independently verified feature effect. Retain first entry,
   deadline/cancellation, first failure and terminal milestones beyond rolling detail.
5. Known actors must remain known through worker handoffs; genuine unknown issuer,
   process or SQL-holder fields must remain explicit. Requester identity is not proof
   of the conflicting physical holder. Startup attribution does not close all actors.
6. Keep optional diagnostics non-authoritative, bounded, redacted and non-interfering.
   Count malformed events, unknown stages, drops and publication failures; distinguish
   current counters from restored historical totals and publication watermarks.
7. Failed/uncertain delivery must preserve the frozen artifact and successor identity
   within the authorized actor/guild/channel/scope, fixed expiry and bounded retention.
   A diagnostic retry is never permission to replay the business operation.
8. Preserve exact historical readers and updater transitions. Test real old readers,
   corrupt/mixed restoration and downgrade/re-upgrade; assert source pins and complete
   transition inventory. Never weaken custody or patch a gate as arbitrary text.
9. Test combined failures with real held work (125 seconds), repeated cancellation,
   unavailable monitors and delivery failure. Check ownership through settlement and
   cancellation before final send, not just incomplete/count labels.
10. Measure shared callers and unchanged resource gates. Use each checkout's own Python.
    Preserve failed/interrupted runs; distinguish parser, fixture, native-host and
    installed evidence. CI step logs and final check conclusions are separate; late
    reviews must be checked even after a mirror merge.
11. Operational commands must use reviewed executable paths: the final transcript's
    `git` PATH failure was resolved by `C:/Program Files/Git/cmd/git.exe`. Record this
    in future operator plans rather than relying on shell PATH after updater work.

## Remaining obligations and when incidents resolve

| Obligation | Owner / next decision | Evidence required before closure |
| --- | --- | --- |
| Early launcher/issuer failure before normal journal; offline collection | P01.2b, next | Exact installed binding inventory; bounded privileged capture and safe projection; one launch; early-failure and real Windows qualification. |
| Passive health, uploads, calendar and read-worker adoption | P01.3-P01.6 | Their own D01-D06/Q01-Q12 adoption and relevant fault/cancellation/ownership regressions; no inherited blanket acceptance. |
| F09 / 51421 contention and observer interference; 51400 holder uncertainty, timing and installed factories | P02 | Actual holder/resource/lifetime and both acquisition orders, observer/producer workload, cleanup and installed binding evidence. No blanket retry or timestamp-based holder attribution. |
| Five historically linked configuration/pipeline records and remaining-stage work | P02 prevention plus P03 recovery/continuation | Fresh exact IDs/state/versions, original intent/captures/receipts, no live owner, durable effect or non-entry proof, supported successor/CAS/lost-reply behavior; then authorized recovery and truthful projections. |
| F28 cancelled-before-SQL sibling still open | Remaining P03 with P04 projection convergence | Match original cancellation proof to sibling import and all views; fix missing convergence rather than manual blanket clearing. |
| Current open-record census | Delivery owner at next incident/recovery decision and before affected deployment | Fresh bounded saved-state observation of the exact records. Report 73 supplies 950 of 17,747 rows and does not prove the old six are unchanged or that no new incident exists. |
| Grouping, recurrence/history, retention and genuine escalation | P04 with P03 dependencies | Ordinary waits/completed/cancelled states converge automatically; uncertain effects remain protected; immutable first failure and recovery history survive restart/capacity. |
| Natural gateway lag and installed SQL/maintenance cost | P02 measurement; P05 combined confirmation | Correlated timings, worker/holder evidence and observer overlap. A clean short log interval is not root-cause closure. |
| P03a.2 whole-flow and import/export/provider acceptance; natural empty-event transition | Owning recovery/domain packets and P05 reconciliation | Appropriate natural functional evidence without replaying already accepted actions; degraded startup health does not certify provider delivery. |
| Mandatory repository-wide confirmation, A01-A14/D01-D06 and P0/P1 reconciliation | P05 after relevant P01-P04 deliveries | Refreshed Bot/SQL entrypoint-to-sink and installed-path census, independent final sweep, cross-package combined failures, current implementation/test/deployment matrix and every residual owner. |

The normal sequence remains remaining P01 -> P02 -> remaining P03 -> P04 -> P05,
then applicable P0 reconciliation and P1 Ark. This is not a rule to leave an unsafe
incident untouched until the end. A supported, evidence-backed recovery may be
performed earlier when needed; unsupported continuation needs its reviewed fix.
If retained work blocks a future protected deployment, design/qualify the exact
repair before bot stop. Zero open incidents is not a deployment prerequisite.

Report 68 historically identified five records for one pipeline plus F28 (and a
separate overview). Exact private IDs remain in
`p03a2-report68-failure-analysis.json`; they are not current authority. P03a.1's old
export recovery is complete and must not be repeated. P01.2b improves evidence; it
does not itself repair F09, resume the pipeline or clear these incidents.

## Documentation delivery and authorization

This closeout updates the existing local programme documents and adds the next
handover. Existing uncommitted work is preserved. It changes no runtime source,
SQL, startup policy, permissions or deployment scripts and performs no production
action. Documentation validators, introduced-link checks and whitespace/hygiene
checks qualify this change; runtime pytest/smoke/registration are skipped because
only prose changes. Security routing: documented skip for the documentation delta;
future executable P01.2b changes require their own exact Changes review, Deep off.

The user authorizes creating and starting the P01.2b chat. Its first deliverable is
the concrete review/design and implementation/qualification packet required by
AGENTS.md. This is not blanket authorization for runtime implementation, production
repair, another deployment or a repeat of accepted work.
