> **Archived at E104, 6 November 2026.** P01.6 is closed for its agreed scope. See [accepted closeout](Startup%20Import%20Export%20Reliability%20-%20P01.6%20Closeout%20-%202026-11-06.md) and [active P02 handover](Startup%20Import%20Export%20Reliability%20-%20P02%20Handover%20and%20Scope%20-%202026-11-06.md). Dated approvals, candidate status and commands below are historical evidence, not instructions to replay deployment or recovery.

# P01.6 Bot and SQL release: review, deployment and validation

6 November 2026. The operator approved PR preparation, review fixes, publication and merge of the Bot mirror/private promotion and SQL companion. Production deployment remains separate. The final handoff binds the merged revisions and package hashes; this plan does not claim that merging installed anything.

## Scope and review verdict

The Bot owns personal Stats SQL/registry/render work until physical cleanup, bounds admission, revalidates account access before private delivery and exposes passive diagnostics. The SQL companion preserves the public contract while rewriting daily source selection and adding one covering index. No new command, dependency, runtime configuration, ProcConfig entry, data backfill or provider replay is required. Existing P01.4/P01.5 acceptance and natural follow-ups remain unchanged. The retained E100 documentation and archive moves are deliberately carried forward.

Local source and native qualification passed. The [qualification record](Startup%20Import%20Export%20Reliability%20-%20P01.6%20Implementation%20and%20Qualification%20-%202026-11-05.md) contains exact full-suite, cost, adverse-run, SQL correctness/performance, permissions and migration evidence. Bot Changes review `30a1cf81-74c7-4416-a21e-76f2c3d5f8ce` and SQL Changes review `05b7ec1a-55e6-4b28-a68b-b37ddd30734a` found no issues. Hosted review then found and corrected Windows CRLF normalization in both migration guards, first-use Stats admission during shutdown, and an uninitialized passive status classification. SQL install/repeat/rollback/repeat now passes with LF and CRLF; all 24 engine cases pass. The Bot corrections pass 142 focused lifecycle, health and updater-transition checks. Final SQL Changes review `1349af3a-12f0-49b6-8560-3f7367313f5f` covers the corrected migration range with zero findings. Its subsequent test-only UTF-8 decode and fixture-description correction received a documented manual-review skip. Final private Bot review and publication checks bind the reviewed fixes to committed heads in the release handoff.

Final review checks the changed callers, shared drain helper, cancellation before/after worker entry, uncertain cleanup, same-key ownership/cache publication, final authorization for images/fallbacks/controls, repeated teardown, updater pins and SQL result/permission contracts. The hosted findings above were corrected before merge; remaining blockers are recorded in the final handoff. Reused helpers are core.owned_work, operation evidence and the existing SQL lifecycle session; their broader relocation and shared connection policy remain deferred. There is no SQL in command/view modules or new critical durable state.

## Release identities and distinct gates

| Item | Bound predecessor / target rule |
| --- | --- |
| Bot mirror source | `codex/p016-owned-personal-stats`, based on mirror `7e430a624a3fecd38360e4cd31f56ec1ef9e3966` |
| Private Bot predecessor | Last accepted installed source `24bca82f0a23721c1428bfe4f0db2e120d5b7c34`; confirm actual host before execution |
| Private Bot target | Exact reviewed private-main merge in final handoff; promoted file delta only, never mirror history |
| SQL predecessor | `b1eeb8e894fec380c7a6d6c5cc5bbfd9dbc3470c`; installed procedure/index admission is checked separately |
| SQL target | Exact SQL-main merge in final handoff; apply only migration `20261106_001_personal_stats_daily_read_plan` |
| SQL rollback | `migrations/rollback/20261106_001_personal_stats_daily_read_plan_rollback.sql` at the same reviewed SQL target |

Record source qualification, actual-host custody/preflight, installed source/startup and observed feature acceptance separately. Fresh host custody is required for every changed path and existing ancestor, including documentation/archive directories; historical P01.5 repairs and a clean Git tree are not substitutes. Inspect owner SID, DACL/inheritance, ordinary attributes, reparse/link/stream state and exact bytes using the Windows ownership contract. Do not run PrepareOnly as a supposedly read-only inventory: it can create protected packages.

The local LPIM trial applies only to development K98DEV. This release does not change production SQL memory policy or authorize copying that host setting. The local Windows paging trigger remains unknown; production performance must be observed independently.

## Deployment order

1. Verify final merged private Bot/SQL revisions and package hashes against the handoff. Confirm the actual installed Bot/updater identity and fresh custody inventory. Stop on drift or unresolved updater intent. Keep all previous receipts and uncertain work. Check backup readiness and an appropriate quiet SQL maintenance window; index creation can block readers/writers and consumes storage/log space. Do not manufacture production load to reproduce the local stall.
2. On the development/release preparation side, validate predecessor-to-target source compatibility with the actual installed tool manifest. P01.6 changes the registered updater family: use the exact predecessor-bound updater upgrade from the final package if the old tool reports `UPDATER_UPGRADE_REQUIRED`. Upgrading the updater does not install Bot source or SQL. A source-compatible package does not by itself prove host custody.
3. From the reviewed SQL checkout on its merged main, explicitly bind `MINI_AMD` / `ROK_TRACKER`, confirm the known stored-procedure predecessor, current indexes, permissions and any module signatures. Stop if the procedure is signed and a reviewed signature-preservation/re-signing step is absent. Retain backup and before-state evidence. Run only the named migration below through the existing runner. Its `ValidationOnly` mode writes deployment history and is not a read-only production probe.

   ```powershell
   .\deploy\Deploy-SqlMigration.ps1 -ServerName 'MINI_AMD' -DatabaseName 'ROK_TRACKER' -MigrationId '20261106_001_personal_stats_daily_read_plan'
   ```

   Do not use batch mode, skip backup checks, override the main-branch gate or install schema exports directly. This SQL-only step is backward compatible with the currently installed Bot. The new index and procedure alter are transactional; drift is refused. A lost acknowledgement requires inspection of the procedure/index and migration receipt before deciding whether any step remains.
4. Verify the installed procedure body and index keys/includes against the reviewed SQL target, retained grants, migration receipt and read-only results for legitimate representative accounts under the application principal. Confirm no unexpected lock/grant wait or import impact. If SQL validation fails, stop before changing Bot source; use the SQL rollback decision below.
5. On MINI_AMD use elevated **Windows PowerShell 5.1**, the reviewed deployment account and the exact updater upgrade package where required. After successful preflight/upgrade, run the fixed updater with `-PrepareOnly`, confirm its selected private-main target matches the handoff, then run it normally:

   ```powershell
   & 'C:\ProgramData\K98\S11\updater\Update-K98.ps1' -PrepareOnly
   & 'C:\ProgramData\K98\S11\updater\Update-K98.ps1'
   ```

   Run `/ops graceful_restart` once only when prompted. The updater owns drain, source/startup-policy installation, single successor startup and verification. No live Git pull, format/test run, manual task start or additional restart. Stop if private main has advanced to an unreviewed target.
6. Complete the validation table below and retain receipts. Startup success alone does not close feature acceptance or whole-flow import/export health. Do not replay accepted earlier operations.

## Validation and stop conditions

| Check | Expected result | Stop / investigate |
| --- | --- | --- |
| SQL installation | Exact procedure and index; unchanged grants; successful migration receipt | Unknown DDL outcome, drift, missing signature/grant, excessive blocking or resource pressure |
| Protected Bot deployment | Exact private merge, successful source/policy/startup and one successor | Wrong revision, failed drain, incomplete phase, startup failure |
| Existing surface | `/ops show_command_versions`, Health and normal existing Stats entry work | Missing commands, import errors, interaction exceptions |
| Stats results | Single/multiple linked accounts and normal periods retain metrics, data freshness and privacy; compare one legitimate sample with prior expected data | Wrong account/period, changed metrics, duplicate delivery, missing source rows |
| Normal controls | Mode/period/scope/picker and accessible fallback behave normally with current authorization | Stale controls or private data delivered after access changes |
| Passive diagnostics | Personal Stats counts/outcomes explain capacity and cleanup; existing evidence ZIP includes bounded redacted details | Cleanup uncertainty treated as healthy, owner released early, sensitive payload leakage |
| Normal demand | Useful reports complete without recurring unexplained nine-second failures; observe ordinary concurrent use | Sustained unavailable responses, query-memory waits or import/write regression |
| Shutdown | Next legitimate restart retains/drains actual work and records settlement | Unconfirmed cleanup or duplicate successor; do not force release |

Use local qualification for deliberately blocked SQL, cancellation races, invalid inputs and denial/fault injection. Do not remove real account access, generate overload or induce database failures merely to reproduce these tests in production. Busy/unavailable is an intentional bounded outcome; cleanup uncertainty must stop new Stats admission. Unknown import/export health stays unknown rather than triggering automatic probes/replays.

## Rollback and interruption

- **Before SQL commit:** a script failure rolls back its DDL. Verify actual object state and transaction/receipt evidence; do not infer rollback from an error message alone.
- **After SQL commit, before Bot change:** the old Bot remains compatible. If the SQL change is implicated, stop the rollout and apply the exact reviewed rollback script to the explicitly verified target during a quiet window, using the approved SQL execution path. It restores the previous procedure and removes only `IX_KS4_Governor_DayEnd`; no table rows are restored or deleted. Revalidate results, privileges and source definitions. Reconcile migration/deployment history truthfully before any future reapply; do not delete an Applied receipt to force the runner.
- **After Bot deployment:** preserve diagnostics and first establish which updater stages completed. The same command can resume a known retained intent according to its receipts; it must not replay committed stages or issue another start after an unknown acknowledgement. SQL rollback is result-compatible with the new Bot but restores prior query performance, so retain the read bounds and stop on renewed failures.
- **Bot rollback:** do not reset/pull an older live checkout or reuse the forward package backwards. Restoring predecessor source requires an exact reviewed private target, authenticated reverse transition/startup policy and settled ownership. Prefer a reviewed focused forward correction when practical. The final forward handoff is not a tested automatic Bot downgrade package; this limitation is explicit.
- Local K98DEV LPIM rollback is separate and never part of a production SQL/Bot rollback. No production memory-policy change is included.

## Remaining acceptance

The synthetic index benefit has a measured cost: about 15.2 MiB for 134,715 rows and approximately 18% insert latency / 10% extra log bytes in rolled-back trials. The eight-worker control showed progress but no throughput gain. Representative production read/write cost remains open. P01.4/P01.5 natural observations, P02 shared connection/contention work, P03 retained continuation, P04 convergence and P05 wider confirmation retain their owners.

Follow the [Promotion Guide](../../reference/Promotion%20Guide.md) and [Windows ownership contract](../../reference/Windows%20ownership%20and%20access%20contract.md). Final hosted checks, review disposition, merge identities, updater package evidence and actual-host readiness are recorded in the release handoff; do not interpret an unfilled gate as permission to bypass it.
