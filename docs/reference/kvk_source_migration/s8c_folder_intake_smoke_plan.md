# S8C local-folder intake and SQL smoke plan

For the operator walkthrough, follow the [step-by-step work instruction](s8c_operator_work_instruction.md).
This plan is the technical execution scope, not the instructions you need to carry out.

## Approval and execution boundary

The operator approved testing and requested an alternative to a test bot on 2026-09-13.
Use a local-folder/console transport over the real intake services and real disposable SQL.
No test bot is required. This document replaces the proposed isolated-bot requirement in the
closeout smoke plan; it does not claim Discord transport testing. Execution results are recorded in [the smoke evidence](s8c_folder_intake_smoke_evidence.md).
Local SQL guidance requires an explicitly named disposable database for each slice; the operator explicitly approved the exact
new targets below before execution. General testing approval is retained and is not reopened.

| Purpose | Approved exact target |
|---|---|
| Local SQL instance | `9SX2VF4\K98DEV` (Windows authentication, local shared-memory connection) |
| New primary database | `K98_S8C_Disposable_20260913_intake` |
| New restore-verification database | `K98_S8C_Disposable_20260913_intake_restore` |
| Local working root | `C:/K98-S8C-Smoke/20260913` |
| Inbox / retained originals / transcripts | `inbox/`, `artifacts/`, `evidence/` beneath that root |
| Backup directory | `backups/` beneath that root; SQL service access must be verified before backup |

Stop if either database or evidence output already exists; retain it and choose another explicitly
approved target. Do not overwrite/rebuild/drop existing databases or files. Do not alter production
connections, environment files, service accounts, running bot configuration, recovery or routing.
An instance start, if needed, is a separate operation; do not restart any existing process.

## Transport and real code path

A small local Python console adapter will represent a message using an explicit one-file or two-file
selection, synthetic message/attachment IDs and a labelled synthetic actor/guild/channel context.
The folder is an inbox, not an unattended import watcher. Scanning a directory never implies consent
to accept or pair files. The adapter reads XLSX bytes, then calls the existing production classes:

- `SourceAdminService` / `SourceAdminDAL` for original retention, metadata, baseline, configuration,
  receipt confirmation, cancellation and resume.
- `SourceAdminReviewService` / `SourceAdminReviewDAL` for season/source review and matched-update
  preparation, confirmation, cancellation and readback, using the S8B service contracts internally.
- `ArtifactStore` rooted only in the smoke directory and an injected connection factory that verifies
  actual SQL server/database on every connection before allowing mutations.

The console displays the real service summaries and requests season, actual UTC scan start,
kind/scope, aggregate coverage/as-of/state and audit reason. It displays durable receipt/review/
UpdateID and version before explicit confirmation. Counterpart reuse requires a separate explicit
synthetic attestation or an actual console operator confirmation; never record an automatic choice
as Chris Watts's approval or as live Discord membership validation.

Do not drive intake by manually inserting SourceImportAttempt, SourceUpdate or complete selection
rows in SSMS. Those rows are outcomes of the tested services. SQL prompts/readback are useful for
inspection, not substitutes for invoking the intake path.

## SQL setup and checks

1. Read-only target preflight: server identity/version, database nonexistence, service availability,
   default data/log locations and SQL-service backup-directory access. Record results before writes.
2. Prepare a fresh synthetic prerequisite schema with an exact reviewed dependency manifest. Prefer
   installation into the new target; if a retained synthetic backup is needed, identify its exact
   file/hash and authorize read-only use before restore. No production data or credentials. Do not
   execute all pending migrations or any predecessor validation pack automatically. The executed dependency manifest and prerequisite-only backup/restore proof are retained in the evidence.
3. Back up the prerequisite-only primary database, verify the backup, and actually restore it into
   the new restore-verification target with unique data/log paths and no REPLACE. Verify readback.
4. Run the 13-check text-only contract validator. Apply exactly the S8C additive migration to the
   new primary database, capture object/constraint/index readback, then rerun and prove no duplicate
   object creation or retained-row mutation. The deployment-runner/history path, if used, needs its
   own explicit reviewed command; direct apply must not be described as runner-history validation.
5. Run `validation/kvk_source/s8c_admin_reviews.sql` in its own approved session. It proves generated
   review sequence, cancellation, stale-version rejection and rollback. It must leave no fixture row.
6. Run only the five S8C opt-in cases in `tests/test_kvk_source_sql_integration.py`, with process-only
   KVK_S8C_SQL_ENABLE=1, KVK_S8C_SQL_SERVER, KVK_S8C_SQL_DATABASE and exact
   KVK_S8C_SQL_APPROVED_TARGET=`server|database`. Keep S8B opt-in disabled. Cases reject invalid state,
   empty owner, malformed JSON, oversized payload and invalid expiry. These tests do not prove the
   end-to-end intake journey or live two-connection concurrency by themselves.

Reviewed S8C SQL files at packet preparation (SHA256 of actual file bytes):

| SQL path | SHA256 |
|---|---|
| `migrations/20260913_002_kvk_source_admin_reviews.sql` | `d9ef15e2dfd474533d200a1d51a1f25fa170acd62a159169153cda775cc691e1` |
| `validation/kvk_source/s8c_admin_reviews.sql` | `7e6cad570da30c1cb1754724c2815fb29992e4c23e8641cd4eb06c8993cd27d0` |
| `deploy/Test-KvkSourceAdminReviewContracts.ps1` | `fa91786d880ea8228a3ef7078326ff6a5daa2ab93325b7daf24f4ec298c2389c` |

## Folder-based smoke scenarios

Use generated synthetic player and kingdom/camp aggregate XLSX workbooks, and explicit synthetic
kvk_list-equivalent setup. Feed configuration through the real retained snapshot hook where possible.
The current kvk_list importer fetches Google Sheets; do not invoke it against its configured provider.
If synthetic fixture rows supply its output tables instead, label that clearly: this smoke then tests
configuration consumption/snapshot behavior, not a real Google kvk_list import.

| Case | Required observed result |
|---|---|
| Missing fixed source | Upload rejected before any retained workbook/receipt insert |
| Missing map/weights | Baseline acceptance blocked; retained receipt can be cancelled/resumed |
| Source/season review | Explicit fixed source; season override before intake; no later season switch |
| Baseline | Confirm metadata and setup, accept B0 through the real service |
| One file then counterpart | First input remains private/waiting; later explicit pairing uses durable identity |
| Both files together / reverse order | Same domain result without pairing by arrival order |
| Grouped attachment equivalent | Same service calls/parameters; label command transport as simulated |
| Pair confirmation | Exact revisions/config/roster/coverage and UpdateID; no partial complete selection |
| Retry and fresh process | Same durable result, semantic deduplication, no new scan for re-export |
| Wrong synthetic actor/scope/version | Permission/CAS rejection, no unauthorized state change |
| Cancel before baseline / after partial intake | No accepted-state deletion; receipts/originals retained |
| Valid unused scans | Intake alone does not assign a fighting window or trigger calculation |
| Later window assignment | Retained scans can become exact endpoints within the same season |
| Endpoint/config correction | Exact endpoint chain; prior result remains previous/pending until eligible pair |
| Counterpart reuse | Explicit contextual attestation required; absent/stale authority rejected |
| Post-use map/camp/weights change | Reviewed version used by next eligible calculation; supplied aggregate DKP/totals remain authoritative |
| No-fight / overall | Domain exceptions and independent overall preserved |

The scenario table is a coverage plan, not a blanket pass claim. Executed scripts, numeric assertions,
failures, successful resumptions and remaining coverage limits are recorded in the linked evidence. Initial smoke can expose
implementation bugs: fix only the approved S8C flow, retain failed evidence, rerun affected cases and
record the actual final code revision. Do not silently include S9A or export-worker implementation.

## Evidence and limits

Retain input hashes, service transcripts, synthetic identities/attestations, SQL receipts/revisions/
UpdateIDs/complete selections, pre/post counts, backup and restore proof, test output, final source
hashes, failures and successful reruns. Disable any export/provider adapters and worker startup;
complete SQL publication/intent creation is not a provider export. No real external workbook is
needed initially, and no new file is deleted automatically when the run finishes.

This proves the exercised real parser/service/DAL/SQL journey through a simulated local transport.
It does not prove Discord uploads, slash-command registration, modal rendering, live role lookup,
message permissions, network timing or a full bot restart. Existing mocked interaction tests are
separate evidence; eventual live Discord smoke remains an explicit outstanding operational check.
S8B 50-case/actual-restore evidence, S8A six-script evidence, and S6 open gates remain unchanged.

## Pending delivery

This is an additional Bot documentation carry-forward path in the S8C closeout. The console adapter, offline boundary tests and evidence summary are now included in that exact
manifest. All pending Bot and two SQL documentation changes remain preserved, uncommitted and
unstaged. Executed SQL/testing authority is limited to the named disposable targets; no Git publication,
production deployment or S9A implementation occurred.
