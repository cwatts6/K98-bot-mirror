# Codex Chat Starter - KVK Targets Quality Phase 2

## Copy/Paste Starter

Codex, take on the task defined in:

`docs/task_packs/Codex Task Pack - KVK Targets Quality Phase 2.md`

Phase 1 of KVK Target Publication State Separation is deployed, production-verified, cache rebuilt,
and working successfully. Preserve that deployed contract. Phase 2 is the approved
deferred-optimisation programme to make the targets subsystem as strong as practical without
changing player target rules or the command surface.

The programme has four approval-gated slices:

1. Phase 2A: immutable typed target rows and explicit cache serialization/compatibility.
2. Phase 2B: one service-owned retrieval and presentation-input path for numeric lookup, name
   lookup, modern card, and fallback embed.
3. Phase 2C: a target-domain cache repository with explicit outcomes and bounded, crash-recoverable
   cross-process single-flight coordination.
4. Phase 2D: compatibility-preserving shared fighting-lifecycle terminology with no state-value or
   threshold changes.

Non-negotiable constraints:

- Do not change target formulas, values, thresholds, populations, exemptions, or the fixed Official
  matchmaking snapshot.
- Do not change `DRAFT / ACTIVE / ENDED` fighting-state semantics, the Pass 4 boundary, broad KVK
  window, stats-alert timing, daily overview timing, history finalisation, or leadership-review
  finalisation.
- Do not change the `DRAFT / OFFICIAL / HISTORIC / UNKNOWN` publication rules or fail-closed
  Unverified behavior.
- Preserve publication version/signature identity, atomic writes, no downgrade, cross-KVK
  rejection, empty/mismatched refresh protection, and matching last-known-good behavior.
- Preserve `/kvk targets` arguments, decorators, permissions, channel, visibility, account
  selection, direct-ID/name behavior, image fallback, command count, and registration.
- Phase 2A includes the separately approved SQL companion that changes only
  `dbo.EXEMPT_FROM_STATS.GovernorID` from `float NOT NULL` to `bigint NOT NULL`. Keep it in a
  separate SQL Git target and PR with a guarded migration, matching snapshot, rollback, validation,
  and `Changes + Deep Off` review. Any additional SQL change requires fresh approval.
- Do not build a universal cache framework or perform unrelated KVK cleanup.
- The operator confirmed that production automatically transitioned targets from Draft to
  Official successfully after Phase 1 deployment. Treat the Phase 2C evidence prerequisite as
  satisfied, but do not start Phase 2C implementation without its separate approval.
- Do not start Phase 2D implementation without separate cross-feature architecture approval.
- Include the already-local Phase 1 deployment documentation and Phase 2 planning documents in the
  first Phase 2 implementation PR.

This is **not** one-pass approved.

Before implementation:

1. Read the active bot and SQL repository instructions and every Required Reading item in the pack.
2. Use `k98-architecture-scope`, `k98-discord-command-feature`, `k98-sql-validation`,
   `k98-test-selection`, and `k98-deferred-optimisation-capture` as directed.
3. Use `k98-security-review-routing` to record separate bot and approved Phase 2A SQL
   `Changes review` decisions with `Changes + Deep Off`. Record a SQL documented skip for later
   slices while SQL remains review-only. Do not start a standard or deep codebase audit.
4. Audit both repositories and return the exact Step 1 output from the task pack.
5. Recommend the first PR-sized Phase 2A plan and its dependencies, but do not implement it.
6. Stop for approval. Do not edit code, SQL, migrations, tests, or docs in the first response.

The audit must prove:

- the exact SQL target row shape and every current dictionary alias;
- the typed target-row, serialization, and compatibility boundary;
- how numeric and name lookup reach one service without changing Discord behavior;
- which duplicate retrieval, last-KVK, exemption, response, and fallback responsibilities can be
  removed safely;
- the current cache callers/processes and a bounded cross-process single-flight design;
- cache lock expiry/crash recovery without publication downgrade;
- whether the Phase 2C production-transition evidence prerequisite is satisfied;
- the full shared fighting-state consumer map and a compatibility rename with unchanged semantics;
- exact per-slice file manifests, test selection, security targets, deployment, smoke, and rollback;
- why SQL remains limited to the approved Phase 2A GovernorID datatype companion and why command
  registration remains unchanged.

Stop after the audit, approval questions, recommended Phase 2A PR-sized plan, and explicit stop
point. Approval of Phase 2A will not approve Phase 2B, 2C, or 2D automatically.
