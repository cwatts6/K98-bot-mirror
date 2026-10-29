# Native qualification and review closeout

This supplement supersedes earlier NOT RUN statements only for the cases explicitly recorded below. Source promotion is authorized. Production deployment is still blocked.

## Subsequent qualification closeout

The separately approved results-import correction returns `OUTPUT INSERTED.ImportId`
from the INSERT execution and raises inside the transaction if no ID is returned.
The updater transition now binds this exact DAL as its 21st member; the original
51 historical transitions remain unchanged. Mirror PR 461 owns this correction.

At 15:01 UTC on 29 October, the bounded continuation passed **N14–N16** with Bot
`f27f373f8e94389dda3f72fc97a3ff4fa1128630` and SQL
`ec336f0d6af1ce3b48e5a34206ab610163d0680d` against the same approved retained database.
N14 persisted and read back import ID 2 and one final result on completed event 1.
N15 preserved previously committed signup/award/completion work while a later award
delete was rejected with SQL 51830; it does not claim whole-operation atomicity.
N16 traversed 63 eligible events in two pages without duplicates. Its synthetic
timings are observations, not a production performance claim.

The original N00–N13 results, failed N14, source bindings, applied release identity
and migration receipt are retained unchanged. The continuation used Verify only:
no migration replay, database recreation, restore, cleanup or child termination.
The earlier exact backup also passed `RESTORE VERIFYONLY WITH CHECKSUM` at
14:18:55 UTC; no database was restored. This supersedes the earlier unverified-backup
statement below.

SQL PR 135 additionally binds the durable continuation claim to the canonical
retained evidence directory, refusing copied evidence before effects. Its guard-only
correction `3235beb253cbefc3e78fcf4121b4b60bf729af02` has 24 passing offline tests;
the successful native cases were not replayed. The original full continuation
Changes review and the incremental guard review are complete with zero findings.
Bot's results-import/updater Changes review likewise completed with zero findings.
The deferred identity-return item below is historical and closed by this correction.

Approved RDP inspection retained the actual installed updater manifest, release
manifest and 09:08 observation. That observation records `ROK_TRACKER` database
collation `Latin1_General_CI_AS`, tempdb collation `SQL_Latin1_General_CP1_CI_AS`,
and compatibility 160. These are dated installed observations, not a fresh SQL
inventory. Current migration history, permissions, backup and protected member
custody still need verification before release metadata is bound.

Protected Windows U05–U13 remain unqualified. The development execution token is
not elevated; file-access approval does not confer Windows administrator rights.
No production updater installation, preparation, SQL write, source update or
restart was performed. Source merges remain distinct from deployment readiness.

## Native SQL run

The operator separately approved creation and synthetic writes to the single disposable database `K98_MGE_Finalisation_Qualification_20261029_A` on the development SQL instance, with its exact data/log/backup paths, two-session races and fixture-owned child interruption. Creation metadata, source commits and approval-byte SHA-256 were bound before execution. Fixtures and evidence are retained; production SQL was not touched.

Reviewed source pair: Bot `40dcc0d62c9826b97d4d1532a660cbd149c9548f`, SQL `626a1811060f40ad02a74b9030336b29097863db`. SQL source is identical to merged SQL PR 134 (`fe0cbbc2107dfc62e8f13568e3404ce4203f2310`).

- **N00–N13 PASS**: identity guards, native SqlClient installation and receipts, four interrupted-install rollbacks, structural postimage refusals, actual DAL writes, atomic target capture, partial/legacy handling, rollback and client loss, concurrent callers, completed-state guards, stale revision refusal, payload preservation and delivery readback.
- **N14 FAIL**: the existing results-import DAL inserts in one cursor execution and reads `SCOPE_IDENTITY()` in another execution. SQL returns NULL for the identity and conversion raises `TypeError`. Independent readback found no import row or final-results row; event completion and the applied migration receipt remain intact. No blind replay occurred.
- **N15–N16 NOT RUN**: the harness stops at its first failure. They are not accepted by inference from earlier unit tests.
- SQL backup history records the exact fixture backup with checksums. Direct operating-system readback of that SQL-owned file was denied; no permission change was attempted. Restore verification is not claimed.
- **U05–U13 NOT RUN**: protected Windows/end-to-end rehearsal requires its separate bounded approval. Passing Windows CI does not replace that qualification.

The failing `mge_results_dal.py` Git blob is identical in the installed predecessor and candidate: `9fe938dbbceb6a8f6ed582dfe8e1be33419ffb63`. This is a demonstrated pre-existing defect, not a freeze-trigger regression. Repository testing rules require unrelated failures to be documented without expanding this PR. It remains a release blocker until a focused correction and safely bound continuation/requalification close N14–N16.

### Deferred Optimisation
- Area: MGE-RESULT-IMPORT-IDENTITY; mge/dal/mge_results_dal.py::create_import_batch
- Type: consistency
- Description: Native case N14 reproduces NULL identity retrieval because INSERT and SCOPE_IDENTITY run in separate SQL execution scopes. The failed fixture transaction rolls back. This code is unchanged from the installed predecessor; MGE release qualification remains blocked.
- Suggested Fix: Correct identity return within the inserting execution scope, validate against authoritative dbo.MGE_ResultImports and real pyodbc, add rollback/result-shape regression coverage, then continue N14–N16 only after independently binding the retained fixture and prior durable outcome. Do not recreate, restore or blindly replay the retained database.
- Impact: high
- Risk: medium
- Dependencies: Focused results-import correction; exact native source/target bindings; separate review/security-routing decision. This entry does not waive release acceptance.

## Private PR review corrections

Private PR 706 review identified two in-scope issues. Finalisation now passes the established `admin_view` or `scheduler` origin into the structured completion audit. A regression test observes the emitted record for both callers. The unused `allow_completed` parameter and command argument are removed; completed award-reminder refresh remains explicitly refused by the accepted frozen-history policy.

The exact successor hashes for those three runtime files are refreshed in the existing 20-member MGE transition and historical test bridge. Historical transition entries, bounds, permissions, SQL statements, delivery semantics and frozen-history policy remain unchanged. Rebuild the candidate updater after this correction; earlier installer/manifest/upgrade hashes are historical and must not authorize the revised source.

## Release bindings and confirmation

Approved RDP inspection confirms the installed predecessor reference and latest deployment receipt both select `2c31de42eb91cf6b7f9f61f3aaf3efc3597c4ea6`. The actual installed manifest was copied read-only and used to bind a local authenticated upgrade candidate. This does not independently verify installed member bytes, custody or current SQL metadata.

Complete the remaining native cases, protected rehearsal, production read-only inventory, SQL profile and changed Bot descriptor before presenting a final package/window for updater installation and production preparation/deployment approval. See the [deployment and confirmation plan](P1%20MGE%20Finalisation%20-%20Deployment%20and%20Confirmation%20Plan%20-%202026-10-29.md). A source merge is not deployment readiness or functional acceptance.
