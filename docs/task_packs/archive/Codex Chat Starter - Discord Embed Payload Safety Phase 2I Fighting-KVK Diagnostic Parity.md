# Archived: Phase 2I delivered and operator-smoke accepted

## Accepted Phase 2I delivery — 2026-09-08

This status supersedes earlier candidate/pending-smoke statements. Chris Watts explicitly accepted
smoke testing as complete. Delivered and tested on the pre-merge production candidate; operator
merges and final main/deployed-head verification remain pending and open the next phase.

Reviewed runtime heads: mirror #260 `06f31a942a1b9b99b17769632beb58a760cb609a`; production #567
`d89e606cf83759bdda4a7b7fdeb96e17aef0d121`. Documentation-only closeout commits follow these heads.
No merge or deployment was performed by this documentation update.

Evidence supplied by the operator: current KVK 16 truthfully returned unavailable with no rows;
historical KVK 15 assembled 5 player, 5 kingdom and 4 camp entries and displayed successfully.
Status at 19:50:52 UTC retained selected KVK 15 and its committed operation; an edit at
19:51:52 UTC committed a new operation. The rejection in the instructed conflicting-selector
sequence was followed by status at 19:54:43 UTC retaining KVK 15 and the same committed operation.
Session tokens, destination identifiers and operation identifiers remain in private operator evidence. The generic rejection
text does not independently identify its cause. Operator reports restart returned the same results
and the capture helper matched the baseline with new diagnostic files created. These are operator
reports; raw message IDs, post-restart receipts and capture files were not independently inspected.

Validation: full mirror 3471 passed, 2 skipped; pinned-dependency matrix 129 passed; production
focused matrix 129 passed; applicable hooks and CI passed. Separate Changes-only, Deep-off reviews
of the two runtime heads covered all 19 changed files with zero findings. Sealed terminal reports
are retained; they are not desktop workbench scan IDs. This Markdown-only closeout has no runtime,
config, SQL, dependency, permission or persistence changes: additional pytest/security scans skipped;
documentation hooks, selector, architecture/deferred/security-routing validation remain required.

Natural production calendar dispatch is expected on 2026-09-09 morning, Europe/London; retain its
actual routing/admission/receipt evidence separately. Phase 2F natural public save remains pending.
Neither observation is closed by diagnostic success. Diagnostics do not prove exactly-once delivery
or all live failure modes. Generic tracked-view timeout and ProcConfig repair remain separate.

Next proposed scope: Phase 2J Ops Diagnostic Convergence, audit first. Preserve all Phase 1–2I
production defaults and existing Phase 2H/2I sessions. No Phase 2J runtime work is approved yet.

## Historical preparation and implementation record

# Codex Chat Starter - Discord Embed Payload Safety Phase 2I Fighting-KVK Diagnostic Parity

Status: selected scope-first task. Design and implementation require approval.

## Copy/paste starter

```text
Begin Discord Embed Payload Safety Phase 2I Fighting-KVK Diagnostic Parity.

Use:
C:\discord_file_downloader\docs\task_packs\Codex Task Pack - Discord Embed Payload Safety Phase 2I Fighting-KVK Diagnostic Parity.md

Historical evidence:
C:\discord_file_downloader\docs\task_packs\archive\Codex Task Pack - Discord Embed Payload Safety Phase 2H Isolated Pre-KVK Dispatch Diagnostics.md
C:\discord_file_downloader\docs\task_packs\archive\Codex Task Pack - Discord Embed Payload Safety Phase 2G Atomic Pre-KVK Reservation.md
C:\discord_file_downloader\docs\task_packs\archive\Discord Embed Payload Safety Audit Findings.md

Phase 2H isolated diagnostic smoke passed on deployed pre-merge commit `7794d2ae`. Phase 2G’s real reservation protocol was exercised successfully through isolated diagnostics. Production-state comparison passed for the observed status/edit operations. Natural production calendar dispatch remains separately pending.

Phase 2H was accepted on deployed pre-merge production
7794d2aee6cc9ea7483a2e0a0f46770e47c925c8. Mirror #259 and production #566 awaited
operator merges and final main deployment/restart verification at preparation. Revalidate both
PRs, final main/deployed heads, restart evidence, clean branch/worktree and Phase 1–2H source.

First response is audit/scope and architecture only. Scope fighting-KVK diagnostic parity through
the existing /kvk_admin test_embed surface. Trace both post_here routes, seasonal selection,
real renderer, all sends/edits, guards, state, locks and returns. Propose explicit validated
destination, mentions disabled, truthful outcomes, owner-bound durable sessions and isolated state.
Do not assume fighting-KVK has Pre-KVK's reservation protocol. Distinguish safe appearance preview
from real admission/receipt validation and gate any reservation extension separately.

Define command compatibility, ownership, restart reopening, retention/cleanup, status/receipts,
permissions, cancellation, once-only offloads, uncertainty and rollback. Preserve Phase 1–2H
production defaults and existing Phase 2H sessions. No global monkeypatch, live state swapping,
calendar/SQL changes, forced duplicates or appearance redesign. Prove real Pycord invocation,
serialized channel/options and Discord group limits; /ops already has 25 children.

Produce safe/fix-now/defer/not-runtime findings, exact runtime/test/tooling/docs and separately
gated SQL manifest, selector/risk tests, Changes-only/Deep-off routing and concrete operator smoke.
Natural production calendar routing and Phase 2F's natural public save remain separately pending.
Diagnostics cannot prove exactly-once or all live failure modes. Keep singleton/public-child
lifecycle, generic view timeout, DM/broad JSON, Stats/KVK History executor audits and ProcConfig
error/false-success repair separate.

Stop for approval after the first response. Do not implement the command or tests yet.
```
