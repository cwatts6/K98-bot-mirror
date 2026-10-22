# P0 fresh report and cache recovery

## Scope and evidence

This focused P0-F03/F05 delivery follows verified cancellation of a failed
cache-only player report. It provides a separate admin decision to calculate a
fresh report from existing imported scans and current SQL settings, followed by a
separately approved local cache rebuild. It does not replay an import or publish
to Sheets. An explicit keep-prior decision makes no freshness claim.

The latest production report showed the original failed report and configuration
continuation resolved. The retained cache still used an older source scan. A new
cache write timestamp alone is not evidence of a newer scan or report.

The publication tail has successful results through request 162; request 163 has
dispatch intent without a saved terminal result. A subsequent bounded authority
diagnostic searched 20 files without read errors and found no matching exception.
Current disk capacity does not establish historical capacity or the failure cause.
This patch adds sanitized background proof error reporting through the existing
authority diagnostic. It does not classify the output as damaged, release an
uncertain claim, or claim the publication failure is fixed.

## Implementation and boundaries

- The latest closed original cache-only report is independently discoverable.
  Original attempt time, existing-scan input, and original/current registration
  comparison appear in a concise decision summary. Unrecorded SQL settings and
  original fault details remain explicitly unknown.
- Existing admin/guild/channel checks, evidence hashes, serialized operations,
  durable action identity and parent linkage bind approval. A lost dispatch or
  commit reply is reconciled without automatically rerunning the report.
- The report has a separate atomic SQL checkpoint and capture recovery. Recovery
  of cache-only and configuration-only captures preserves their original
  no-export intent, including direct queue-action refusal.
- Only verified report completion offers local cache refresh. The rebuild reads
  the existing SQL report without executing its producer, validates the snapshot,
  writes atomically under the normal cache lock, and verifies saved bytes. Its
  receipt records hash, row count, KVK, source time and verification time.
- Cache receipt acknowledgement loss is reconciled. Without a durable receipt a
  fresh admin approval can repeat the read-only rebuild; report SQL is not replayed.
- No SQL schema, dependency, activation flag or provider protocol change is needed.
  SQL names are checked against the authoritative reviewed installed-schema
  checkout; disposable tests use temporary tables on local K98DEV only.

## Guided verification after deployment

1. Run `/ops dl_bot_status`, then open the recovery centre. Find **Fresh player
   report and cache**. Review the original attempt and registration comparison.
   No incident is expected when there is no qualifying failed cache-only report.
2. Choose **Build fresh player report** only when a recalculation from currently
   imported scans/settings is wanted. Confirm once. **Keep prior report and
   cache** is a separate explicit decision without a freshness certificate.
3. Recheck the saved decision. If linked report recovery is required, open
   **Review fresh report result**, complete its offered capture checks, and wait
   for verified no-export completion. Do not run the report again.
4. Choose **Refresh local player cache** and confirm. Expect **report_and_cache_verified**
   with KVK, row count, source scan time and cache verification time. An old source
   scan time is valid when no newer scan was imported.
5. Download the complete report. Verify the continuation/action outcomes and cache
   receipt. Recheck again: no new report or spreadsheet job should be created.
   Failed validation retains the previous cache and leaves a guided action open.
6. A fresh publication check remains separately authorized and separately verified.
   A recorded export confirmation or green access probe is not a fresh publication
   proof. If it fails, retain the complete report and sanitized authority diagnostic.

## Validation and delivery gates

Use affected report/cache/configuration capture, production-policy, real admin
confirmation, stale approval, lost reply and restart tests, plus full pytest,
architecture/deferred/routing checks, lint, synthetic-config smoke, registration
and pytest log isolation. Rehearse the exact updater package on a disposable
protected Windows fixture. Security route: **Changes**, Deep off, separate final
mirror and private commit ranges; no routine Codebase scan.

Package instructions must identify the exact predecessor and target, installer
and upgrade hashes, compatibility verdict and protected rehearsal result.
The normal private-main updater and its prompted graceful restart remain the
deployment path. No production operation is part of local qualification.

## Required remainder

All unchecked items in [P0 Final Recovery Acceptance](P0%20Final%20Recovery%20Acceptance.md)
remain mandatory. In particular: fresh publication failure diagnosis and proof,
all-valid-copy loss and ownership conflict workflows, remaining pipeline admission
and predurable failure cases, rollover qualification, and the complete failure/
repair matrix and natural production acceptance. This release does not finish P0
and does not move any recovery gap to P1.
