# Codex Chat Starter - KVK Target Publication State Separation

## Copy/Paste Starter

Codex, take on the task defined in:

`docs/task_packs/Codex Task Pack - KVK Target Publication State Separation.md`

The required outcome is to separate KVK target publication status from the shared KVK fighting
state.

Current problem:

- the shared `DRAFT / ACTIVE / ENDED` KVK state is a Pass 4 fighting lifecycle;
- `/kvk targets` currently copies that state into the target cache and output;
- for KVK 16, matchmaking scan 1059 had already fixed the targets while the current scan was 1060
  and Pass 4 starts at scan 1087, so the shared fighting state correctly remained `DRAFT` but the
  player target output incorrectly said the fixed targets were Draft;
- target generation already uses `MATCHMAKING_SCAN` when available and otherwise uses `DRAFTSCAN`;
- the bot needs durable proof of which source scan actually produced the displayed target rows.

The approved product model is:

```text
Shared fighting state:
DRAFT -> ACTIVE -> ENDED
         Pass 4    KVK end

Target publication state:
DRAFT -> OFFICIAL -> HISTORIC
         successful exact matchmaking-scan publication

UNKNOWN / Unverified:
used whenever publication provenance cannot be proved safely
```

Key constraints:

- Do not change the shared KVK state resolver or make it Active at matchmaking.
- Preserve Pre-KVK stats alerts until Pass 4, live KVK alerts from Pass 4, daily overview timing,
  history finalisation, and leadership-review finalisation.
- Official targets must be proved from persisted successful target-generation metadata, not merely
  from `MAX(ScanOrder) >= MATCHMAKING_SCAN`.
- Preserve target formulas, values, exemptions, `/kvk targets` arguments, permissions, response
  visibility, account selection, and fallback behaviour.
- Add or reuse a durable SQL publication/provenance contract recording KVK, actual source scan,
  source type, configured scans, publication time, row count, output object, and publication
  version/signature.
- Keep target rows, bot-facing view/pointer, and publication metadata consistent.
- Preserve fixed Official targets as later scans and Pass 4 progress. Do not silently republish an
  Official target set through routine processing.
- Change cache identity and refresh rules to use publication provenance, with atomic writes,
  last-known-good safety, cross-KVK protection, and deliberate legacy-cache migration.
- Update both the modern image card and fallback embed with Draft, Official, Historical, and
  Unverified state/source wording. Missing state must never default to Official.
- No new command or command-registration change is expected.
- SQL must be deployed and the current publication verified before the bot is deployed.

This is **not** one-pass approved.

Before any implementation:

1. Read the active bot and SQL repository instructions and the Required Reading section of the task
   pack.
2. Use `k98-architecture-scope`, `k98-discord-command-feature`, and `k98-sql-validation` as directed.
3. Use `k98-security-review-routing` to record provisional separate bot and SQL `Changes review`
   decisions. The intended final setup for each is `Changes + Deep Off`. Do not start a standard or
   deep codebase audit.
4. Audit both repositories and return the required Step 1 output below.
5. Stop for approval. Do not edit code, SQL, migrations, tests, or docs in the first response.

## Step 1 Required Output

Return:

1. Audit Summary
2. Current KVK State Consumer Map
3. Current `/kvk targets` Command, Service, Cache, Renderer, And Fallback Map
4. Current SQL Target Generation And Source-Scan Selection Map
5. Current `v_TARGETS_FOR_UPLOAD` Publication/Provenance Risks
6. Current Cache Schema, Refresh Triggers, Persistence, And Restart Behaviour
7. Proposed Typed Target Publication Metadata And State Resolver
8. Exact Draft / Official / Historical / Unknown Rules And Reason Codes
9. State Transition And Failure Matrix
10. Proposed SQL Object Ownership, Transaction Boundary, Migration, And Rollback Posture
11. Proposed Bot DAL / Service / Cache / Renderer Ownership
12. Legacy Cache And Model Compatibility Strategy
13. Exact Bot And SQL Review/Modify/Create File Manifests
14. Focused And Broader Test Selection
15. SQL-First Deployment, Current-KVK Republish/Verification, Bot Deployment, Cache Rebuild, Smoke,
    And Rollback Plan
16. Provisional Bot And SQL Changes-Review Targets With Deep Off
17. Refactor Findings And Structured Deferred Candidates
18. Approval Questions
19. Explicit Stop Point

The audit must specifically answer:

- how the SQL procedure proves whether it actually used `DRAFTSCAN` or the exact configured
  `MATCHMAKING_SCAN`;
- whether an existing SQL object can own publication metadata or whether
  `dbo.KVK_Target_Publication` should be created;
- whether a dedicated `dbo.v_KVK_TARGETS_FOR_BOT` view or another single-read consistency mechanism
  is safest;
- how routine processing will avoid silently replacing an Official fixed target set;
- whether a default-off operator force-republish path is genuinely required;
- how the bot will prevent a previous KVK cache or stale view from being labelled current;
- how a matching last-known-good Official cache behaves during a transient SQL failure;
- how `target_state` and `source_state` will be renamed or compatibly evolved;
- why stats alerts, daily overview, history, leadership review, and command registration remain
  unchanged.

Do not implement until the audit, target architecture, SQL contract, cache transition matrix, and
first PR-sized plan have each been approved.
