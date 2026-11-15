# Aggregate finalization permission gap — local evidence

## Result and scope

The application grant plan omitted `INSERT` and `SELECT` on
`KVK.SourceKingdomReportRow` and `KVK.SourceCampReportRow`. The importer inserts
these fixed table names inside a loop; the reporting DAL reads them similarly.
The local change adds exactly these four object grants and updates the pinned
application grant-plan hash. It adds no row-table UPDATE, DELETE, schema grant,
role membership or grant option.

The acceptance path now records an opaque correlation reference, transaction
stage, SQL-template fingerprint, exception class, SQLSTATE and numeric native
code. It does not log SQL text, parameters, raw driver messages or workbook
contents. A private Discord error can carry that reference. Nested receipt and
import transactions share one diagnostic scope; existing commit uncertainty,
rollback, authorization, replay and confirmation behavior is retained.

## Evidence

Read-only SSMS inspection of `mini_AMD / ROK_TRACKER` on 12 October 2026 found:

- The affected KVK16 receipt remained `validated`, version 2, with no aggregate
  revision and an expired finalize proposal.
- No aggregate report, aggregate revision, kingdom report rows or camp report
  rows existed for that failed acceptance. This is a bounded observation, not a
  claim about every database table.
- `S11_ExportApplication` had INSERT/SELECT/UPDATE on the aggregate report and
  INSERT/SELECT on its revision, but no direct grant on either row table.
- Its two database roles were `ExportExecutionAuthority` and
  `ExportLegacyEntryReader`. Catalog checks found no relevant inherited row-table,
  KVK-schema or broad database permission, and no server role membership.
- The four aggregate tables had 7/23/40/39 columns respectively, no computed
  columns and no enabled triggers.

The original incident log retained only `ProgrammingError`. Missing grants are a
strongly supported explanation; the historical native error code is unavailable.

All SQL writes for diagnosis were confined to the newly created
`9SX2VF4\K98DEV / K98_Aggregate_Disposable_20261012`. Nineteen dependency-ordered
table definitions and six deferred foreign keys came from the SQL repository at
`d08306c1b4f586cb6393c0b88fef1528a4aabc94`.

The unchanged retained workbook (SHA256
`b053dcbef561cb18d91a936fd1448461ae9b73de5c1f80607eb983a6b6b53ec8`) parsed and saved
all 36 kingdom and 4 camp rows with the real ODBC driver under a local privileged
connection. Its synthetic season and fixture mapping do not assert production
configuration equivalence.

A no-login user in the disposable database received the relevant old grant-plan
subset. Real `SourceAdminDAL.confirm` and its borrowed importer transaction then:

1. Failed on the kingdom row INSERT with `ProgrammingError`, SQLSTATE `42000`,
   native `229`, statement fingerprint `692ef9db459d5921`.
2. After the kingdom grants, failed on the camp row INSERT with the same class
   and codes, fingerprint `fdef5c41530987ab`.
3. After each denial, retained byte-identical receipt provenance and original
   artifact, version 2 and validated status; aggregate counts were all zero and
   only the original draft attempt remained.
4. After applying both tables' corrected plan grants locally, a fresh DAL
   instance accepted the same receipt. Counts were one report, one revision,
   two synthetic kingdom rows, two synthetic camp rows and two attempts (draft
   plus acceptance). Repeated confirmation returned the saved result without
   invoking acceptance again. Restricted SELECT reads of both row tables passed.

Private receipt identifiers, query scripts, workbook probe and reproducible
permission probe are retained locally under the ignored
`.codex_artifacts/aggregate-finalization-20261012/` directory. The disposable DB
and no-login test users remain available for inspection. ODBC pooling was disabled
for the impersonation fixture to prevent impersonated sessions re-entering a pool.

## Validation

- 302 focused tests passed: diagnostics, importer, admin service, private view,
  direct permission contract, reporting and routing.
- 612 additional related tests passed: SQL connection/runtime composition,
  receipt state, admin review, parser and metadata.
- The additional `test_ui_imports.py` test failed in its unchanged constants stub:
  `PLAYER_STATS_LAST_CACHE` is absent when importing `stats_cache_helpers` through
  registry/target views. This unrelated failure was not changed.
- Architecture, deferred-item, security-routing and command-registration
  validators passed; Ruff and `git diff --check` passed.
- Smoke imports passed with the existing synthetic test environment and UTF-8
  output. `.env` was not read.
- Test selection was run. The full repository suite recommendation was replaced
  by the related suites above and real SQL denial/recovery checks; unrelated
  integrations and environment-dependent suites were not exercised.

## Deployment and recovery boundary

This is a local implementation and diagnostic result. Production was only read;
no grant, retry, restart, migration or deployment was performed.

The revised contract rejects the old grant set. Deployment must coordinate the
four object grants with the promoted bot version and independently reviewed
permission observations/seals; do not merely add grants to the running old sealed
contract or reuse its metadata fingerprint. Existing account provisioning output
is not an upgrade script: it deliberately refuses to adopt an existing user.
Prepare a separately reviewed identity-bound amendment for the existing account.

After authorized deployment, inspect the durable receipt and configuration,
resume its retained original, prepare a fresh confirmation, and have an
authorized operator review it. The expired confirmation must not be replayed.
Do not manually rewrite the receipt, delete accepted facts or re-upload solely to
work around this failure. Rollback of permissions and code must be coordinated
with their corresponding contract snapshot; accepted immutable data is retained.

No SQL schema change was required. The unrelated deferred-optimisation edit and
SQL repository recovery-script edit were preserved.
