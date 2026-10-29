# P0b retained-output decision summary

## Scope and result

Captured imports, player-stat reports, configuration publications and all-KVK output
use a five-field decision summary before confirmation. It identifies the original
creation time, recorded procedure/input, current diagnosis, configuration comparison
and queue/skip effect. Missing historical identity remains explicitly unknown.
Full settings and destination links remain available as optional technical details.

An unqueued capture is not by itself evidence of a failed import. A producer may
complete SQL and save output without requesting export. The review does not infer
a fault or certify spreadsheet delivery from a retained snapshot.

The same bounded identity and configuration fingerprints are retained in the
existing failure-context field and downloadable reports. No raw configuration,
private paths, arbitrary producer text or destination identifiers are added there.

## Architecture and proof

- Reuse `capture_recovery_context`, the adapter's existing fresh inspection and the
  existing `RecoverySummaryView`/confirmation service. No SQL in views, new command,
  schema migration, authority policy or automatic repair is introduced.
- SQL source checked: `ExportPreparation.CreatedUTC/RequestJson/GenerationJson`
  and `StatsImportExecution.CompletedFileName` in the authoritative SQL repository.
- Services keep authorization, current revision/token, pending-action and allowed
  action checks. Opening a summary or technical details performs no repair.
- Confirmation still requires the admin decision, then current evidence and normal
  per-action verification. SQL output is not replayed. Original bytes remain retained.
- No new shared helper or unrelated refactor is required. The existing capture
  review validation is reused by both presentations.

## Acceptance

1. An eligible capture opens one short summary with a correct action-neutral title.
2. Admin can confirm from the summary without paging through full configuration.
3. Full technical details remain accessible and complete.
4. Wrong admin/guild/channel, stale token/revision, a resolved incident or removed
   action cannot gain confirmation or repair authority.
5. Queue and skip actions retain independent durable verification, duplicate-click
   protection and restart/lost-acknowledgement recovery.
6. Incident/complete reports contain the original time, recorded procedure/input,
   configuration comparison and explicit unknown-fault qualification.

Validation includes unit negative cases and actual guided buttons against disposable
SQL for stats, player report, configuration publication and all-KVK captures; report
identity assertions, retained-byte checks, permissions, duplicate confirmation and
restarted verification are included. Changes-only security review, Deep off, is the
required gate for the exact final Bot diff. No SQL repository diff is introduced.

## Remaining mandatory P0b delivery

These are required recovery work, not deferred optimisations. A zero incident count
alone is not full P0b acceptance.

| Priority / focused increment | Required acceptance |
| --- | --- |
| P0b-1: routine producer capture disposition | Distinguish a cache/config refresh with no requested export from an interrupted requested export using durable original intent. Prevent recurring routine backlog without silently discarding wanted output. Existing captures remain guided until their disposition is evidenced. |
| P0b-2: monitor contention and root diagnostics | Expected active execution can wait/retry without false healthy status or repeated failure alerts. Reports retain the attributable failure and progress, and real outages still notify. Startup's protected-path verification warning has an explicit diagnosed outcome. |
| P0b-3: exhausted admission | Detect a request that never obtained admission without relying on the next business failure; retain original inputs/configuration, offer a verified retry/cancel decision, survive restart and prevent duplicate execution. |
| P0b-4: genuine configuration membership conflict | Compare original registration, installed registration and exact owned resources; guide admin through the discrepancy; execute only a verified repair/continuation with independent readback. Missing ownership evidence never becomes an override. |
| P0b-5: still-needed/historical and unknown-write outputs | Preserve uncertain originals; guide review of the exact input/configuration and external outcome, perform only an authorized replacement/publication, prove linkage and delivery, and verify exact release. Historical retirement must continue to preserve unknown SQL outcomes. |
| P0b-6: producer and rollover completion | Cover each remaining producer/rollover interruption with discoverable incidents, original-work context, guided decisions, durable action receipts and restart verification; include changed-configuration and missing-evidence paths. |
| Final acceptance | Every supported failure mode has an explicit recoverable or evidence-required path, proactive notification and report coverage. Production checks distinguish SQL completion, queue admission, provider delivery and updater readiness. No unresolved workflow is declared complete merely because its current incident was retired. |

## Operator verification

Open an eligible captured output in the recovery centre. Choose **Queue verified
capture** only if that original output is still required, or **Keep SQL; skip this
export** when no spreadsheet update is needed. Read the short decision, optionally
inspect destination/settings details, then confirm. Recheck until verified and
download the complete report. Queue admission does not by itself prove delivery.

Routine startup capture prevention and the other required increments above remain
open; this presentation increment does not change their execution semantics.
