> **Archived 5 November 2026.** Completed or superseded delivery record; dated holds and pending statements below are historical. Current outcome: [P01.4 closeout](Startup%20Import%20Export%20Reliability%20-%20P01.4%20Closeout%20-%202026-11-05.md); remaining checks: [natural acceptance](../Startup%20Import%20Export%20Reliability%20-%20P01.4%20Natural%20Acceptance%20-%202026-11-05.md); next work: [P01.5 handover](Startup%20Import%20Export%20Reliability%20-%20P01.5%20Handover%20and%20Scope%20-%202026-11-05.md).

# P01.4 PR review and release preparation

**E92, 5 November 2026: publication, review fixes and merge are authorized; deployment remains for the operator.** This supersedes the publication hold in the dated E91 qualification receipt without changing its evidence or the complete original scope.

The complete candidate is being delivered through [mirror PR 488](https://github.com/cwatts6/K98-bot-mirror/pull/488) and a patch-based private production PR. SQL source is unchanged, so no SQL PR or migration is required. The [complete local qualification](Startup%20Import%20Export%20Reliability%20-%20P01.4%20Complete%20Local%20Qualification%20-%202026-11-05.md), [whole-solution design](Startup%20Import%20Export%20Reliability%20-%20P01.4%20Whole%20Solution%20Design%20-%202026-11-05.md) and [carry-forward manifest](Startup%20Import%20Export%20Reliability%20-%20P01.4%20Delivered%20Documentation%20Carry-forward%20-%202026-11-05.md) remain the scope and evidence sources.

## Review corrections

- The promotion hook required Black formatting in 11 Python files. Their ASTs are identical before/after; only the ten affected P01.4 updater postimage hashes changed. All 63 historical transition records remain unchanged. The 169 affected tests and all repository pre-commit hooks passed.
- GitHub review found stale SQL worker summaries after the final operation settled. The SQL adapter now publishes from the transport settlement hook, after its state, failure count and first error type update. The new idle-success and idle-failure regressions both failed before the correction and pass afterward; they require no subsequent upload or shutdown. All 157 related worker/lifecycle/archive/updater tests and pre-commit hooks passed. Only the corresponding new-family postimage pin changed.
- The exact mirror runtime head `df02daaa487c64038d7ea4f5f2123cbfb0eef7bd` received a completed Codex review with no remaining findings. The actionable thread was answered and resolved. Copilot could not complete its selected-tier review because of policy/plan restrictions; its summary is not treated as an independent completed approval.

The final private head, CI/review results, merge identities and package hashes are recorded in the release handoff after verification. Do not interpret this checkpoint as a completed merge or deployment receipt.

## Scope and optimisation disposition

All three original slices remain: truthful outcomes, one selected fallback admission with isolated optional CSV, and isolated optional SQL audit. Shared lifecycle, bounded diagnostics, cancellation/physical ownership, manual Location parity and exact updater admission are included. Both workers remain gated on the retained local cost/resource/drain evidence. No CSV deferral or alternative second solution was introduced.

Existing helper extraction and bounded/coalesced observation remove duplicated work without adding a retry spool or changing business persistence. No additional speculative optimisation is added during PR review. Optional observation loss, unavailable counts and arbitrary driver hangs retain their explicit semantics. P01.5/P01.6, P02–P05, F09 contention and incident recovery remain separately owned scope.

## Operator deployment and validation sequence

1. Use the final release package and pinned private-main target from the handoff; confirm the actual installed predecessor and updater manifest on MINI_AMD.
2. Upgrade the installed updater with the authenticated upgrade helper. The old reader must refuse the new exact 40-member transition; all historical transition authority remains unchanged.
3. Run the protected updater with `-PrepareOnly`, check the exact target, then run normally. Request `/ops graceful_restart` once only when prompted. No live pull, manual task start, dependency install or SQL migration is part of this release.
4. Retain source/tool identity, drain/startup/readiness receipts and one fresh complete/ordinary recovery report. Missing fresh import/export evidence may remain degraded; it is not permission to replay work.
5. Observe the next legitimate Honor, PreKVK, Weekly, automatic/manual Location, KVK and fallback operations as available. Keep authoritative business outcome distinct from optional SQL/CSV observations. Record unexercised paths as pending natural acceptance; do not manufacture production faults or an extra restart.

The complete design can be locally qualified and merged before these production acceptance observations exist. Programme delivery closure requires actual deployment and acceptance evidence. Retain uncertain stages and ownership on failure; rollback needs a separately reviewed private revert and exact reverse transition, not a manual downgrade.
