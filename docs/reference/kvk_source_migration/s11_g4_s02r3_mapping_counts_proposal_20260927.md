# S02R3 — exact permission target mapping and public category counts

PREPARED, NOT APPROVED OR EXECUTED. Local preparation only. This new scoped operation does not retry S02R1 or S02R2.

Command: `.codex_artifacts/s11-g4-capture-preparation-20260926/commands/S02R3.sql.txt`.

SHA256: `4a874bdc835fc7153ac945aed9eb0bc0c8a54f763b74e883505f90dedb708390`.

## Targets and reused facts

Existing SSMS session only, MINI_AMD / ROK_TRACKER, accepted SQL ORIGINAL_LOGIN MicrosoftAccount\cwattsconsulting@outlook.com. Chris Watts is operator/reviewer/abort owner. Retain Windows/UI MINI_AMD\cwatt separately. H14 SSMS executable hash: `935b24379389e8260ac0d02d5e77402b005fce12c72b0ed2894a4138a6864fb7`; no fresh executable observation implied.

S02R2 returned eight explicit SHEETS_USER grants, including EXECUTE on object IDs 1322500536 and 1766401462 and INSERT/SELECT/UPDATE on schema ID 1. Their installed names were not returned. S02R1 already captured role membership, including db_owner, and absence of three S11 roles; its public permission prefix reached 129 rows and is incomplete. Reuse these facts without repeating inventories. Source definitions do not establish production object IDs.

Read sys.objects/sys.schemas for exactly those two object IDs and that schema ID. Output target class/ID, schema name, object name/type and present flag. LEFT JOIN preserves an absent target as a row with null names and present=0. No module text, object content, parameter shape, procedure execution or schema expansion.

Separately read public entries in sys.database_permissions joined to sys.database_principals and aggregate by class/class_desc/state_desc and a two-value ID bucket. The negative_object_id bucket means only class=1 and major_id<0; do not interpret the label as verified system/default/safe grants. All other entries are counted in other. Output only category counts, not permission details or additional principals. No public entries are filtered out before grouping. Counts will inform a separately approved missing-detail proposal; they cannot complete the public permission inventory, establish default permissions or prove effective capability.

## Exact limits and effects

Four result sets: one identity/UTC/visibility row; exactly three target rows; zero to 33 public category rows; one completion row. Thirty-three categories is the sentinel for a 32-category budget and means INCOMPLETE/STOP. If all categories fit, their sum is a point-in-time row count for this filtered catalog, not a full effective permission inventory. The mapping and aggregate statements are not a transactionally consistent snapshot with each other or prior receipts.

One attempt, one batch, 32 KiB output maximum, ten-second current-tab query timeout, fifteen-second operator cutoff, one-second session lock timeout, MAXDOP1 on both catalog queries. Counts require scanning/grouping matching catalog rows; TOP bounds result categories, not scanned rows or CPU/I/O/memory. No full elapsed-time guarantee is inferred from result timestamps.

The exact S02R2 guard/identity prefix is retained: isolated transaction-state/count/implicit flag checks, accepted target/login, VIEW DEFINITION and database CONTROL gates, NOCOUNT ON, LOCK_TIMEOUT 1000 and DEADLOCK_PRIORITY LOW. These session effects persist afterward. CONTROL is observer visibility, not future application privilege. Other effects: local scalar assignments, catalog reads/locking/audit/resource use and editor/history/autorecovery. No SQL data/schema/permission writes, provisioning, import/export, backup/restore, application procedure, provider/Discord call, task/Agent control, restart/deployment or Git publication.

## Approval, execution and stops

Requires approval of this exact hash/envelope for a fresh twenty-minute UTC window. Existing connection only; zero new connections requested, five-second connect timeout unestablished, invisible SSMS reconnect cannot be excluded. Stop on disconnected/changed target or reconnect/auth/certificate prompts. Do not create a query connection, alter settings, weaken TLS or switch client.

Replace only the previous capture text in the existing unsaved editor; stop if unrelated work is present. Verify the final marker `S02R3 ID mapping and public counts completed`. Execute the entire exact batch once, not a selected fragment. Confirm the existing ten-second timeout remains set. Start operator timing before Execute; cancel at fifteen seconds and report if still running. Cancellation is not proof of server quiescence.

Stop on errors/guard failure, target or visibility mismatch, any present=0 mapping, unexpected row shape, 33-category sentinel, output over 32 KiB, truncation, missing completion or time limit. A completed aggregate does not override a missing mapping stop. No retry, pagination, broader lookup, cap increase, kill, reconnect, COMMIT/ROLLBACK, grants or transaction repair. Preserve all four result sets, empty headers, errors and timing; retain receipt time separately. No subsequent operation inherits approval.

## Validation and retained boundaries

Local static checks: exact previous prefix, literal target IDs from S02R2, preserved missing rows, one public-only aggregate, no dynamic SQL/mutation or predecessor inventory. Authoritative SQL migration source uses the same sys.objects catalog; no application schema or installed mapping is inferred from Python/source names. Live SQL validation is pending; no deployment verdict follows.

Documentation/inert-observation preparation retains the documented security-routing skip; no runtime implementation, SQL migration or permissions change, no PR. Runtime tests, predecessor suites and pre-PR validators are skipped as inapplicable. No security discovery launched. Existing sealed evidence and pending work are preserved.

All seven typed G4 proofs and actual restore remain incomplete. Rollout/G5 remain unapproved. Preserve isolated hotfix, single-account/admin-owned operation, fresh output/equivalent reports, deferred memory investigation, withdrawn collector and separate KVK/view-rehydration issues.
