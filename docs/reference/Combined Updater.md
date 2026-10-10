# Normal combined Bot and SQL updater

The installed `Update-K98.ps1` can prepare source-only releases or a bounded
combined release from private `K98-bot/main`. It preserves the installed startup
contracts, activation flags and held work. This change does not deploy or restart
the live Bot, repeat the completed 10 October 2026 release, or complete broader S11
business-failure acceptance.

## Reviewed inputs and supported profile

A changed `deploy/k98-release.json` in the reviewed Bot target selects SQL. An
unchanged description means a source-only update. Removing a description is
refused. The containing Bot commit is the target; `bot_predecessors` lists exact
permitted private production predecessor commits, not mirror commits.

```json
{
  "version": 1,
  "profile": "module_grants_v1",
  "bot_predecessors": ["<40 lowercase hexadecimal characters>"],
  "sql_commit": "<40 lowercase hexadecimal characters>",
  "migrations": [
    {"id": "20261010_901_example", "sha256": "<SHA256 of exact profile bytes>"}
  ]
}
```

The SQL commit must be on reviewed SQL main. Its exact runner, ordered profiles
and module files are acquired into a separate protected Git database and sealed
into the release package. SQL main is never selected independently of this pin.
Each profile lives at `migrations/<id>.release.json`; the SQL repository's
`docs/module-release.md` defines its format. No operational release description
or migration is added by the updater implementation itself.

Descriptor-only pull requests trigger updater CI. The metadata check validates
the actual descriptor's shape, exact commit/hash fields and explicit migration
order. Installed-predecessor compatibility, private SQL acquisition and live SQL
preconditions remain preparation checks before drain; CI does not claim those
production observations.

The first profile supports existing unsigned ordinary stored procedures/views and
explicit new object EXECUTE/SELECT grants. It refuses sealed startup objects or
principals, whole-database startup contracts, schema/data migrations, identities,
dependencies/configuration changes, SQL Agent jobs, file/external effects, CLR,
encrypted modules, DDL triggers and ledger triggers. Profiles cannot modify the
same module or grant twice in a release. Required migration history must already
exist before drain; intra-release predecessor dependencies are not supported.
Unsupported changes need a separately reviewed release design before deployment.

## Operator sequence

1. Install the reviewed stable updater package using its generated
   `Upgrade-K98InstalledUpdater.ps1`. The package binds the actual previous
   `update-tool.json`, installer and new tool manifest. It refuses an active
   release or unexpected installed bytes; it archives the prior tool and retains
   all evidence. Do not substitute a guessed previous manifest.
2. On MINI_AMD, use Windows PowerShell 5.1, Run as administrator under the existing
   deployment account. Run the protected installed `Update-K98.ps1 -PrepareOnly`.
   This acquires and validates exact files, source custody, installed dependencies,
   full startup SQL comparators, module preimages, database/tempdb collations,
   compatibility level and backups before requesting drain. No drain is requested
   by PrepareOnly. Inspect the named transcript and selected revisions.
3. Run the same `Update-K98.ps1` and follow its existing Discord drain/restart
   instruction. The coordinated runner applies SQL in explicit order, source,
   successor seed, one start, readiness, then atomic outer closeout.
4. After any interruption, run `Update-K98.ps1 -Status`, retain its evidence paths
   and the update transcript, then rerun the same updater only as indicated.
   Do not manually restart, remove receipts, change hashes or replay SQL.

No new force switch, arbitrary SQL command, manual receipt editor or bespoke
release launcher is part of this workflow. Production always deploys private
`K98-bot/main`; Bot mirror and SQL histories remain separate.

## Status and recovery

| Evidence | Meaning and next action |
| --- | --- |
| Unstarted, exact preconditions | Continue the same reviewed release through drain. |
| SQL `rolled_back`, exclusive owner lock acquired, exact preimages | The same release may apply again; earlier attempts remain recorded. |
| SQL `committed`, exact Applied receipt and postimages | Verify and continue later stages; SQL is not applied again. |
| Live SQL owner, unknown outcome, drift or Failed migration identity | Stop; retain transcript, profile, expected/observed hashes and history. Review the named discrepancy; do not force or reuse a corrective identity. |
| Source target committed, exact permitted checkout bytes, unchanged index and same drain intent | Complete exact byte installation and index reconciliation. Unknown/interrupted Git state before target commit requires review. |
| Partial seed, exact existing members, empty successor history, disabled expected task | Install missing members and complete task binding. Torn or unknown members require review. |
| Start intent without verified native successor | Stop for native/task/session evidence review. Never request a second start automatically. |
| Readiness pending after verified start | Repeat the bounded read-only readiness wait. |
| All stages verified, outer bookkeeping pending | Publish closeout atomically; do not run SQL/source/start verifiers again. |
| `VERIFIED_HISTORICAL` | Deployment completed at its recorded readiness time. This is not a fresh health or process-liveness claim. |

Status performs protected reads and SQL observations without starting a transcript,
creating receipts, applying source/SQL, altering tasks or starting processes. A
concurrent change can make status inconclusive; it is not an atomic live snapshot.
Resume holds the operator lock. Timing fields measure updater stages, not business
export or Google Sheets latency.

## Validation and retained scope

Run Python updater/release tests, Windows PowerShell orchestration/source/upgrade
tests, `Test-K98CombinedUpdate.ps1`, and the SQL profile tests. The SQL repository
provides an isolated K98DEV rehearsal of the actual Windows 5.1 outer runner and
SqlClient: differing database/tempdb collation, exact Unicode/LF definitions,
rollback retention, process death before/after commit, lock contention and drift.
Native administrative custody additionally needs the elevated development-PC
rehearsal. Substituted external task/process tests must not be described as a live
production deployment rehearsal.

Keep separate: business failure/restart acceptance and admin-resolution runbook
coverage; busy/not-probed versus provider-failure wording; business stage latency;
old persistent-view rehydration; reminder temporary-file races; disabled-DM retry
handling. Preserve the existing separation between player statistics and optional
Sheets outcomes. Their detailed prior captures remain in the S11 handover.
