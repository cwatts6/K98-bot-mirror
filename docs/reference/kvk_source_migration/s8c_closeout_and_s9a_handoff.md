# S8C closeout and S9A handoff

> Current handoff: **S9B repository-delivered; not deployed**. See [S9B closeout / S10A scope and exact documentation carry-forward](s9b_closeout_and_s10a_handoff.md).
> Retained evidence and historical approvals below remain intact; no predecessor rerun or live operation is authorized.

> Retained S8B/S8C reference, 2026-09-14: S9B repository delivery is now complete.
> See [S9A closeout / S9B scope and pending documentation delivery](s9a_closeout_and_s9b_handoff.md).
> Historical execution/operator evidence and limits below remain intact; this update does not
> request a rerun or claim live Discord acceptance, bot-machine deployment or activation.


## Delivered state — 2026-09-13

**S8C implementation, code review and repository delivery are complete.** The operator confirms
merges and local pulls. Both worktrees were clean at this closeout's entry. The bot machine remains
outside this delivery. Separately approved post-merge disposable SQL and simulated folder intake
smoke have now run; see [the exact evidence and limits](s8c_folder_intake_smoke_evidence.md).
The operator completed the local work instruction on 2026-09-14: **all seven checks PASS**,
verified against the retained console transcript in the linked evidence.
No bot-machine smoke, deployment or activation is claimed.

| Repository | Merge UTC | Merge commit | Final reviewed head |
|---|---|---|---|
| [Mirror #275](https://github.com/cwatts6/K98-bot-mirror/pull/275) | 2026-09-13 18:44:03 | `913cebaad3b69310a5e5b62289a2e88ecd66d792` | `cd7442a120f4bda03d471bec72f5cbbab60312f5` |
| [Production #582](https://github.com/cwatts6/k98-bot/pull/582) | 2026-09-13 18:45:13 | `afac4118db4bca282c8d12ea3d121701ae2da3c0` | `ce766017476c2e0e1dd5bf38d7fd531da4e2981a` |
| [SQL #82](https://github.com/cwatts6/K98-bot-SQL-Server/pull/82) | 2026-09-13 18:43:41 | `3c1b5ceaa7a686bc594ca8637d0a1569030d66c4` | `083718e971acc7d4593610199a5575bd3159b4e8` |

Bot main/origin main is `b6e45293348ece7b562e29c0451a8c3a7dbe2550`, synchronized from production
`afac4118`; production/main matches the merge. SQL main/origin main matches `3c1b5ce` above.
These are comparison anchors, never reset instructions. No Git mutation is performed by this closeout.
Fresh merged Files changed proof: production's 67 entries cover all **69 physical Bot paths**,
including both filename and previous_filename of the two S8B archive moves. All delivered blobs
match the synchronized local Bot HEAD; archive origins are absent. SQL's **six paths** all match
local SQL HEAD. No S8C implementation or predecessor carry-forward path remains missing.

## Delivered behavior and final review fixes

Private intake supports either file order, one-at-a-time/two-file messages and the existing grouped
admin attachment flow. Explicit season review precedes intake; source remains fixed per season.
Imported kvk_list kingdom/camp/weights configuration gates baseline acceptance. Valid unused scans
are retained and can later become endpoints within that season. Post-use configuration changes are
reviewed/versioned; supplied kingdom/camp totals and DKP remain authoritative, overall independent.
Durable review identities and matched UpdateID, explicit counterpart attestation, CAS/sealed input,
complete selection/full-vector intent and prior endpoint/no-fight/SCANORDER rules remain intact.

Final fixes report the retained semantic-duplicate UpdateID, preserve friendly missing-weight-column
errors, remove unused modal fields and check source/lifecycle under the season lock before storing
artifacts. No shared-original deletion was added. Legacy ingest/recompute admission lifetime remains
preserved. SQL includes SourceAdminReview, additive migration, disposable fixture and static checker;
review metadata says Forward Fix Only, NOCOUNT is set, and synthetic identity literals are Unicode.
All six original mirror/SQL comments and both production comments were answered and resolved.

## Validation and explicit evidence limits

- Final pre-merge production patch: **96 focused tests passed; 4,214 passed / 62 skipped** in the
  full offline suite; production operational logs unchanged. Architecture, deferred-items, routing,
  selector, import smoke, registration **36 top-level / 101 grouped**, and applicable hooks passed.
  Final production Quality, command governance and gitleaks CI passed; mirror and SQL CI passed.
- SQL text-only checker: **13 checks passed**. S8C disposable migration apply/rerun, rollback fixture, actual
  prerequisite-backup restore and **five opt-in Bot SQL cases passed** on the separately approved
  new target. Direct execution does not validate deployment-runner history. Local whole-SQL validator previously could not write its sandboxed log;
  hosted SQL CI passed. Neither static checks nor repository merge prove applied migrations.
- Full implementation Changes reviews: Bot `d5641b69-74b3-4241-b7c5-fbc992350b2b`, SQL
  `00c2caf5-e6ce-4ace-816b-268120f8aabd`; follow-ups Bot `43ab3fde-0947-4cec-b320-1200fa1a3e63`,
  SQL `1f23bee6-0463-4fa7-9eff-6b11a538270f`: zero findings, Deep off.
  Production review-fix Changes `9cc8aa2d-3e9d-4ece-9c1a-f054280cfd99` covered all three changed
  runtime files with zero findings. It retained a snapshot warning after Ruff combined test imports;
  the mechanical test-only difference was manually checked, with runtime changes unchanged.
- Earlier S8C 4,202/62 and 4,208/62 results are historical checkpoints, superseded by final 4,214/62
  offline evidence. None is a fresh post-merge or bot-machine smoke result.
- S8B accepted operator smoke and retained **50-case disposable SQL**/actual-restore evidence are
  separate from later offline fixes and offline-only SQL runner-history support. S8A's **six-script**
  and VERIFYONLY evidence remains separate; no S8A actual restore is retrospectively claimed.
- Preserve S6-OPS01/PERF01/CAP01, uncertain publications `e19c89ac-7977-5f28-ae4c-031807cd1728`
  and `54a2480a-26fb-5bad-a3f5-9321525a731c`, and every retained database, backup, receipt and file.

## What is next

**Next implementation slice: S9A Public Routing and Availability, initial review/scope only.**
Use the [S9A pack](../../task_packs/archive/Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S9A%20Public%20Routing%20and%20Availability.md)
and [starter](../../task_packs/archive/Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S9A%20Public%20Routing%20and%20Availability.md).
The approved S7 plan specifies 20 S9A paths; S9B card work follows, then S10 export coordination
and S11 integration evidence. No later implementation or automatic new task begins here.

The separately approved disposable SQL and folder intake smoke are now recorded in
[the execution evidence](s8c_folder_intake_smoke_evidence.md). This tests real parsers/services/DAL/SQL
through simulated transport; live Discord and real Google kvk_list import remain untested here.
The operator completed the [step-by-step work instruction](s8c_operator_work_instruction.md)
on 2026-09-14 with all seven checks PASS. The local walkthrough is accepted; no repeat is needed.
The retained transcript and its exact scope are recorded in the linked execution evidence.
Production SQL deployment, bot-machine delivery, intake activation and live transport acceptance
remain separate operations. SourceRouting.Enabled alone is not public routing.

## Exact pending documentation and smoke-tool carry-forward

On 2026-09-14 the operator approved carrying this complete documentation/smoke-tool union in
the S9A delivery cycle, rather than a standalone S8C follow-up PR. The two SQL documentation paths
remain a separate SQL-repository PR in that cycle. This approves grouping only, not immediate
implementation, publication or deployment.

The following documentation and smoke-tool changes are local and uncommitted. The next separately authorized
Bot PR must include their union with S9A implementation and approved amendments, or provide
individual merged commit/blob proof. Check actual GitHub filename AND previous_filename, including
both sides of both S8C archive moves. Do not infer completeness from counts alone.

| Action | Bot repository-relative path |
|---|---|
| Modify | `README-DEV.md` |
| Modify | `docs/reference/README.md` |
| Modify | `docs/reference/kvk_source_migration/decision_and_evidence_register.md` |
| Modify | `docs/reference/kvk_source_migration/integration_contract_and_consumer_matrix.md` |
| Modify | `docs/reference/kvk_source_migration/integration_implementation_manifests.md` |
| Modify | `docs/reference/kvk_source_migration/phase_2_acceptance_scenarios.md` |
| Modify | `docs/reference/kvk_source_migration/phase_2_contract_and_architecture.md` |
| Modify | `docs/reference/kvk_source_migration/phase_2_evidence_and_validation_log.md` |
| Modify | `docs/reference/kvk_source_migration/phase_2_implementation_plan.md` |
| Modify | `docs/reference/kvk_source_migration/phase_2b_evidence_and_validation_log.md` |
| Modify | `docs/reference/kvk_source_migration/post_s6_handoff_log.md` |
| Modify | `docs/reference/kvk_source_migration/post_s6_integration_requirements.md` |
| Modify | `docs/reference/kvk_source_migration/release_evidence_log.md` |
| Modify | `docs/reference/kvk_source_migration/release_readiness_and_rollback.md` |
| Modify | `docs/reference/kvk_source_migration/s8a_closeout_and_s8b_handoff.md` |
| Modify | `docs/reference/kvk_source_migration/s8b_closeout_and_s8c_handoff.md` |
| Create | `docs/reference/kvk_source_migration/s8c_closeout_and_s9a_handoff.md` |
| Create | `docs/reference/kvk_source_migration/s8c_folder_intake_smoke_plan.md` |
| Create | `docs/reference/kvk_source_migration/s8c_folder_intake_smoke_evidence.md` |
| Create | `docs/reference/kvk_source_migration/s8c_operator_work_instruction.md` |
| Create | `scripts/smoke_kvk_source_intake.py` |
| Create | `tests/test_kvk_source_folder_smoke.py` |
| Modify | `docs/reference/local_sql_development.md` |
| Delete (archive origin) | `docs/task_packs/Codex Chat Starter - KVK Source Migration S8C Intake and Admin Pairing UX.md` |
| Create | `docs/task_packs/Codex Chat Starter - KVK Source Migration S9A Public Routing and Availability.md` |
| Delete (archive origin) | `docs/task_packs/Codex Task Pack - KVK Source Migration S8C Intake and Admin Pairing UX.md` |
| Create | `docs/task_packs/Codex Task Pack - KVK Source Migration S9A Public Routing and Availability.md` |
| Modify | `docs/task_packs/KVK Source Migration - Programme Pack.md` |
| Modify | `docs/task_packs/README.md` |
| Modify | `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S7 Integration Contract and Implementation Planning.md` |
| Modify | `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S8A SQL Foundation.md` |
| Modify | `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S8B Bot Source and Matched Update Services.md` |
| Create (archive destination) | `docs/task_packs/archive/Codex Chat Starter - KVK Source Migration S8C Intake and Admin Pairing UX.md` |
| Modify | `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S7 Integration Contract and Implementation Planning.md` |
| Modify | `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S8A SQL Foundation.md` |
| Modify | `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S8B Bot Source and Matched Update Services.md` |
| Create (archive destination) | `docs/task_packs/archive/Codex Task Pack - KVK Source Migration S8C Intake and Admin Pairing UX.md` |
| Modify | `docs/task_packs/archive/README.md` |


Separate SQL carry-forward: modify `docs/SQL_DELIVERY_LOG.md` and `migrations/README.md` in the SQL
repository only. These two paths must never enter a Bot PR; verify their later SQL PR separately.

## Historical documentation-closeout validation/security decision

Markdown-only status/evidence/link/archive/planning changes; no executable, configuration,
permission, data-access or persistence behavior changes. Bot documented security skip and separate
SQL two-document skip via k98-security-review-routing; no scan started. Runtime pytest, imports,
registration and SQL execution are skipped for this documentation-only closeout; retained results
above remain dated pre-merge evidence. Closeout checks passed: architecture (0 Python paths),
deferred-items (31 Markdown files), security-routing (0 errors/warnings), exact-path selector,
Bot/SQL whitespace, 510 local links (none missing), original exact 33-path Bot documentation union and
S9A's exact 20-path S7 manifest. SQL changes are exactly the two documentation paths above.
No staging, commit, push or PR.

Smoke execution adds the evidence summary, adapter and tests: the current Bot union is 38 physical paths (36 documentation and two Python paths), including the operator work instruction.
Approved testing has completed as recorded in the linked evidence. The work-instruction revision is
documentation-only; it does not add another SQL/test execution or claim operator acceptance.
