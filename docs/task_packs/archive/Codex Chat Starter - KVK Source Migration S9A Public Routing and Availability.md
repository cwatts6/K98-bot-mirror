# S9A starter — Public Routing and Availability

> Archived 2026-09-14 after merged mirror #276, production #583 and SQL #83.
> This document preserves the S9A scope, approvals and execution/review history.
> Current authority: [S9A closeout](../../reference/kvk_source_migration/s9a_closeout_and_s9b_handoff.md) and [S9B scope pack](../Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S9B%20Stats%20Target%20Card%20Context%20and%20Admin%20Dispatch.md).
> Earlier prospective instructions below are historical, not renewed authorization.


Please begin **S9A initial review/scope only** using
[the task pack](Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S9A%20Public%20Routing%20and%20Availability.md),
[the S8C closeout](../../reference/kvk_source_migration/s8c_closeout_and_s9a_handoff.md), current AGENTS/core
references, approved S7 contract/manifests, authoritative SQL, architecture/EndScanID amendment and
retained S6 evidence. S8C code review and repository delivery are complete: mirror #275, production
#582 and SQL #82 merged, local pulls verified. Separately approved S8C disposable SQL and automated
folder smoke passed; Chris reported PASS on all seven local operator walkthrough checks on 2026-09-14.
Read the retained execution/operator evidence linked from the closeout. No live Discord acceptance,
bot-machine pull, deployment or activation is claimed. Keep S8B accepted smoke/50-case evidence and
offline runner-history support distinct from S8A six-script evidence and S8C evidence.

Comparison anchors (never reset instructions): Bot main/origin main
b6e45293348ece7b562e29c0451a8c3a7dbe2550; production/main
afac4118db4bca282c8d12ea3d121701ae2da3c0; SQL main/origin main
3c1b5ceaa7a686bc594ca8637d0a1569030d66c4. Recheck both repos and preserve all pending work.

The operator approved carrying the pending S8C documentation and smoke tooling in the S9A slice
on 2026-09-14; do not create a standalone S8C documentation/smoke-tool PR. Scope the exact 20 S9A
runtime/test paths plus the complete 38-path Bot carry-forward manifest: 36 documentation paths and
`scripts/smoke_kvk_source_intake.py` plus `tests/test_kvk_source_folder_smoke.py`. Those two completed
S8C paths are approved carry-forward, not additional S9A feature work requiring renewed approval.
Include smoke execution/operator acceptance evidence, the work instruction, both sides of both S8C
archive moves and these S9A outputs. The current union is 58 physical Bot paths before amendments.
Eventual separately authorized S9A Bot PR must include the complete exact union or prove specific
paths already merged, checking `filename` AND `previous_filename`; counts alone are insufficient.
Carry SQL `docs/SQL_DELIVERY_LOG.md` and `migrations/README.md` in a separate SQL-repository PR
in that S9A delivery cycle; never include them in the Bot PR. Preserve external evidence locally.
This grouping decision does not authorize implementation, Git publication or SQL execution now.

Trace ordinary callers through fixed-source complete selection and availability/cache handling.
Preserve no mixed sources or silent legacy fallback, authoritative aggregates/DKP/overall, B0,
UTC starts, daily SCANORDER, unused retained scans and movable within-season windows, exact endpoint
chain, CAS/sealed inputs, durable UpdateID and explicit counterpart attestation. SourceRouting.Enabled
alone does not implement public routing. Retain admission locks and existing grouped commands;
no new top-level command, S9B/S10 implementation or activation. Use security routing then Changes,
Deep off at the exact implementation target when approved; assess SQL independently.

Return scope, risks, tests and implementation plan for approval. Preserve S6-OPS01/PERF01/CAP01,
both uncertain publications and all retained databases/files. No SQL/provider/Discord execution,
real imports/exports, bot-machine pull/restart/deployment, predecessor rerun, Git publication or
automatic new task. Do not re-ask settled decisions or conflate disposable S8C SQL/folder evidence with live Discord acceptance.
