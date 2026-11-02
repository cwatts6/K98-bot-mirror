# Backlog Priority Assessment — 2026-09-09

Owner/selection authority: Chris Watts. Status: assessment complete; operator priority decision
recorded below. Runtime implementation, deployment and channel changes are not approved.

## Operator priority decision — 2026-09-09

**1. KVK Source Migration. 2. Private Inventory Import and Support Sharing. 3. Bot Operational
Reliability WS1 (ProcConfig).** This explicit operator decision supersedes the earlier
containment-first recommendation and the condition that technical containment must precede KVK.

The operator states that all players see the empty KVK stats embed three times a day during the
current KVK. Inventory uploads are optional, used by only a handful of players, and not required
for participation. The operator plans to highlight the exposure risk and advise players to hold
off uploading until the private workflow is fixed. This makes KVK the immediate delivery priority
and inventory the next programme, ahead of ProcConfig/general reliability.

The planned warning is a communication-based risk-reduction measure, not technical containment.
It has not been verified as sent; uploads remain capable of exposing data if players continue.
The security finding stays open without a severity downgrade or claim of remediation. Detailed
residual-risk context stays in the private security record. Recommended review point: completion
of the first KVK audit, or sooner if further exposure or increased inventory use is reported.
No fixed expiry date, channel restriction, suspension or notification has been applied by Codex.

Start next with the existing KVK Source Migration Phase 1 read-only audit and identify the
earliest safe useful correction or new-source delivery. If it proves a blocking shared ProcConfig
dependency, bring back that specific prerequisite for approval; do not silently reorder programmes.
The user's priority decision does not approve later runtime, SQL or live data changes.

## Scope and evidence limits

Quick reconciliation covered all **22 top-level files** present before this assessment document
was created. All were Markdown. Pack/starter pairs and programme/design companions are grouped,
not counted as separate implementation projects. The `archive/` folder contained 281 historical
files; its index and relevant supporting records were checked, not every historical task rerun.
A top-level file is not automatically current work: two paths are compatibility redirects, two
are test-contract fixtures, one is resolved-history material and one is the index.

Current bot code baseline: `1a3a5de3d2e9f349c276725f6271ef19a7517c4f`; working-tree changes are
documentation from the programme-boundary task and supplied backlog packs. SQL source baseline:
`fc0e94ebd2e0a98286069c8a8b71365dd5178657`, clean. Operator-supplied production deployment is
`1e72949dc69f1a1e5a529dbf1951039fe0ba74a6` with clean checkout and the accepted 12:08–12:09 restart.
No fresh remote merge check, live SQL query, source-workbook analysis, Discord ACL inspection,
runtime test, import, upgrade or application execution was performed for this assessment.

Evidence combines current pack status/contracts, focused source/test inspection, the previously
completed WS1 audit and fresh operator urgency. It is a portfolio assessment, not execution of
each pack's full audit. Historical instructions embedded in a starter do not authorize running it.
Numeric delivery estimates would be speculative; effort below is relative and includes integration
and validation, not just code size. Security findings are not ranked by optimisation scores.

## Relative priority and next bounded action

| Order / condition | Programme or task | Benefit / urgency | Effort and delivery risk | Next action and reason |
|---|---|---|---|---|
| **1 — current-KVK delivery track** | KVK Source Migration, starting with Phase 1 audit | Operator priority 1: all players see empty stats three times daily during active KVK; delaying loses useful reporting windows. Data correctness and period identity are unresolved. | Audit medium; full new-source ingestion/reporting programme large/high risk, involving SQL, two source streams and consumers. | Start the existing read-only Phase 1 pack. First distinguish a bounded current-source/configuration defect from the need for new-source migration; trace actual current-KVK blockers before selecting the smallest implementation. Do not treat source files as a safe drop-in backfill. |
| **2 — private inventory programme** | Private Inventory Import and Support Sharing — Phases 1–6 | Recent exposure remains open. Optional use by a handful of players; operator plans risk warning and asks them to defer uploads. Private transport, consent and retention remain significant improvements. | Large/high: shared Pycord upgrade, domain state, multi-image UI, SQL consent, retention, atomic cutover and soak. | Follow KVK under the explicit operator decision. Preserve the selected modal journey and one cutover. Warning/advice does not technically prevent exposure, and the dependency foundation alone is not remediation. Revisit if new incidents or usage changes alter risk. |
| **3 — bounded reliability fix** | Bot Operational Reliability WS1 — ProcConfig | Repeated resource-lifetime failure and false-success reporting are established; design/manifests are complete. | Medium relative to the two full migrations, but high integration risk across workers, transactions and callers; still a coherent bounded delivery. | Revalidate and approve the existing exact design. Bring a prerequisite exception back for approval only if the KVK audit proves a participating-path dependency; it is not a prerequisite to starting that read-only audit. Preserve unknown/partial outcomes and no replay. |
| **4 — bounded assurance** | MGE Sign-Up Tool Task N | Closes restart/view integration and cross-module regression evidence for an already delivered feature. No new broad implementation need is established. | Small/medium audit; any demonstrated defect needs its own scope. | Run the closure audit over current wiring and meaningful restart/permission tests when urgent import/privacy work permits. Coordinate relevant UI regression evidence with the Pycord upgrade, without marking Task N complete from dependency smoke alone. |
| **Gated next review — target 2026-09-15** | Import Pipeline Task C Slice 14, SUMMARY_PROC | Historical nine-batch sample identifies a substantial latency hotspot; potential performance improvement, not a demonstrated current failure. | Medium read-only audit; tuning/decomposition unknown until attribution is proven. | Keep natural evidence collection. Formal audit needs at least 10 days and 30 complete batches, preferably 14 days; on 2026-09-09 the date gate has not elapsed. Current batch count is unverified. An evidenced alert condition can bring it forward. No new automation or forced benchmark is created here. |
| **Later feature** | GovernorOS v2 Phase 9 — /stats kingdom | Valuable leadership overview and historical analytics, but it adds capability rather than repairing current exposure or missing imports. | Large/high: SQL aggregation, bounded history, visual/service work, permissions, performance and regression gates. | Keep proposed. Stabilise or explicitly isolate source semantics before implementing KVK aggregates so the new feature does not need immediate rework. Do not assume every kingdom metric depends on the migration; map actual consumers during its audit. |

Orders 1–3 now reflect explicit operator selection, not only the earlier assessment. Remaining
items retain their gates and relative position. Reassess newly proved dependencies or material
exposure changes with the operator; do not automatically elevate an entire reliability programme.

## Reliability workstreams within the new programme

Do not rank the entire six-workstream Reliability programme as one indivisible prerequisite.

| Workstream | Relative position | Reason / escalation trigger |
|---|---|---|
| WS1 ProcConfig | Highest reliability readiness; order 3 above, with any prerequisite exception separately approved | Repeated observed defect, complete design, known participating path. |
| WS2 remaining executors | Next reliability candidate, focusing first on consequential writes | Some paths may repeat work after entry; their real side effects need confirmation. Raise immediately if a currently used path can repeat data mutation or publication. Avoid generic consolidation first. |
| WS3 lifecycle/rehydration | Next reliability candidate alongside WS2 | Repeated 10-second tracked-view timeout is observed. Identify affected remaining views and whether recovery occurs; raise if current users cannot complete an important workflow. Keep singleton/public-child ownership as separate slices. |
| WS4 DM/JSON ordering | Evidence-led backlog | Meaningful loss/duplication prevention, but ownership and state-contract changes need independent evidence and tests. Raise on lost reminders, duplicate DMs or proved concurrent writer loss. |
| WS5 durable dispatch policy | Significant but separately gated | Can reduce missed/duplicate announcements across ambiguity and restart. Requires explicit policy, migration and rollback decisions; preserve accepted Phase 2K behavior until approved. Raise on actual repeated delivery incidents. |
| WS6 independent import admission | Evidence-gated | At-most-one backend per invocation does not establish cross-invocation exclusivity. First prove overlap and existing SQL protection; do not add durable coordination solely because it might help. |

Optional canonical embed convergence, Ark retention/draft-persistence debt and unrelated SQL
modernisation remain separately captured. They are not newly selected implementation projects.
Natural Pre-KVK/off-season and Phase 2F public-save receipts remain independent observation items,
with Chris Watts retaining ownership; they do not reopen the closed embed implementation programme.

## Important corrections to backlog assumptions

**Inventory:** the provided July Phase 1 is only a dependency/UI-compatibility foundation, with
no intended inventory behavior change. The programme keeps the new path hidden until Phase 5,
after support/consent foundations. Therefore starting Phase 1 is not immediate containment.
The selected modal journey and single user-facing cutover remain product decisions; this assessment
does not introduce a rejected temporary DM/thread/attachment-option journey or silently disable
imports. The operator has now chosen warnings and voluntary upload deferral while KVK goes first; this reduces expected use but does not close the exposure.
Detailed claim-specific security evidence is retained outside the repository/private workflow.

The checked-in Pycord pin still matches the pack's historical Git revision in both requirement
files. Official [Pycord 2.8 release notes](https://github.com/Pycord-Development/pycord/releases/tag/v2.8.0)
and [versioned changelog](https://docs.pycord.dev/en/v2.8.x/changelog.html) support a real stable
release and distinguish legacy Modal/View from Designer components. They do not prove this bot's
compatibility. Recheck the exact approved target, Python runtime and representative UI contracts
when the foundation is selected; no dependency update or capability test was run here.

**KVK:** the supplied programme is a whole-KVK source migration, not just importing a missing file.
Player snapshots, master-roster eligibility, authoritative kingdom/camp totals, UTC scan identity
and report-period semantics differ. The evidence register explicitly says earlier Sheet gaps do
not prove live SQL gaps. The supplied restart's successful table insert counts also do not prove
KVK-16 completeness in each configuration table. Do not add rows, inherit old weights, fabricate
zero endpoints or rerun imports from either inference.

The pack identifies an undesignated/unsupplied master roster and a private source-evidence bundle;
their current availability has not been verified in this assessment. Missing roster acceptance
must not block independent source/repository audit. A current-KVK deadline increases priority,
but cannot waive baseline, aggregate-period or source-identity decisions before publication.

**MGE:** Tasks A–M and much of N's wiring already exist. Current startup/cache registration and
the supplied restart support that classification. The small rehydration/startup tests inspected
primarily assert importability/wiring, supporting the need for the bounded closure audit; this is
not an assertion that no stronger test exists elsewhere or that a runtime MGE failure was proved.

**SUMMARY_PROC:** the historical 62.1–75.8 second duration and approximately 93.8% emitted-subphase
share identify an audit target. They do not attribute the separate coarse timing gap to that
procedure or prove a safe tuning boundary. The pack's alert thresholds can override the wait only
with evidence; no fresh production timing sample was retrieved.

## Exact top-level file reconciliation

The paths below are relative to `docs/task_packs/`. All 22 original files are accounted for.
No supplied programme or fixture was moved, deleted or rewritten to make the list look current.

| File | Classification / disposition |
|---|---|
| `Bot Operational Reliability - Programme Pack.md` | Active proposed programme; six independently gated workstreams. |
| `Bot Operational Reliability Workstream 1 - Design and Manifests.md` | Completed audit/design proposal; not implementation or acceptance. |
| `Codex Task Pack - Bot Operational Reliability Workstream 1 ProcConfig Import Reliability and Truthful Completion Reporting.md` | Active WS1 scope, design approval pending. |
| `Codex Chat Starter - Bot Operational Reliability Workstream 1 ProcConfig Import Reliability and Truthful Completion Reporting.md` | Companion invocation context, not another project. |
| `Private Inventory Import and Support Sharing - Programme Pack.md` | Active privacy programme; current exposure gives priority to containment. |
| `Codex Task Pack - Private Inventory Import and Support Sharing Phase 1 Pycord 2.8 Upgrade and UI Compatibility Foundation.md` | Prepared enabling slice; does not itself implement privacy. |
| `Codex Chat Starter - Private Inventory Import and Support Sharing Phase 1 Pycord 2.8 Upgrade and UI Compatibility Foundation.md` | Contains conditional one-pass instructions; reading it for assessment does not invoke them. |
| `KVK Source Migration - Programme Pack.md` | Active five-phase programme; current-KVK urgency confirmed by operator. |
| `Codex Task Pack - KVK Source Migration Phase 1 Audit and Validation.md` | Ready read-only audit; recommended next substantial task after immediate containment decision. |
| `Codex Chat Starter - KVK Source Migration Phase 1 Audit and Validation.md` | Companion starter; not a separate implementation project. |
| `Player Self-Service Command Centre v2 - Programme Pack.md` | Living programme history through accepted Phase 8.1; Phase 9 remains proposed. |
| `Codex Task Pack - Player Self-Service Command Centre v2 Phase 9 Leadership Stats Kingdom.md` | Genuine future feature; source/SQL/visual/performance and scheduling gates remain. |
| `Codex Chat Starter - Player Self-Service Command Centre v2 Phase 9 Leadership Stats Kingdom.md` | Companion starter for the same proposed feature. |
| `Codex Task Pack - Import Pipeline Deferred Optimisation Task C Slice 14 SUMMARY_PROC Responsibility and Performance Audit.md` | Active natural evidence collection; formal read-only audit date/sample gate remains. |
| `Codex Chat Starter - Import Pipeline Deferred Optimisation Task C Slice 14 SUMMARY_PROC Responsibility and Performance Audit.md` | Gated starter for Slice 14, not permission to benchmark production. |
| `MGE Sign-Up Tool.md` | Delivered A–M; only bounded Task N closure/assurance remains, supported by archived implementation-progress record. |
| `Codex Task Pack - Discord Embed Payload Safety Phase 2L ProcConfig Import Reliability and Truthful Completion Reporting.md` | Compatibility redirect to Reliability WS1; not active embed work. |
| `Codex Chat Starter - Discord Embed Payload Safety Phase 2L ProcConfig Import Reliability and Truthful Completion Reporting.md` | Compatibility redirect to the canonical starter. |
| `KVK_ALL Schema Modernisation - Phase 4 Metric Source Rules.md` | Retained contract fixture; exact top-level path is read by `tests/test_kvk_all_recompute_sql_contract.py:99`. Do not archive blindly. |
| `KVK_ALL Schema Modernisation - Phase 10 Metric Source Correction.md` | Retained contract fixture; exact top-level path is read by the same test module at line 118. Not an unfinished Phase 10. |
| `deferred_optimisations_resolved_append.md` | Two completed-history notes; no active implementation. Consolidation may be documentation cleanup later, not priority work. |
| `README.md` | Current index plus historical narrative; this assessment governs portfolio priority, while existing evidence remains intact. |

Supporting evidence outside this top-level list includes the KVK decision/evidence register,
active/resolved deferred registers, archived MGE progress and original embed audit. These inform
priority; their presence does not authorize every historical task or every deferred item.

## Next-task handoffs and decisions

1. **KVK Source Migration Phase 1 first:** use its existing read-only task pack. Lead with the
   active-KVK empty output seen by all players three times daily and the earliest usable safe
   outcome. Complete independent source/SQL/consumer investigations, preserve known decisions,
   identify exact missing evidence and propose the smallest implementation slice. Distinguish a
   current-source/config correction from new-source ingestion if evidence supports that boundary.
   No mutation, backfill or migration implementation is approved by this priority decision.
2. **Private Inventory Import and Support Sharing second:** preserve the existing selected modal,
   explicit support consent and single-cutover direction. The operator owns the planned player
   warning/advice to pause optional uploads. Keep the exposure open and review residual risk after
   the first KVK audit or new reports. Do not claim a warning has been sent or that uploads are
   technically blocked. No automatic notification, feature suspension or permission change.
3. **Reliability WS1 third:** retain the completed exact design/manifests. Revalidate drift before
   implementation approval. If KVK reveals a necessary shared-path prerequisite, propose that
   precise exception rather than pull in unrelated executors, lifecycle or policy changes.

## Validation and handling

Security triage was completed statically before documentation edits; no tests, application, PoC
or dynamic validation were run during triage. Its complete per-claim result remains outside Git.
This portfolio update changes only assessment/index/programme Markdown. Documentation validators,
introduced-link/hygiene checks and diff review are appropriate; runtime pytest, smoke imports,
command registration execution, SQL tests and security discovery scans are no-runtime-diff skips.
Future code/SQL fixes require their own current Changes-only/Deep-off review and implementation
approval. No scan, severity, remediation success or live containment is implied by this doc review.

Completed documentation checks: architecture passed (zero Python files); deferred validator passed;
security-routing validator passed with zero errors/warnings; selector completed. Its generic
smoke-import/registration suggestions are explicitly skipped for this Markdown-only change.
Introduced local links and Markdown hygiene passed across the 15 owned documentation files,
including the earlier boundary work; `git diff --check` passed. The earlier pre-commit launcher
cache limitation remains documented in the programme pack; no hook pass is claimed here.
