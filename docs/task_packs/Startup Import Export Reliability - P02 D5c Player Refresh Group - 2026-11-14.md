# P02 D5c grouped player report and cache refresh

## Approved scope

Prepare, review and execute one bounded offline pass for `player_report_continuation/refresh_report` and `player_report_continuation/refresh_cache` under the user's continuing approval. Start from `d5c-read-release-closeout.json`: 39/73 final-action routes accepted, 34 remaining; 25/25 inspectors; 9/12 D5c families closed. Existing approvals cover related test corrections and additional separately preserved passes. No accepted native operation is replayed.

Use the original PlayerReportContinuation and inherited ConfigurationContinuationDAL/ProducerRefusalDAL, original player request validation and original report intent/runtime context. Reuse the frozen inert fixtures and isolated runner. Cover exact approvals, original failure preservation, foreign ownership, changed configuration, exclusion, compare-and-set loss, work exceptions, duplicate actions, receipt reconciliation and no automatic repeat after an unacknowledged cache write.

The report and cache workers are explicitly inert. Child completion presentation is a controlled test input; original child request lineage is checked, but its atomic report checkpoint and actual cache bytes are not independently established by this group. A cache build can precede failed receipt recording: the test must preserve uncertainty rather than claim no cache effect. This qualification does not prove provider calls, report calculation, filesystem publication, SQL transaction durability or native scheduling. Preserve these limitations as named follow-ups, rather than treating route acceptance as full D5c closure.

## Limits and preservation

Use `python -I -S -B`, 300-second total, 1 MiB combined intent/result, first failure stops, create-new receipts and fixed ordered case list. Pin original evidence and source, including authoritative SQL contracts; verify pins after execution. No new inputs, database/VM work, synthetic rows, permission/settings changes or runtime corrections. Preserve 21 consumed inputs, 1,260 native seconds including the protected 1,000-second later-stage reserve, 50 Windows-test seconds and 11/64 synthetic rows. No limit extension is required.

Output: `.codex_artifacts/p025/d5c-player-refresh/packet.json`, `intent.json`, `result.json`; runner `scripts/run_p02_d5c_player_refresh.py`; cases `tests/test_p02_d5c_player_refresh.py`. Execute only after reviewed frozen bytes are unchanged. If both routes qualify, record 41 accepted / 32 remaining. Failure advances no route count.

## Source validation and review

Validate exact ExportPreparation, ExportResource and StatsImportExecution fields against `C:/K98-bot-SQL-Server/sql_schema`; retain existing 23 SQL source pins. SQL predicates and parameter identities are exercised through the original DAL with inert transaction transport. No SQL repository changes or migration.

Security routing: Changes, Deep off, exact five-file packet range, including tests and this plan. Complete parent and independent review before behavioral execution. Reuse the supplied canonical threat model unchanged with its historical-scope limitation; this packet is offline only. Inspect source loading, file/import guards, preserved hashes, create-new receipts and honest claims. No codebase scan.

Test selector emulation recommends full pytest and startup/registration smoke checks for new tests. Skip those here because they expand into application startup outside the explicitly inert qualification boundary. Use static compilation and the bounded original-body pass. Architecture/deferred/security-routing validation remains a PR gate; no PR or promotion is performed. No new runtime helper or refactor is introduced; reuse existing reviewed test machinery. No new runtime deferred item is identified. All inherited unresolved obligations remain open.

## Next step

Codex runs this offline group after review. No elevated PowerShell action is needed. Later D5c native checks, D5d/e/f and separate D6 deployment remain outstanding.
