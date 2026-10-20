# P0 health-probe contention and held-read cancellation

## Scope and diagnosis

The deployed publication progress worker can return an authenticated pre-dispatch
busy response. A health probe previously claimed its configuration preparation
before asking that worker to open a stream. Propagating busy marked the preparation
uncertain, retained its reservations, and left no stream to reconcile automatically.
The ordinary cancellation preview then rejected the request: its validator expected
a bare `read_configuration` document, whereas `LegacySnapshotDAL.request` stores
and hashes a consumer/season/storage-owner envelope containing that document.

This focused release covers prevention and the existing guided cancellation path.
It does not unlock a reservation because a process timed out or a provider was busy.
All remaining P0-F01 through P0-F05 work in `P0 Final Recovery Acceptance.md`
remains mandatory.

## Implementation and boundaries

- A local scheduling lock excludes Bot configuration collection and owned authority
  proofs. Health observations defer before creating any SQL ticket if the lock is
  busy. Collection keeps the lock until closure and settlement. The authority's
  own observational worker does not acquire the Bot scheduling lock.
- A probe already admitted by SQL waits on an authenticated pre-dispatch busy
  response using its original stream ID and request. Unknown, malformed or lost
  replies still preserve uncertain ownership. Existing runtime lifetime/drain
  retains the original call; an observation timeout does not cancel that work.
- Guided cancellation accepts the real stored envelope only when its consumer,
  null season, storage owner and exact inner read UUID agree. Bare historical
  requests remain compatible. Additional intent, foreign identities, any request
  or event, conflicting streams and changed reservations remain ineligible.
- The existing authority transaction fences the old claim and releases only its
  exact reservations. Private and SQL receipts are read back; a lost reply is
  reconciled without repeating the cancellation. The admin decision remains
  explicit. Cancellation proves no successful configuration read or publication.

No SQL migration, credentials, permissions, dependency or activation change is
required. `ExportPreparation`, resource membership and execution ledger definitions
were checked against the authoritative SQL repository. Changes remain in service
and existing authority/DAL layers; no SQL is added to Discord interactions.

## Operator verification

1. Install the matching updater package on MINI_AMD, run the normal updater and
   request one Discord graceful restart only when prompted.
2. Open **Configuration read recovery — held** and **Recheck**. For an unchanged
   unstarted read, **Cancel unstarted read** should now appear. Review that it never
   opened an execution stream and has no provider requests, then confirm once.
   If the evidence differs, retain the hold and export its current report.
3. Recheck until the incident is **resolved** and the explanation says it was
   cancelled before execution. Reopening must show the verified saved decision.
   This step closes only that read, not an export or an unknown SQL import.
4. Run `/ops dl_bot_status`, then request one **Check published output** from the
   retained publication. During the owned check, health may say deferred/busy;
   it must not create another held configuration read or queue blocker.
5. Use the saved check's progress/recheck controls rather than starting duplicates.
   A fresh confirmed publication check is separate from the green historical
   delivery card. An absent/damaged result requires its own reviewed action.
6. Download the complete report after completion. Check current monitoring,
   publication outcome, zero newly stranded probe tickets, and the cancellation
   receipt. Successful deployment alone does not certify import/export health.

## Validation and security

Tests cover the actual DAL-written request shape, identity/intent rejection,
admin confirmation and receipt verification, lost acknowledgement, real temporary
SQL fencing/rollback/races, both proof/read ordering windows, authenticated busy
retry and unknown-reply retention. Protected updater compatibility requires the
complete three-file runtime transition and rejects partial/unreviewed bundles.

Security routing: separate mirror and private **Changes** scans against exact
base/head revisions; Deep scan off. SQL schema is unchanged. Record final scan,
test, CI and protected rehearsal results in the release package before handoff.
No unrelated refactor or optimisation is included.
