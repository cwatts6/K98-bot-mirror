# P1 MGE A1b: local implementation and validation

Status: implementation in progress under explicit operator approval of the revised
scope. Publication, merge, updater installation, deployment, restart and live
SQL/provider operations are separate and have not been performed.

## Custody

- Managed implementation worktree: `p1-mge-a1b/discord_file_downloader`.
- Mirror source base: `8ce3234c54fccebea018ac95f49a2d5076db68c5`.
- Merged handover: mirror PR 455 / `8db65da6`, private PR 703 / `07d5dd17`.
- Preserved design branch: `codex/p1-mge-a1b-design`, `a025adb7`.
- Local implementation branch: `codex/p1-mge-a1b-b1`. The design-only delta was
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
