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
5. A new refused ProcConfig read uses **Configuration import read not started**:
   **Read & publish current config** or **Keep prior configuration**, as already
   delivered by PRs 389/646. Its blocking writer has its own recovery requirements.

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

## Remaining required P0b work

The failed export with retained execution streams needs a separate complete
private-journal verification and guided repair. Grouped historical retirement
must review identical shared configuration once, present each input/date and
allow member selection, persist individual approvals, and verify each member
independently. Unknown writes, replacement publication, unresolved producer and
rollover workflows remain mandatory in the existing P0b scope. They are not
deferred optimisations and this slice does not mark P0b complete.
