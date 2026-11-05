# F01 receipt — source candidate file metadata

Bounded file metadata observation COMPLETE. Operator JSON reports Operation F01, Host MINI_AMD, Status Completed, FailureType null, ExpectedFiles=ObservedFiles=119. All 119 paths are distinct and exactly match the sealed manifest, with no missing/unexpected path or zero-length file. Every file reports Archive attributes. This is operator-reported metadata, not independent authenticated filesystem or content verification.

Raw attachment preserved byte-for-byte at `.codex_artifacts/s11-g4-capture-preparation-20260926/received-F01-20260928T103011Z.txt` (18,658 bytes, below 128 KiB). It includes a trailing `PS C:\WINDOWS\system32>` prompt. The JSON object was parsed separately; the prompt is retained as text, never executed. Initial whole-file JSON parsing rejected that prompt; this was a local parser issue, not a failed production observation or reason to rerun.

Receipt recorded 2026-09-28T10:30:11Z. Reported start 10:29:45.6292724Z, finish 10:29:45.8818437Z, ElapsedMilliseconds=250, within ten-second cooperative/fifteen-second operator budgets and maintenance window ending 2026-09-29T09:23:23Z. Reported stopwatch and UTC interval differ slightly; retain supplied values without inventing independent timing.

Completed status is consistent with all four fixed parent-directory/reparse checks passing in the approved command; individual parent attributes were not emitted, so do not fabricate parent rows or claim race-free traversal. File reparse flags are not present in emitted attributes. No native token/handle identity or subsequent path stability was established.

## Size reconciliation

Actual reported file-length total: 2,815,180,800 bytes. Catalog compressed-size total: 2,814,975,773 bytes. Difference: +205,027 bytes across the candidate set. All 119 individual file lengths differ from their corresponding catalog compressed_backup_size values. These quantities are retained separately; no automatic equality assertion was required by F01. Differences alone do not establish either corruption or integrity, and their exact cause was not investigated.

Per-file path, actual/catalog lengths and signed deltas are retained in `f01-local-analysis-20260928.json`. Full file length is 1,173,233,664 bytes versus catalog 1,173,233,788; do not conceal negative as well as positive differences. Exact file last-write times are preserved in the raw receipt. No file content, hash, header, backup verification or restore was performed. Catalog candidate relationships remain separate from physical-media validation.

## Remaining grouped work

Source file existence/nonzero lengths at the observation are now supplied. Do not repeat all 119 metadata reads merely to refresh them. They remain under the partly understood prune roots; this receipt neither preserves them against future deletion nor approves copying/moving them. Retention/protection and media-header/readability/integrity work require exact separately approved operations and I/O budgets.

Destination database/file exclusions, exact volumes/paths and usable capacity remain unresolved. The existing question about an already-open development SSMS binding is pending; no answer or connection authorization is assumed. Production session identity cannot be reused as a development guard. No disposable database/path reservation, media copy or restore is approved.

Maintenance approval remains through 2026-09-29T09:23:23Z without renewed scheduling confirmation. All seven typed G4 proofs and actual restore remain incomplete; rollout/G5 unapproved. Preserve pending/recovered work, isolated hotfix, single-account/admin-owned operation, fresh output/equivalent reports, deferred memory cause, withdrawn collector and separate KVK/view issues.

Validation: JSON plus trailing-prompt handling, 119-row uniqueness/exact manifest equality, lengths/attributes, timing/budgets, proposal/approval seals and original evidence preservation. Documentation/evidence only; no runtime/predecessor tests or security discovery applicable. No live observation by the assistant.
