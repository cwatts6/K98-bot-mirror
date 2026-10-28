# P1 MGE A1b: local implementation and validation

Status: implementation in progress under explicit operator approval of the revised
scope. Publication, merge, updater installation, deployment, restart and live
SQL/provider operations are separate and have not been performed.

## Custody

- Managed implementation worktree: `p1-mge-a1b/discord_file_downloader`.
- Mirror source base: `8ce3234c54fccebea018ac95f49a2d5076db68c5`.
- Merged handover: mirror PR 455 / `8db65da6`, private PR 703 / `07d5dd17`.
- Preserved design branch: `codex/p1-mge-a1b-design`, `a025adb7`.
- Local slices: B1 `codex/p1-mge-a1b-b1` / `8e7a79b6`; B2 `codex/p1-mge-a1b-b2`. The design-only delta was
  carried from the merged handover without resetting the original checkout.
- Deployed runtime evidence remains private `87c1b393`; local changes are not deployed.

## Requirement and evidence map

| Requirement | Implementation / caller evidence | Current validation |
|---|---|---|
| Q1 qualified presentation | Strict MGE DAL metadata checks; event/row/join/lifecycle/identity preparation; public, leadership and awards delivery guards | Initial focused 74 passed; wider MGE 574 passed, two source-pin failures pending the final authenticated successor; final B1 qualification rerun 45 passed |
| O1 exact action outcome | Roster, targets, rules and mode changes; preserve partial/unknown | Pending |
| R1 reply-independent refresh | Both leadership UIs, signup/edit/withdraw/admin-add and rules/modes | Pending |
| C1 coalescing and semantic keys | Owned per-target refresh and reply-release gates | Pending |
| I1 lifecycle/identity ownership | Publish/unpublish primary transitions, refresh and journal reconciliation | Pending |
| L1 drain/recovery | Private/background admission, scheduler, finite startup sweep and progress | Pending |
| E1 measurement/release evidence | Frozen baseline/candidate harness, final regression/security/updater qualification | Pending |

No caller inherits acceptance from helper tests alone. This table will be completed
with exact local commits and final test results before handoff. Runtime/operator
acceptance and the carried R01-R18, WS1-WS6 and P0 boundaries remain unchanged.

## Validation environment

Windows Python 3.11.9 from the existing repository `.venv`; imports resolve from the
managed worktree. Initial restricted test startup could not create worktree-local
test directories. That run was stopped and is not counted. The permitted offline
rerun passed 74 tests in 4.67 seconds. No SQL/provider call is validation evidence.

B1 wider MGE run: 574 passed and two failed in 23.21 seconds. Failures are the
current-source assertions in `test_mge_a1a_update_transition.py` and
`test_mge_update_transition.py`, because the runtime bytes intentionally changed.
They remain required unresolved gates until the final exact successor transition
and authenticated historical bridge are supplied; their original pins will not be
rewritten. Final B1 qualification tests: 45 passed in 1.97 seconds. Ruff, Black,
architecture (11 Python files), deferred and routing validators and whitespace
checks pass. This is an intermediate local slice, not release readiness.

Security routing: Changes review of immutable local Bot base/head, Deep off, after
the implementation settles. No SQL repository change or repository-wide audit is
proposed. Final scan and validation evidence are still pending.

## B2 implementation evidence

- Ordinary roster, target, rules and mode results carry explicit primary, secondary
  and audit evidence. Existing required audits are checked; this does not add a new
  audit policy to notes or waitlist-order writers. Unknown transaction settlement
  remains unknown. Confirmed earlier writes survive a later audit or target failure.
- Simplified leadership, legacy roster, signup/edit/withdraw, admin-add, rules and
  mode callbacks use the result adapter. Legacy roster snapshots remain available
  through Show Roster, and the existing legacy versus simplified DM policy remains.
- Refresh registration precedes the private reply. A reply-release gate prevents
  refresh IO before that attempt; failure releases owned work. Delivery observers
  report delivered, pending, refused, failed or not-requested per target. Ordinary
  results never promise delivery; explicit refresh observes for ten seconds without
  cancelling the operation. Newer requests during a pass cause a fresh pass.
- Publish/unpublish primary transitions share the event presentation owner with
  refresh, including state change, Discord send/delete and identity settlement.
  Recursive refresh and notifications run after releasing that owner. Conditional
  ID writes compare status, rule mode, publish version, exact SQL revision and IDs.
  SQL datetime2(7) precision is retained as an ISO revision token; Python's
  microsecond datetime is not used as the exact comparison value.
- The recovery inventory uses EventId high-water/keyset pages of fifty and at most
  two event tasks. Startup covers persisted identities including completed events
  outside the calendar window; periodic sweeps cover noncompleted events. Known
  identities are edited only, without placement, creation or mentions. Failed pages
  retain their cursor; failed targets do not starve later events. Progress includes
  scanned, eligible, refreshed, held, failed, outstanding and cursor/high-water state.
- A journal acknowledgement can restore a missing SQL ID only with matching key,
  event, kind, destination, lifecycle/revision and previously absent identity.
  Legacy, uncertain, superseded or cleared bindings remain held, never replayed.
- Shutdown closes new private/background admission together. Already admitted
  private work may register refresh continuation; private work drains before board
  work, while delivery remains available. Ten-second drain observations report
  pending work without cancelling threads, primary transitions or receipts.

### Concrete regression coverage

| Contract | Tests |
|---|---|
| Qualified shape/empty/identity/payload | `test_mge_board_qualification.py`, `test_mge_dataset_validity.py` |
| Actual settled DAL and partial audit results | `test_mge_action_evidence.py` |
| Two actual rules callers: reply order and failed transport | `test_mge_action_evidence.py::test_real_rules_callers_register_before_reply_and_release_on_transport_failure` |
| Shared pass, dirty follow-up, timeout/cancellation, target separation, refused target, drain | `test_mge_refresh_ownership.py` |
| Publish/unpublish versus refresh in both orderings; exact conditional ID predicate | `test_mge_publication_ownership.py` |
| Restart keyset/high-water, poison target, failed page, receipt binding, calendar failure | `test_mge_recovery.py`, `test_mge_board_delivery.py` |
| Existing permission/caller/lifecycle behavior | MGE view, command, lifecycle and service suites |
| Exact fixed release bundle and historical source bridges | `test_mge_a1b_update_transition.py`, `test_a1b_source_bridge.py` and predecessor suites |

### Release qualification boundaries

The local successor is `p1_mge_a1b_v1`: forty-one exact source/dependency members.
All fifty historical transition entries remain byte-equivalent as canonical JSON.
The count cap increases only to fifty-one and registry byte cap from 96 KiB to
100 KiB; the candidate registry is 100,849 bytes. This is one fixed bundle, not a
new wildcard admission rule. Every member/predecessor/required absence is pinned.
Candidate policy changes do not authorize their own installation: a separately
reviewed installed updater upgrade is still required before ordinary deployment.
No installed updater, production checkout, SQL schema or live data was changed.

B1 Changes scan `a8ccabd7-1036-4c8b-b61d-a663e0d0ad6f` completed on immutable
`8ce3234c..8e7a79b6`: all nine changed source files reviewed, no candidates/findings.
B2 security review, final whole-suite reconciliation and frozen benchmark results
remain pending in this checkpoint. This checkpoint is not publication readiness.
