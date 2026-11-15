# P02 D5b report execution packet — 2026-11-11

Execution update: V2 captures and rollback have passed independent host
adjudication. **D5b is complete within its approved isolated scope**; see the
[closeout](Startup%20Import%20Export%20Reliability%20-%20P02%20D5b%20Closeout%20-%202026-11-11.md).
The packet and first-failure history below remain preserved; do not rerun them.

The report-readiness receipt passed host-only adjudication. Maintenance remains
complete and its one targeted recovery retry is consumed. This packet prepares
the remaining report evidence under the existing native D5b approval; it does not
authorize an import, maintenance repeat, production change or permission change.
Full D5b acceptance requires the captured reports and independent comparison.

## Accepted readiness evidence

Receipt `d5b-report-readiness-result-ec3c99ca02344cc6a736ee8e5834330b.json`,
SHA-256 `4b096adf20f889c95b5908cd7b5f1d512c4fbd45992a96a00afbc8d055e661a6`,
used 4.0058705 seconds, 27 client commands and 130 metadata rows with no errors.
Work and observer connections were disposed and the exact original SQL session
was absent. Source database protection, ownership, permissions, six completed
maintenance records, backup demand and all 30 installed candidate images match
the successful maintenance continuation. Original FirstError 15247 is retained.

All 56 column lists match both retained reference and candidate captures; all
112 corresponding file hashes were verified. Eleven report procedure bodies
match the authoritative SQL repository after declaration/line-ending
normalization and the existing six local database bindings in GOV_NAMES.
No procedure body is installed or rewritten by this report packet.
The names helper and view are additionally pinned to their retained installed
source, independently matched to the current SQL repository.

The separate adjudication is beside the original receipt. The original receipt
was not rewritten. Remaining native allowance is **1508 seconds**; the original
**21-input allowance remains consumed**.

## Exact execution

Use the existing operator console's `$global:D5bReportSession`, instance
`67caa9aa-5bb2-466c-991d-26ab8e1a2fc6`. The script pins host 9SX2VF4, isolated
VM `2ac1b401-7076-4965-af71-de36ee0f9f9c`, four CPUs, fixed 8 GiB RAM, zero
adapters, guest MINI_AMD, exact Q volume, database id/date/files/settings,
existing Windows owner and source READ_ONLY/RESTRICTED_USER state.

1. Create one exclusive host intent and new host/guest evidence directories.
   Refuse prior intent or changed manifest/helper/receipt bytes. Recheck source
   protection, 13 report/helper/view definitions, 30 candidate images, full
   permission fingerprint, completed maintenance, nine summary checkpoints,
   source aggregates and absence of foreign copy sessions.
2. Capture the 42 detailed states and 14 exports before work. Also capture the
   alliance-sync state solely to prove restoration; this is not a 57th business
   test case. Names, aliases and alliance tables are already represented by the
   export captures.
3. Record SQL UTC/local clock bounds. Acquire the existing zero-wait exclusive
   report snapshot lock. Open one outer transaction on the disposable copy.
   Change only the nine completed summary test cursors from 1245 to 1244 inside
   that transaction. Require exactly nine affected rows.
4. Execute the unchanged `GOVERNOR_NAMES_PROC` and `SUMMARY_PROC` once each.
   Require transaction depth one and a committable transaction after each.
   Require all nine summary checkpoints to return to 1245. No UPDATE_ALL2,
   import-stage reset, maintenance worker, backup dispatch or producer replay is
   called. Record actual clock bounds; do not freeze or rewrite report clocks.
5. Capture the same 56 report results plus sync state, then explicitly roll back
   the outer transaction. Capture all 57 results again and compare restored
   metadata, procedure definitions, permissions, maintenance, backup demand,
   source protection and candidate images with prestate.
6. Dispose the work connection and verify absence of its exact session-id/login
   time using the separately validated observer. Dispose the observer. Only then
   transfer the bounded capture files to their new host directory and verify
   every file's size and SHA-256. Retain guest captures and all partial evidence.

Failure or cancellation stops dependent work. Cancel and join the actual reader
or command task; preserve an unjoined physical owner for review. Attempt only
owned transaction rollback. A missing rollback acknowledgement, missing output,
failed reserve, altered metadata or unverified connection closure is not a pass
and does not permit an automatic retry.

## Limits and evidence separation

The successful path uses **41 client commands**, including three streaming
capture batches, one report-work batch and connection-closure checks. The
48-command guard remains. Metadata queries retain three-second command timeout,
zero row-lock wait, at most 512 rows per command, 2048 total metadata rows and
1 MiB receipt. Native work/capture commands have a stricter 120-second timeout;
the guest deadline is 210 seconds, with owned host cancellation before the
300-second outer envelope. Transfer stops admitting files after 240 seconds.
All elapsed native time, including evidence transfer, is deducted conservatively
from 1508 seconds. No Bot timeout changes.

Full report rows use the existing Phase 1 report-artifact envelope, separately
from the small metadata receipt: at most **1,000,000 rows and 256 MiB per output**.
Both uncompressed and compressed byte counts are bounded. Three stages produce
171 unique gzip files; metadata records their counts and hashes. Capture streams
rows without loading whole tables into guest memory. Decimal38, bigint and binary
floating-point values are encoded as exact rational numbers; NULL, strings,
date-only values and timestamps retain their distinct representations. Duplicates
are preserved. No report content is printed to chat.

Host/guest C and Q reserves remain at least 8 GiB. Log use and version-store
samples retain the 70 percent and 512 MiB ceilings. Host memory reserve remains
the original pre-start gate, not an invented post-start 8 GiB requirement.
No original data, disk, settings, account, role, grant or failure receipt changes.

## Independent acceptance, after capture

Acceptance is host-only and consumes no new inputs or native allowance:

- Verify receipt, manifest and all 171 file hashes/counts. Compare before versus
  restored as exact multisets across every output, preserving duplicates.
- Reuse the retained independently captured 486842-row source history and
  latest-name evidence. Check the 415 latest-scan governors' endpoints and
  12/6/3-month windows against each actual run's clock interval. Ambiguous source
  rows on a clock cutoff stop acceptance; do not waive a difference as "time".
- Check all eight summary aggregates using exact arithmetic and halfway-away
  rounding, every combined-summary numeric cell, intermediate windows/latest
  tables and the nine summary checkpoints. Unaffected rows remain exact.
- Check all 14 exports, current display-name rules and historical aliases.
  Preserve the accepted unspecified equal-score ordinal policy only where
  demonstrated; do not introduce a blanket rank/name/numeric tolerance.
- Verify the original queued payload's exact saved bytes/digest and the already
  tested candidate conversion contract. Do not regenerate or overwrite it.
- Reconcile these results with the completed six real children and Q05 offline
  correction. D5c lifecycle/concurrency, D5e balanced costs and D6 production
  promotion remain separate; one report run cannot qualify them.

## Preparation and review

The initial unexecuted packet had a generated carriage return in its guest path.
Its exact source bytes are preserved under `.codex_artifacts/p025/`; no SQL/VM
operation used them. Initial Changes review
`3d5ac8a1-603c-44d5-8f27-01b63d4d1a10` found no security vulnerability but recorded
that correctness blocker. The corrected packet uses the exact rooted child
`Q:\D5b-20261111\reports-<runId>` and an AST regression check.

Actual Windows PowerShell 5.1 testing also exposed native-DateTime versus literal
Microsoft-JSON date escaping. The metadata comparator now normalizes DateTime
values to the exact pinned millisecond form without changing strings or other
fields; a one-millisecond change still refuses. SQL date-only capture formatting
has a separate regression check. These were local preparation failures, not
native attempts. Original evidence and native allowance are unchanged.

Focused tests exercise parsing, row/command budgets, metadata visibility, target
identity, conservative elapsed-time accounting, cancellation/disposal, exact
numeric/string/date capture, gzip custody, duplicate preservation and refusal to
overwrite evidence. They use fake commands and in-memory readers only.
The final corrected source hashes, test results and Changes-only review are
recorded separately in `d5b-reports-preparation-validation.json` before operator
handoff. No codebase/deep scan or production change is part of this packet.

## First native pre-work refusal and V2 continuation

The reviewed first packet stopped before capture or report execution. Receipt
`d5b-reports-result-04e894a50eb0493d821def3c0eb920cc.json`, SHA-256
`8bc578e8462733fabb501fadc9817af0b8b2b4fc17558dff3deecbc6aa7436db`,
records 18 commands, 40 metadata rows, empty captures, no workload clock/rollback
fields and verified work-session absence/observer disposal. Its six maintenance
rows, ownership and backup state exactly match the pinned manifest. Remaining
native time is now **1505 seconds**. No report workload allowance or new input
was consumed. The original script, manifest, intent and receipt remain intact.

Host-only Windows PowerShell 5.1 serialization reproduced the cause: a remoted
ArrayList also satisfies the custom-object test. The comparison therefore read
its Capacity/Count/SyncRoot wrapper properties instead of its six rows. Ordinary
local JSON fixtures did not exercise that transport representation. The separate
failure adjudication and reproduction output preserve this evidence.

Versioned `run_p02_d5b_reports_v2.ps1` moves collection enumeration before the
custom-object branch, after the existing dictionary/date branches. It retains
all exact scalar/date checks, rows, generations, claims and original errors.
The new manifest/intent/receipt identities bind the failed receipt and remaining
1505-second budget. All report operations, capture helper, limits and cleanup
remain unchanged; this is not a maintenance retry.

Actual full-manifest PS5.1 serializer roundtrip tests now cover native GUID and
DateTime ledger values, every pinned collection, all 57 column arrays and refusal
of missing/duplicate rows, changed generation/claim/timestamp and erased first
error. They pass. Reusing the unchanged capture helper in the same and a second
owned local runspace also passes. V2 independent/Changes review and exact hashes
are recorded in `d5b-reports-v2-preparation-validation.json` before handoff.
