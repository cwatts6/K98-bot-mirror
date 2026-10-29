# Native qualification and review closeout

This supplement supersedes earlier NOT RUN statements only for the cases explicitly recorded below. Source promotion is authorized. Production deployment is still blocked.

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
