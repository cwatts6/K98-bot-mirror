# P0 publication detail and card context diagnostics

## Approved scope

The operator approved continued P0 implementation and offered to repeat a manual
published-output check when measurement is ready. This candidate addresses two
observability defects. It does not close the full P0 acceptance matrix or authorize
an agent to merge, deploy, restart, change source routing, or repeat business work.

1. Publication readback currently combines stream admission, SQL/private request
   journals, request pacing, provider-child execution and closure. Record bounded
   aggregate counts and monotonic durations for those distinct steps.
2. A card with no season-wide `overall` period currently resolves the display fight
   and then overwrites any routing failure with `overall_missing`. Resolve the
   card's explicit period without display fallback, preserve routing diagnoses,
   and explain a missing overall period in readable language.

## Architecture and contracts

`services/export_publication_metrics.py` owns a context-local, fixed-name timing
collector. It is active only inside the synchronous publication probe. The local
authority broker stays on that thread. Request authority and budget code record
diagnostics without depending on the reconciliation service or changing request,
event, retry, pacing, ownership, closure or evidence semantics. Timing failure must
not turn a successful operation into uncertain work or repeat a failed request.
The existing five phase records remain intact.

Each probe emits at most sixteen detail records. They contain fixed step names,
counts, failures and durations only: no request IDs, targets, payloads, credentials
or exception text. The existing protected rotating timing log owns storage.
`request_budget` contains `budget_sql` and `budget_wait`; probe observation contains
request timings. These intervals overlap and must not be summed together.
`provider_child` includes IPC and child-side processing; it is not pure HTTP time.
The collector accepts an explicit UTC interval of at most 24 hours, retains strict
path/identity/ACL checks, and returns only complete allowlisted records.

The card DAL still checks `KVK.SourcePeriod` by its unique source/season/key and
kind. `resolve_season_read` defaults to existing display behavior for all other
callers; cards explicitly disable that fallback. Missing/disabled routing and
unsupported capabilities remain authoritative. Main player totals, targets and
KVK rank are unchanged. This diagnostic does not create or select a period, route
to legacy data, or claim that cached player values are current imports.

Schema alignment was checked against `KVK.SourcePeriod`, `KVK.SourceRouting` and
`KVK.SeasonSource` in the authoritative SQL repository. There are no query, schema,
procedure, permission, dependency or runtime-flag additions. No SQL deployment is
required. The live reason why KVK16 changed source/context since an earlier manual
check remains unverified; the footer is not sufficient evidence of that change.

## Verification and deployment boundary

Regression coverage includes context isolation, diagnostic failures, context-manager
exception/suppression behavior, one-time dispatch under lost acknowledgements,
local broker propagation, unchanged proof closure/sealing, measured quota waits,
redacted collector parsing and native custody checks. Card tests cover missing
overall plus missing/disabled/unsupported routing, no display-fight result queries,
unchanged player totals and existing source-selection revalidation.

The exact four-member protected runtime transition is `publication_detail_v1`.
Prior transition hashes remain immutable. An updater package must bind the
currently installed revision-2 tool manifest as its predecessor and pass the
protected upgrade rehearsal. Runtime checks and final validation receipts are
retained with the package; this document alone is not a readiness certificate.

Security routing: Changes review required for the exact final mirror and private
diffs, Deep off, covering diagnostics, data access and protected deployment. The
previous release's scan does not cover this candidate. No repository-wide audit
is requested. Review and promotion use the K98 PR and promotion checklists.

## Acceptance after operator deployment

1. Verify the exact deployed source and normal startup/cache receipt. Retain the
   already successful KVK16 card and existing source scan time as separate evidence.
2. Repeat `/kvk stats` once. Record the footer and whether the ordinary values
   remain correct. Use read-only source evidence before considering any source or
   overall-period configuration change.
3. For one operator-approved manual published-output check, record start/end UTC
   and the terminal result. Collect that bounded interval with
   `Read-K98PublicationTiming.ps1 -StartUtc <start> -EndUtc <end>` on the bot host.
   Match one complete five-phase sequence and its detail records. Multiple checks,
   missing rotations or partial records cannot establish a single-run comparison.
4. Compare the same publication/workload and request counts. Attribute quota waits,
   request journals, admission, closure and provider-child time separately. The
   saved 851.176-second successful check remains valid. A lower connection count
   in deterministic replay tests is not a measured production speedup.

## Remaining P0 scope

`P0 Final Recovery Acceptance.md` remains authoritative. F01 still needs observed
timing attribution and remaining failure-during-repair acceptance. F02 retains
all-copy evidence loss and configuration/ownership conflict workflows. F03 retains
historical partial producers and remaining durable pipeline stages. F04 retains
integrated rollover qualification. F05 requires the complete failure-family matrix,
final package and distinct natural production acceptance. None moves to P1.

The supplied post-deployment report has no open recovery incidents, and the
operator's ordinary KVK16 stats check succeeds. Those are completed milestones,
not evidence that every P0 failure family is supported. Tracked-view startup
deadline handling remains the separately scoped P1 item.
