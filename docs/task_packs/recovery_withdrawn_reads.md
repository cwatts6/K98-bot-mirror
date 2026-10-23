# Withdrawn reads and recovery navigation

## Scope and evidence

The October 18 deployment logs show a ProcConfig configuration-read refusal
behind a failed startup `SP_Stats_for_Upload` writer. Refusal happens before
collecting inputs or publishing configuration; the generic critical-failure
message obscured that distinction. Unexpected exceptions remain errors.

An older untyped configuration read, including the reported queue ticket 3311,
can remain visible after automatic withdrawal. The new **Close withdrawn read**
decision requires exact initial withdrawal (unavailable, version 2, fence 1),
canonical saved request identity, and no resource membership, held resource,
execution stream, SQL execution receipt, job or capture. It records a separate
decision without changing owner, fence, request or state, then reads it back.
Typed configuration-import reads retain their separate continuation workflow.
Unavailable original input files and publication intent are stated explicitly.

If the same withdrawn read also has a configuration-read incident, that incident
links to the queue closeout and independently verifies its final receipt. An
empty reservation set in this exact case is not reported as configuration drift.
Real reservation mismatches still require authority verification; their guided
diagnosis and original-registration recovery remain mandatory P0b work.

Tracked production example: incident
`bff228ee-0df1-4ad9-bdf3-47b7d65375e6`, checked 2026-10-18 19:02:02 UTC,
reports reservation membership differing from installed configuration. Its
classification must come from fresh scoped evidence, not the screenshot.
Acceptance requires either verified withdrawn-read closeout through the queue
link, or a guided comparison of original/current configuration and reservations,
an evidence-authorized repair, and independent readback. A remaining Recheck-only
incident does not satisfy completion of this P0b requirement.

Incident browsing uses ascending FirstSeenUTC and an IncidentID tie-breaker.
A scoped cursor remains usable after its incident resolves. Complete report
pagination remains independently bounded by its existing export snapshot.

## Operator verification

1. Open **Review queue blockers** and find ticket 3311. Recheck its evidence.
2. Use **Close withdrawn read**, review the explanation and confirm only if
   offered. The bot revalidates the exact state and records the closeout.
3. Recheck: the queue incident must resolve with no pending action. Download
   the complete report to retain the decision and missing-input explanation.
4. Open the incident list: first-seen timestamps must increase across pages.
5. A new refused ProcConfig publication read uses **Configuration import read not started**:
   **Read & publish current config** or **Keep prior configuration**, as already
   delivered by PRs 389/646. Its blocking writer has its own recovery requirements.
6. A refused schema-only dry-run has no saved publication. Use **Review queue
   blockers** to inspect blocking work, then rerun the dry-run when account access
   is available. Do not look for a publication-continuation incident for that dry-run.

This closes only the proven withdrawn read; it does not certify import/export
health, retire the current SQL writer, or infer success from a timeout.

## Engineering and acceptance

Services own decisions, DAL owns scoped locked compare-and-set, views retain the
existing admin/guild/channel confirmation boundary. SQL definitions validated
against the registered guided-recovery SQL source b663308a; no schema or grants
change. Required tests cover explicit confirmation, lost acknowledgement,
independent readback, typed/changed evidence refusal, chronological ties and
resolved/foreign cursors, and narrow logging classification.

Security routing: Changes review of the focused Bot diff, Deep off, separate
private promotion target. This touches SQL persistence and admin interactions.
Architecture/deferred/security routing validators, focused tests, formatting,
lint, smoke imports and command registration are required before handoff.

Review followup: the schema-only dry-run instruction now points to the existing
queue-blocker entry point and an explicit fresh dry-run. Twenty ProcConfig tests
passed, including distinct dry-run/publication instructions. A repeated full suite
is unnecessary for this text-only increment after the completed full promotion
suite. Incremental security scan skipped: inspected the message literals in
proc_config_import.py, their test assertions and this operator guide; no control
flow, permissions, data access, persistence or configuration behavior changes.
The preceding queue and promoted Changes reviews remain applicable.

## Remaining required P0b work

The failed export with retained execution streams needs a separate complete
private-journal verification and guided repair. Grouped historical retirement
must review identical shared configuration once, present each input/date and
allow member selection, persist individual approvals, and verify each member
independently. Unknown writes, replacement publication, unresolved producer and
rollover workflows remain mandatory in the existing P0b scope. They are not
deferred optimisations and this slice does not mark P0b complete.
