# Guided recovery: P0a first release and P0b full release

Operator decision, 16 October 2026: release complete supported workflows early for
admin feedback, then finish the full P0 scope. Notify the operator as soon as P0a
is deployment-ready; the operator will arrange the maintenance window and deploy.
This authorizes preparation and validation, not a live deployment or SQL install.

## P0a — first release

Status: **preparing; not deployment-ready**. Candidate implementation heads are
Bot `c66b0d81` (the source-pin correction on draft PR #361's `34cdb5c5`, including
#360 and the merged #356 work) and SQL
`71c6cedcdc317b49df5a312a938759c5a6183a93` (draft PR #119 and predecessors).
These are development candidates, not private-production deployment commits.

The initial pilot must provide complete alert-to-verification workflows for:

1. Verified abandoned configuration reads, including the approved automatic
   read-only release and guided investigation when proof is insufficient.
2. Account/SQL writer refusal before execution: explain and link the blocking
   operation, preserve the saved inputs, show registration changes, then confirm
   one fresh admitted continuation without replaying an uncertain write.
3. Atomic configuration publication: distinguish rollback from committed output,
   guide exact release or capture/export settlement, and offer separately confirmed
   fresh configuration publication or an explicit decision to retain prior config.

Other already implemented families may join P0a only after their complete
acceptance evidence and required dependencies are recorded in the release matrix.
Do not expose an unfinished repair merely because its backend is present in the
candidate stack. Discovery must still report unsupported incidents accurately;
absence of a repair must never be described as a healthy or resolved outcome.

P0a release acceptance:

- Freeze exact Bot and SQL commits, dependency/PR order, migrations and hashes.
- Resolve the known source-pin mismatches by identifying each original reviewed
  image and intended change. Do not broadly rebaseline unrelated SQL objects.
- Prepare the supported updater/release metadata, matching protected runtime
  contracts, SQL-before-Bot sequence and a tested rollback/forward-recovery plan.
- Pass an integrated full-suite run, or explicitly qualify unrelated baseline
  failures with evidence; pass architecture, routing, registration, import, lint,
  whitespace and operational-log-isolation checks on the release candidate.
- Complete exact-diff security reviews for any new runtime/deployment changes in
  each repository, and retain the sealed reviews for the included feature stack.
- Prove proactive discovery, private admin-only review pages/buttons, confirmation,
  execution and independently verified settlement for every enabled repair.
- Prove restart, lost reply, duplicate/stale click, changed registration, live
  ownership and failure during repair without duplicate writes or timeout release.
- Document which incidents P0a can fix and which remain P0b; verify the runtime
  exposure matches that matrix. An admin must not need to invent a query/command.
- Prepare a concise operator deployment packet and feedback checklist. Notify the
  operator when all pre-window gates pass; record live acceptance after deployment.

Feedback should capture whether the alert identifies the issue before dependent
work fails, whether checks/actions are understandable, and whether the final
message accurately describes the verified result and any remaining work.

## P0b — full release

These remain required acceptance work, not deferred optimisation:

1. Historical partially applied configuration writes and guided superseding repair.
2. UPDATE_ALL2 partial reporting continuation without repeating committed imports.
3. Durable whole-pipeline continuation: caches, maintenance, remaining publication,
   pre-request failures and historical cases with missing inputs.
4. All-copy containment/active-registration-history evidence loss, with guided
   verification and superseding repair rather than fabricated success evidence.
5. Held access without verifiable ownership and its executable guided disposition.
6. Integrated rollover and recovery acceptance across worker execution, final
   independent verification, restart, concurrency and interruption during repair.

P0b incorporates P0a feedback and passes the full original recovery coverage matrix.
P0 is complete only after P0b acceptance; P0a deployment is an interim milestone.
The broader bot recovery programme outside P0 remains in scope as previously agreed.

Each remaining workflow must meet these specific acceptance outcomes as well as
the shared alert, private review, confirmation, audit and verification requirements:

| Required P0b workflow | Completion criterion |
| --- | --- |
| Historical partial configuration | Admin reviews the affected configuration and confirms a fresh superseding publication; the bot fences the old attempt, performs the approved repair and verifies the new result. The original unknown outcome stays recorded. |
| Partial UPDATE_ALL2 reporting | Resume reporting from the committed import receipt without claiming or importing the file again. Retain completed phase receipts; prove interruption and repeated confirmation cannot duplicate non-idempotent report effects. |
| Whole-pipeline continuation | Persist and resume outstanding cache, maintenance, configuration and export stages. Pre-request failures also create incidents. Missing historical inputs have guided collection/validation and an explicit disposition; admins do not construct commands or queries. |
| Lost containment or registration history | Identify unavailable proof before dependent work fails. Guide verification and a safe superseding repair; never manufacture original proof or discard uncertainty to release ownership. |
| Unattributed held access | Proactively surface the hold, guide the required ownership checks, then execute and independently verify the permitted disposition. Unproven live ownership remains protected and visibly unresolved. |
| Rollover completion | A single integrated test chain drives actual admin callbacks, authority journal, disposable SQL and worker through final independent verification. Cover restart, concurrent/stale confirmation and interruption at each effect boundary. |

## Immediate release blockers

- `deploy/k98-release.json` still describes the earlier October 13 release, not
  this recovery stack. Twelve additional SQL migration files are in the candidate
  SQL delta from its locally known main; compatibility/install qualification remains.
- The four historical application-source pin mismatches have been traced and
  corrected in the candidate (details below). Exact-diff review and installation
  contract/updater qualification remain release gates; source pins alone do not
  approve the installed database.
- The pilot exposure matrix, final release-candidate suite and updater/rollback
  rehearsal have not yet been completed. No maintenance window is requested yet.

## SQL source-pin qualification

The read-only audit compared all 560 pinned source blobs with candidate SQL
`71c6cedcdc317b49df5a312a938759c5a6183a93` and SQL baseline
`b3480656e3454fbe713905460177f8d038c2bd5f`. Exactly four differed from the Bot
manifest; all four have identical bytes at the SQL baseline and candidate.
Each stale pin is exactly the blob immediately before the change identified below;
each replacement is exactly that change's postimage, unchanged through candidate SQL.

| Object | Historical change | Stale SHA256 | Candidate SHA256 |
| --- | --- | --- | --- |
| `dbo.ARCHIVE_IMPORT_STAGING_FILE` | `1159e82456761080eefe18a7a914190b70ecafce` | `aa3b5e4f14e6f84d0de7c48179a0c7a573ca93eb46bf35350bfefe30fbe1fced` | `80ded675c44eb406569f62ef68666646d530582365a3dde7742ad242633b086d` |
| `dbo.CLAIM_KS4_IMPORT_FILE` | `1159e82456761080eefe18a7a914190b70ecafce` | `ee46075e0ce2ba4bc5de5201d108acee1bd817090cb852fe902400ce3561f2df` | `56fa3718d947206b71dfc556d47c2af6a1ab5aa91094e67ea635c584375404ea` |
| `dbo.IMPORT_STAGING_PROC_CORE` | `1159e82456761080eefe18a7a914190b70ecafce` | `df01cd3699b3e9f056ab60bd28e276d081ecd6c62ba57ba17d133e1460411898` | `70143750800457202f79c00174bc0a367e026837ef84041e7053635b72d37d24` |
| `dbo.ExportAttemptPart` | `0cc5f529fa462ec95b68a3d9af1ee1606d70215a` | `8174bd0df3f4914cfb98e4164ab4d0c20494175069d00a09a0edc201dbb6f699` | `888068ce8c2e5796dd0767aaf8985f98e102816b2f1d3f1e6ed78d85b2ece5d8` |

The three procedures replace eleven `xp_fileexist` calls with scalar
`sys.dm_os_file_exists` checks, preserving file identity, ownership, hash checks,
locking and transactions. The table constraint permits `public_editor` only for
legacy `output` parts; it does not make index/generation parts public editors.
The SQL migrations and historical signing/permission profile pins are unchanged.
This Bot patch does not run those migrations or accept live SQL metadata.

Complete offline regeneration of the activation scope succeeds against the exact
candidate SQL commit after these four corrections. Roots and admitted objects are
unchanged. The existing conservative matcher also restores three reference edges:
`StatsImportExecution -> STATS`, `usp_S11RunStatsImport -> STATS`, and
`usp_ExportJobContainTargets -> TARGETS`. These arise from unqualified text
matches (including a filename literal, lock resource, and table variable), not
new SQL dependencies. Keeping them matches the generator's documented conservative
contract. The saved scope equals its complete regenerated output.

## Release packaging and pilot exposure findings

The combined updater consumes explicit `migrations/<id>.release.json` profiles,
not arbitrary `.sql` migration files. The SQL candidate currently contains only
the October 13 reader-history profile. Its module and additive-table profiles
do not automatically support this recovery stack's table alterations, new modules,
and ordered dependencies. Updating the descriptor with SQL-file hashes would be
incorrect. P0a needs an explicitly reviewed, tested deployment path for the exact
twelve recovery migrations, including interrupted apply/verification and receipt
handling. This is a P0a blocker, not a P0b deferral.

The current runtime composes ten recovery adapter kinds, with no P0a-specific
action filter. In addition to the initial three pilot families, it exposes
`stats_import`, `all_kvk_capture`, `player_report`, `export_job`,
`export_rollover`, and `private_evidence` workflows. The three pilot families
use `configuration_read`, `producer_refusal`, `configuration_producer`, and
`configuration_continuation` (ten kinds in total). Therefore the three-family
description above is a proposed acceptance boundary, not an assertion that the
current candidate already enforces it. Before release, each reachable action must
either receive complete P0a acceptance evidence or be withheld consistently at
presentation and execution while retaining honest discovery and open incidents.
In-flight action reconciliation must remain safe across any release gating.

## Initial pilot acceptance evidence map

Existing tests are evidence for individual slices, not a claim that release
packaging or the complete final candidate has already passed.

| Pilot behavior | Existing focused evidence | Remaining release check |
| --- | --- | --- |
| Verified abandoned read automatically releases; unknown writes never do | `test_config_recovery_guided.py`, `test_config_preparation_recovery_sql.py` | Rehearse notification-to-settlement on the packaged candidate and verify exact ownership after restart. |
| Explicitly confirmed unstarted/read-only containment | `test_config_read_containment_sql.py`, `test_config_unstarted_read_sql.py` | Confirm explanation distinguishes fenced/discarded reads from positively terminated children. |
| Writer refusal before execution links its blocker and retains inputs | `test_producer_admission_recovery_sql.py`, `test_admission_decisions_sql.py`, `test_replacement_admission_sql.py` | Prove every enabled blocker link reaches a qualified action or clearly identifies the P0b boundary. |
| Atomic configuration rollback or committed capture | `test_configuration_producer_recovery_sql.py`, `test_configuration_targets_contract_sql.py` | Qualify exact migration/install contracts and representative publication data; synthetic nested-callee tests alone do not prove business output. |
| Fresh configuration publication or keep-prior decision | `test_configuration_continuation_sql.py`, `test_recovery_review_view.py` | Verify the full displayed path through capture/export settlement, including changed registration and lost reply, on the packaged candidate. |
| Proactive alerts and persistent private admin controls | `test_recovery_notifications.py`, `test_recovery_review_view.py`, `test_recovery_input_view.py` | Exercise the deployed admin channel after maintenance; record alert usefulness and clarity without exposing private targets publicly. |

The deployment handoff must identify exact approved commits/package checksums,
explicit migration order, expected success/degraded messages, safe interruption
instructions and the feedback cases to run. It must give the operator executable
steps; it must not require the operator to design release manifests or repair SQL.

## Source-pin correction validation

The 350 existing activation-scope, runtime-composition and log-isolation tests
passed. Architecture (203 Python files), deferred-item validation, security routing,
test selection, Ruff, Black, whitespace, synthetic imports and command registration
(36 primary commands / 102 grouped subcommands) passed. The read-only SQL
file-visibility validator verified all three exact migration/source postimages and
the inverse proof of precisely eleven existence-check replacements.

Changes scan `bfec7228-67dc-4f4e-a146-191ff26a7eb7` reviewed the frozen working-tree
patch against `34cdb5c5`, subsequently committed unchanged as the three source files
in `c66b0d81`. All three source files have complete coverage and no findings; the
scan completed, sealed and was read back at `2026-10-16T07:59:57.442351Z`.
Tool-reported scan usage: 1,692,981 tokens. Release documentation added after that
scan changes no runtime, permission, input, deployment execution or persistence
behavior and needs no additional Changes scan. It does not certify deployment.
