# Bot Operational Reliability — Programme Pack

Date: 2026-09-09. Owner and priority decision: Chris Watts.
Status: programme boundary/documentation approved; portfolio assessment complete; priority selected; runtime implementation approval pending.

[Current portfolio assessment](Backlog%20Priority%20Assessment%20-%202026-09-09.md) records
the operator-selected order: KVK Source Migration first, private inventory second, Reliability
WS1 third. Empty KVK stats are seen by all players three times daily; inventory is optional and
used by a handful. The operator plans a risk warning/advice to defer uploads. This is not technical
containment or remediation. Start KVK's read-only Phase 1 next; any proved WS1 prerequisite
exception requires approval. Runtime and live-action approvals remain separate.

## Authority and programme boundary

The operator approved separating operational reliability from Discord Embed Payload Safety on
2026-09-09. The embed programme's approved implementation scope closes through Phase 2K. Original
payload families are delivered, assessed safe within their enforced contracts, or explicitly
deferred; this is not a claim of exhaustive automated coverage or completion of every observation.
Do not create automatic embed Phases 2M/2N for newly discovered reliability work.

ProcConfig Import Reliability and Truthful Completion Reporting, formerly Phase 2L, is now
**Workstream 1 (WS1)** of this programme. Its audit/design is complete and retained in the
[WS1 design and manifests](Bot%20Operational%20Reliability%20Workstream%201%20-%20Design%20and%20Manifests.md).
The [WS1 task pack](Codex%20Task%20Pack%20-%20Bot%20Operational%20Reliability%20Workstream%201%20ProcConfig%20Import%20Reliability%20and%20Truthful%20Completion%20Reporting.md)
and matching chat starter are canonical; the old Phase 2L paths are redirects for historical links.
Neither the rename nor this programme approval authorizes runtime, test, SQL or state changes.
WS1 numbering identifies the first designed workstream; it does not preselect the next execution
priority ahead of the two other backlog programmes below.

Objective: consequential work executes within an explicit ownership contract, preserves known
state, and reports completion honestly across failures, cancellation and restart. Deliver bounded,
independently approved changes rather than a general executor or persistence rewrite.

## Proposed deliverables and acceptance boundaries

All rows are proposed deliverables, not blanket implementation approval or a mandatory sequence.
Existing items in [the active register](../reference/deferred_optimisations.md) retain their evidence
and ownership. Programme grouping does not mark them resolved or duplicate them as new findings.

| Workstream | Deliverable / evidence required for acceptance | Why separate from WS1 |
|---|---|---|
| WS1 — ProcConfig resource lifetime and truthful outcomes | Complete participating call path; explicit cursor/connection ownership and result exhaustion; separate autocommit target connection; confirmed commit ledger; success/failed/partial/unknown outcomes through workers, reports and callers; required unique per-run manifest; at most one backend execution per invocation after submission. Deterministic late-error, ambiguous-commit, transport, cancellation, cleanup and artifact tests plus natural smoke. Exact runtime/test manifests are in the design; proposed SQL mutation manifest is empty. | Repeated production HY000 followed by false success is established. This coherent root-cause family is already designed; implementation still requires approval after programme comparison. |
| WS2 — Remaining executor replay prevention | Inventory Stats, KVK History and stats-alert call shapes and side effects. Prioritise consequential writes if confirmed. Prove no post-entry fallback/re-execution with invocation counters, argument/return preservation and timeout/cancellation tests. Consolidate helpers only where contracts actually match. | Different callers and side effects require individual evidence. A generic rewrite would broaden regressions and is not needed to repair the participating ProcConfig adapters. |
| WS3 — Process/task ownership and restart rehydration | Separate slices for singleton ownership, generic tracked views and public-reminder child supervision. Establish actual resumed/aborted work, preserve identity and permissions, and report partial/timeout truthfully. Test concurrent ownership, shutdown, cancellation and restart as applicable. | The supplied final restart aborted remaining tracked views after 10 seconds at 12:09:24.054; recovery and affected views are not yet established. Ownership/supervision changes need their own lifecycle contract. |
| WS4 — DM and JSON persistence ordering | Identify authoritative writers and state identities; design ordered writes and restart-safe persistence for each selected state family. Test competing writes, interruption and restart without losing sent/scheduled markers or silently replaying messages. | Atomic replacement alone does not solve ownership or concurrent ordering. Preserve the narrower accepted Phase 2F active-public-reminder fix. |
| WS5 — Durable dispatch ownership and delivery policy | Separately design fighting admission, KS preclaim timing, ambiguous Pre-KVK edit outcomes, and durable delivery audit semantics. Define uncertain-delivery behavior, migrations, concurrency tests and bounded rollback before code. | These are policy/persistence changes with high regression risk. They must preserve accepted Phase 2K receipt/claim distinctions until a separately approved policy changes them. No automatic replay is implied. |
| WS6 — Independent ProcConfig invocation admission | Establish whether admin/startup/pipeline invocations overlap and what existing SQL locks protect. If justified, design cross-invocation admission and provenance with exact ownership and compatibility; test concurrent entry and crash uncertainty. | WS1 guarantees at most one backend per invocation, not global exactly-once execution. Current manifests are observations, not durable admission authority. Avoid inventing a recovery/reservation protocol without evidence and approval. |

Programme-wide acceptance for any selected slice: current scope and exact manifests, source-of-truth
SQL validation where applicable, meaningful positive/negative and restart tests, required validators,
Changes-only security review with Deep off or precise skip, independent bot/SQL Git targets,
reviewed promotion, deployed-SHA/clean-checkout/restart evidence, and bounded rollback. Logs must
distinguish workflow, SQL, artifact and Discord receipt facts rather than collapse them into success.

Preserve Phase 2J removal, Phase 2H/I sessions and defaults, accepted payloads/mentions and Phase 2K
delivery/claim semantics. WS1 adds no automatic replay/recovery protocol. Later work cannot treat
this charter as permission to change dispatch policy, delete state, rerun imports or mutate live SQL.
Each workstream may close independently; newly discovered debt must not silently extend it.

## Embed programme observations and adjacent backlog

Chris Watts retains ownership of these observation follow-ups. Attach exact deployed revision,
timestamps and receipt/state evidence to the original accepted records; no forced live test is
authorized by this documentation update.

| Follow-up | Completion evidence | Disposition |
|---|---|---|
| Natural Pre-KVK dispatch | Next legitimate seasonal execution with matching reserve/commit/message receipt and correct mention/state behavior; isolated diagnostics alone do not close it. | Open; expected approximately two months from 2026-09-09. Not a blocker to accepted Phase 2K smoke or programme implementation closure. |
| Natural off-season production behavior | Legitimate off-season route, outcome and actual delivery/admission evidence where applicable. | Open until the natural opportunity; do not infer from fighting or isolated preview success. |
| Phase 2F active public-reminder save | Natural save evidence from the exact active-public-reminder persistence path. DM saves, live-event tracker writes and pinned-calendar edits do not substitute. | Open independently; implemented atomicity remains accepted. |

Optional canonical payload-boundary convergence, Ark keep-all confirmation-history retention,
strict transactional Ark draft-write debt, and unrelated SQL modernisation/performance remain
separate backlog candidates. No new payload incident or measured performance bottleneck is claimed.
Require a concrete benefit and domain-specific scope before selection; do not absorb them into
WS1 or make their completion a condition of closing the embed programme.

## Cross-programme intake and priority decision

Assess these three candidates together before selecting the next implementation task. Both sets
of programme files arrived during this documentation update; their headers/scope were inspected
for intake, not their full engineering/data/security evidence. Pack assertions and historical
approvals require reconciliation with the current source and the operator's present priority gate.

| Candidate | Evidence currently available | Assessment still required |
|---|---|---|
| Bot Operational Reliability | WS1 full audit/design and repeated failure/false-success evidence; WS2–WS6 captures above. | Compare the smallest useful WS1 delivery against the other programmes; do not rank an entire six-workstream programme as one indivisible task. |
| [KVK Source Migration](KVK%20Source%20Migration%20-%20Programme%20Pack.md) | Programme, Phase 1 pack/starter and decision/evidence register received. Header inspection shows a broader source-aware player-snapshot and authoritative kingdom/camp totals migration, preserving the legacy route; implementation unapproved. | Reconcile the operator's missing-import symptom with the supplied migration scope. Establish missing KVKs/scans/source files, expected versus actual output, affected users, source availability, lineage and correction risks. Do not reduce the programme to a simple backfill, assume ProcConfig is the cause, or assume reimport is safe. Validate SQL before data repair. |
| [Private Inventory Import and Support Sharing](Private%20Inventory%20Import%20and%20Support%20Sharing%20-%20Programme%20Pack.md) | Programme and Phase 1 pack/starter received. Operator reports upload exposure; the pack also describes public extracted values/review controls and automatic administrator debug uploads. These are reported findings, not fresh current-code validation. | Route the existing finding through k98-security-review-routing and Codex Security triage-finding; retain finding/scan IDs and revisions if available. Establish viewers, data, duration, controls, severity and any immediate containment need. Compare the full private-upload/support-consent programme with a bounded containment option; its dependency/UI foundation alone is not a privacy fix. No live cross-user test or disclosure is authorized here. |

Received KVK companions: [Phase 1 audit pack](archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20Phase%201%20Audit%20and%20Validation.md),
[chat starter](archive/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20Phase%201%20Audit%20and%20Validation.md),
and [decision/evidence register](../reference/kvk_source_migration/decision_and_evidence_register.md).
Its pack identifies a separate private evidence bundle and an unsupplied master roster; their
availability has not been independently checked here. Historical pack instructions to begin its
full Phase 1 audit do not override the present cross-programme comparison boundary.

Received inventory companions: [Phase 1 pack](Codex%20Task%20Pack%20-%20Private%20Inventory%20Import%20and%20Support%20Sharing%20Phase%201%20Pycord%202.8%20Upgrade%20and%20UI%20Compatibility%20Foundation.md)
and [chat starter](Codex%20Chat%20Starter%20-%20Private%20Inventory%20Import%20and%20Support%20Sharing%20Phase%201%20Pycord%202.8%20Upgrade%20and%20UI%20Compatibility%20Foundation.md).
The July pack's dependency baseline and claims of product/conditional one-pass approval are
historical inputs; do not execute its starter or upgrade dependencies as part of programme intake.

Both programme sets are now under `docs/task_packs/` (plural, underscore), with supplied filenames
and contents preserved. Any supplemental evidence should include reproduction/observation evidence,
affected revision and expected behavior, dependencies, prior decisions and any proposed remediation.
Keep raw uploads, credentials and private player evidence out of mirror-bound documentation; use
sanitized summaries or references to private evidence. Original private security findings remain
unchanged in their security workflow, not in deferred-optimisation scoring or public SECURITY.md.

Assessment deliverable: one side-by-side decision record separating observed facts from assumptions,
security severity/containment, user/data impact, recurrence, exposure, urgency, dependency order,
effort, implementation risk and reversibility. Recommend the next bounded task and explain the
tradeoffs; retain alternatives and obtain operator selection/implementation approval. Triage may
justify urgent inventory containment before the larger programme, but no severity or accepted-risk
decision is invented here. Do not use optimisation scores to lower vulnerability severity.

The comparison is **complete**, including the other top-level backlog groups; see the assessment
above for recommendation, conditions and exact file reconciliation. Operator priority is now selected as above;
runtime implementation approval remains pending. The intake table preserves the evidence available when
the packs first arrived; current priority and private security triage supersede pending-assessment
wording in that historical intake. Documentation approval is
not runtime approval. If work resumes later, recheck source/deployment drift before relying on the
WS1 exact manifests. No scheduler, reminder automation or background monitor is created by this pack.

## Final Phase 2K entry evidence

Mirror #262 merged 2026-09-09 12:06:38 UTC (`134fcee529766cb258fb644b5ca0a9bad47af226`);
production #569 merged 12:07:06 UTC (`1e72949dc69f1a1e5a529dbf1951039fe0ba74a6`). Verified
mirror main was `1a3a5de3d2e9f349c276725f6271ef19a7517c4f`, matching the mirror publication from
that production main. Operator-supplied bot HEAD equals production main and status is clean.
Associated restart: invoked 12:08:56.672, ready 12:09:10.755, full startup complete 12:09:15.539;
new child PID 4800. This closes the final deployment association gap, while preserving candidate
smoke provenance at production `36208765bf7200fa6855f3892e6b32d43b23bccf` / mirror
`2d892cefcfdfa0a8263efe69997bf292503b23aa` and historical 3514 passed / 2 skipped.

The natural startup ProcConfig run logged success at 12:09:30.498 without HY000 in the supplied
excerpt; the parent logged `success=True report_keys=None` at 12:09:30.764. One successful run
does not resolve the intermittent defect or independently prove full SQL result completion.
Full-startup completion does not establish completion of every background job.

## Documentation-change validation

This boundary update changes Markdown only: programme/WS1 packs and design, compatibility redirects,
developer/task/archive indexes, original audit, Phase 2K closeout and active/resolved register context.
Run architecture, deferred, test-selector and security-routing validators, local-link checks and
Markdown hygiene. Runtime pytest, imports, command-registration execution and SQL tests are skipped
because no runtime/test/config/SQL behavior changes. Security review is a documented no-runtime-diff
skip for these files; no security finding is adjudicated by that skip. Future fixes require their
own Changes-only/Deep-off decision and separate SQL review when a SQL delta exists.

Boundary-update checks on 2026-09-09: architecture passed (zero Python files), deferred validation
passed, security-routing passed (zero errors/warnings), selector completed, and `git diff --check`
passed. Introduced local links and Markdown hygiene were checked across the 14 owned documents.
The selector's generic smoke-import/registration recommendations are explicitly skipped for this
Markdown-only update. Pre-commit hook launch was blocked by its read-only cache database before
hooks ran; do not label those hooks passed. Independent checks cover introduced whitespace,
conflict markers, EOF, fences and local links; pre-existing README formatting was left unchanged.
Operator-added KVK and inventory programme/evidence documents are preserved unchanged and are outside this
update's owned manifest. No commits, PRs, live actions or runtime tests were performed.
