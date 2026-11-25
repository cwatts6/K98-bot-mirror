# S11 G4 — KVK16 overall local publication, 2026-10-02

**Local overall calculation/publication and report validation completed. Real two-export Sheets demonstration remains incomplete.** This supplements the retained 2026-10-01 local import result and 2026-10-02 calculation-preview receipts. It does not replace their seals or convert offline replay into provider acceptance.

Chris selected **overall baseline-to-end** for this demonstration and confirmed the corrected workbook is the final aggregate. Exact 2026-08-26 04:07 UTC → 2026-09-07 07:21 UTC timestamps are retained scan/test bindings; they were not extracted from the aggregate workbook. The response “final aggregate” is retained as such, not rewritten as an independently verified minute-level source timestamp. The Pass 4 window remains separate; no matching Pass 4 aggregate was supplied or invented.

## Completed results

Corrected input: `C:\Users\cwatt\Downloads\KVK16\kdall-stats-26aug4am-to-7sep7am.xlsx`, 13,241 bytes, SHA256 `f45a0a9e0e579a79a7ef1f63d0d0d7ccef603356cf194a6e1d79c0dcbd05e215`. The actual application parser passed with 36 kingdom rows, four camp rows and no diagnostics. Semantic digest: `494ceb041ca8477fd593176f12a80a45d90269f62592a266b003980f8f95890a`. All 320 aggregate metric raw-token/value/status comparisons passed against the generated CSV sections. Abbreviated reported precision is preserved; player sums are not substituted for aggregate facts.

Target remained `localhost\K98DEV`, canonical `9SX2VF4\K98DEV`, **ROK_TRACKER database 24**. A fresh non-overwriting COPY_ONLY/CHECKSUM compressed backup was created at `C:\Program Files\Microsoft SQL Server\MSSQL16.K98DEV\MSSQL\DATA\S11G4_DB24_before_overall_20261002.bak` (31,305,728 bytes). VERIFYONLY/CHECKSUM passed; this is not an actual restore. DB22 and its 119 media files were not accessed or changed.

The source-required `20260913_001_kvk_source_update_no_fight_context.sql` amendment was previewed at zero SourceUpdate rows and then applied in a separate session. Exact source SHA256: `97faf5b82c9b2415db79064c35d747df5a3f0b01463884c6152c05a40e2a248c`. Both stages acknowledged completion. No wholesale application installation or predecessor fixture rerun occurred.

The existing DAL/service path then appended:

| Identity | Value |
|---|---|
| Overall configuration | `33d08912-d5f9-49c8-b558-85485f291978` |
| Overall period | `dfc08aa3-da10-4f93-8ace-dd0909993993` |
| Aggregate report | `3dfb6d25-7e69-4053-99f0-22dd172ac1d7` |
| Aggregate revision | `3954ed7d-de67-45ad-a8f2-8cbe2def3efe` |
| Sealed update | `d60f2a79-cc65-4f45-8a6f-d732b5f6d32e` |
| Selected publication | `07f4ba4e-c69d-5102-be61-ea9f97eff343` |
| Export intent | `209b8561-7de7-480c-b7ef-9199581dedde` |
| Public selection version / commit sequence | 1 / 1, local database identities only |

The update includes explicit period-assignment evidence for the already accepted scans 1 and 3. Original observation metadata and the Baseline/Pass 4 configurations were not rewritten. Weights 10/20/40, frozen B0 and the original mapping were reused. `SourceRouting.Enabled` remained **0**. A selected local publication is not Bot activation or Google publication.

Stored-result validation passed:

- 5,806 eligible B0 players; 5,417 matched; zero missing starts; 389 missing ends; 303 outside-cohort governors excluded.
- All 5,806 persisted player result rows equal a fresh source calculation.
- 70,421 independent counter/DKP arithmetic assertions and 27,085 rank/population assertions passed.
- The immutable export intent reloaded to the exact same twelve section hashes and content key `db5ff926257d2f9231de0f4aa3464e84afa56b0df92f746dd539a16bdbcee238`.
- Full sections contain 5,806 players, 36 kingdoms and four camps. The three windowed sections are empty because this export selects only the overall period. This is expected, not the separate empty-KVK-report issue.

Twelve local CSV projections total 17,170,631 bytes. Spreadsheet formula-leading strings are escaped in CSV; the source export manifest hashes describe the original RAW table values, not the escaped CSV serialization. These are the real source-generated report sections, not the previous in-memory diagnostic preview. No claim of equivalence to a captured production export is made.

## Execution bounds and retained evidence

Evidence root: `C:\Users\cwatt\Documents\Codex\s11-overall-validation-20261002`.

`working` and `sealed` hold separate complete scripts and launchers. The publication script is SHA256 `b85a91b62f6e5113431e194bbf5c94f5f4b7b46265101a128825cb7df70deb8f`; its launcher is `19a908736c68035bb3c5a13a3a59963574f863aefa27110e27281626a1381870`. The result seal binds each other command, receipt, source copy, CSV and document individually. All 549 pinned application source members were checked before application imports.

Commands use the existing protected `C:\K98-S11-Validation\python-env\Scripts\python.exe -I -B <sealed-script>`. Launchers start hidden owned children, preserve stdout/stderr/exit receipts, and refuse existing attempt output. No automatic publication retry occurred.

Installation: 5-second connections; backup/VERIFYONLY command timeout 120 seconds; migration command timeout 30 seconds; 1-second SQL lock timeout and source-defined 10-second application-lock timeout; 240-second cooperative stage bound, 300-second owned-child ceiling. Migration evidence is capped at 100 rows per result. The backup refuses an existing exact path and checks a 2-GiB post-write ceiling; this is not a preallocated hard disk quota. Existing DB24 data/log limits remain unchanged.

Publication: exact server/database ID/original-login guard on each injected connection; no pooling or retry; 5-second connection, 15-second command, 1-second lock timeouts; at most 30,000 SQL calls, 270-second cooperative deadline, 300-second owned-child ceiling. Actual: 6,107 SQL calls in 61.453 seconds, child exit 0. Original aggregate storage is under `C:\K98-S11-Validation\kvk16-overall-20261002-originals`, preserved outside Git. Source transactions acknowledge commit/rollback separately. No hard host memory/output/disk quota is claimed.

Read-only verification used the same connection/time limits: 34 SQL calls, 15.860 seconds, exit 0. Its first harness attempt compared a raw ODBC UUID representation with a canonical lowercase UUID and stopped. The corrected version used the application's canonical row mapper and passed. Both versions/failure receipts remain. No publication was repeated to repair that harness assertion.

On unknown SQL/provider outcomes, preserve state and reconcile exact identities before any continuation. The migration is forward-fix-only; no automatic drop/restore is supplied. The backup is retained recovery material, not permission to overwrite DB24 or any other database. The initial offline parser launch could not access the protected interpreter from the sandbox; the escalated offline invocation succeeded. The standalone offline parser/aggregate-CSV check commands are retained in chat plus sealed Python bodies; they did not use separate pre-dispatch launcher files.

## Provider result and unresolved demonstration

The previous fresh five-file check remains evidence that the selected files were blank, owned by Chris, writable by the existing service account, and public Viewer. It is not silently refreshed or converted into registration evidence here.

One bounded IAM metadata GET targeted only `projects/statsupdate/serviceAccounts/sheets-service@statsupdate.iam.gserviceaccount.com/keys`, requesting user-managed key identity/type/origin/validity/disabled metadata, never key bytes. The same existing credential was used. Google returned HTTP **403**, reason **SERVICE_DISABLED**, identifying project number **283272667859** and `iam.googleapis.com`. This does not establish whether the service account has the necessary IAM read permission once the API is enabled. The child exit 0 records successful capture of the denial, not a successful metadata check.

IAM request budgets: one token refresh invocation and one GET; no GET retries/redirects; 5-second connect and 15-second read timeout, 64-KiB response cap, 300-second owned-child ceiling. TLS certificate/hostname verification used the existing Windows trust store. No Google file, permission, key or API configuration was changed.

**The live two-export demonstration is not complete.** The current S11 authority requires the retained identity/custody and runtime/registration prerequisites. Enabling the API alone would not establish all of them. Remaining facts/decisions include:

1. Current key/IAM metadata from an existing authorized Google Cloud administrator, or enabling the existing IAM API and establishing a permitted bounded reader. No replacement service account, human OAuth or key material is needed.
2. The previously recorded two-host key-custody/writer-coordination interpretation and protected output/reference closure, including uncertain outputs. The statement that only production and this machine hold the key is retained; it is not an observed production drain.
3. Actual export authority/process/configuration and restricted SQL/manual-pool registration evidence. The approved full-source implementation exists; DB24 currently has the report foundations and S8B amendment, not the complete S11 authority installation. Do not substitute the older unrecorded delivery path, an always-true reuse guard, fabricated G4 records or a second Bot to claim completion.

The broad local/demo approval remains valid. Missing facts are not another request to approve the same execution. No production operation, Bot restart, cloud grant, Git publication, G5 activation or broad collector occurred. Seven typed G4 proofs, S6/S8 open gates, both uncertain publications and the shared-account amendment remain open. No runtime source code changed; operational scripts were source-inspected and exercised within these bounds. No new canonical Changes security scan or restricted-principal SQL acceptance is claimed.
