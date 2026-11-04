# P01.3 implementation and PR readiness — 4 November 2026

Status: implementation complete locally; final full-suite and independent private preparation pending. Nothing has been published, merged, installed or restarted. This receipt supersedes the earlier design-only status, while retaining its agreed scope and limits.

## Delivered behavior

The command, pinned card and persistent Refresh use one bounded passive health projection and renderer. Reads do not acquire writer locks, start probes, scan logs, inspect receipt journals or schedule retry workers. Existing owners publish immutable summaries; busy sources retain their previous observation or unknown, with the next existing five-minute update rereading state. Provider observations become stale after 60 minutes; the existing 90-second recovery-cycle freshness rule remains separate from in-progress/stall ownership.

Refresh has a stable custom ID, no view timeout, prompt acknowledgement before edit, exact guild/channel/message binding and bounded registration. Startup restores the existing message ID, and a successful edit migrates old buttons. Transient fetch failures retain identity; confirmed deletion permits replacement. Shutdown closes interaction admission and drains an admitted edit before teardown. Reconnect cannot restart the loop during shutdown.

The card directs administrators to the existing recovery-centre command in the notify channel. Only a fresh observed access failure with a concrete action or a sustained dashboard delivery problem can use the existing health alert route; generic failed checks, stale observations, unknown and deferred admission alone do not. Attempted but unconfirmed delivery does not become proof of delivery or trigger repeated attempts for the same observation. Recovery incidents retain their existing notification owner and route.

Automatic log scans, ten/sixty-minute error counts, spike alerts and the last-20-errors button are removed. Explicit `/ops logs` remains separate. Ordinary and complete evidence reports optionally include the same compact projection through existing authorization, redaction and budgets. Original report components retain priority. No SQL schema, activation flag, dependency or credential change is required.

The related review corrected startup deadline states that could incorrectly appear settled, normalized an active profile refresh to in-progress, and made invalidated cache summaries unknown rather than a newly dated success. Original business outcomes and receipts are unchanged.

## Source and updater compatibility

- Mirror baseline: `31552caf24efcd03ed542d68a65e2fb72c602f5a`.
- Reviewed runtime/tool checkpoint: `38c9e8974d5ee53d4911d6c200cdb238be8a48e5`, branch `codex/p013-passive-health`.
- Private baseline fetched: `67c4e12a8ecf0c25280770860480ac65a6826602`; independent local preparation pending final mirror validation.
- SQL diff: none; existing active admission and write/receipt authority remain unchanged.

The protected updater requires a new exact `p013_passive_health_v1` successor containing all 13 runtime members, including the two new modules. All 61 historical transition records are unchanged. The registry cap increases from 128 KiB to 136 KiB to accommodate the complete family and Windows newlines; record count remains bounded at 62. Every predecessor/postimage, missing member, changed peer and incomplete inventory is checked. A target registry cannot grant authority to an installed reader that lacks the new family. Historical tests authenticate the new successor before mapping to their original immutable pins.

This is local source compatibility preparation, not installed-tool acceptance. Deployment still requires the normal reviewed updater installation/source-policy protocol; no live updater, native fixture, provider, SQL or restart operation was performed.

## Validation evidence

Private raw evidence is retained under `.codex_artifacts/p013-validation/` on the development PC; it is not a repository dependency or a public download.

| Gate | Evidence and disposition |
| --- | --- |
| H01 passive entrypoints | Real command body and scheduled adapter with fake Discord, fail-on-call active dependencies; shared payload and one-button inventory. Explicit log command retained. |
| H02 observation truth | Unknown, scope mismatch, stale/invalid/future timestamps, success/failure history, deferred, in-progress, recovery freshness/stalls; cache invalidation and startup pending completion covered. |
| H03 original ownership | Existing probe proof/cleanup/activity tests plus controlled actual thread, observer timeout, late completion and repeated passive reads; no replacement work. |
| H04 locks/fault isolation | Writer locks held by another thread while snapshots render; immutable records, bounded fields, optional metadata failure and unchanged business result covered. |
| H05 interactions | Actual Pycord persistent registration, stable ID, repeated refresh, stale message/guild/channel refusal, acknowledgement before edit, expired/failed acknowledgement and concurrent interaction coalescing. |
| H06 alerts/navigation | Action classification, cooldown and observation deduplication, failed delivery reservation, dashboard link and configured notify-channel recovery route. |
| H07 restart/lifecycle | Repeated registration and restarted client, transient lookup identity retention, uncertain initial send, existing-card rebinding, admitted edit drain and loop self-stop. |
| H08 evidence | Optional ordinary/complete report component, bounded size, unavailable health fault isolation and existing report priority; original redaction/receipt tests retained. |
| H09 cost | Controlled offline matched experiment passed after simulator correction below. No production timing claim. |

Focused validation: initial 134 existing tests passed; 70 final state/profile/startup tests passed; 201 updater/lifecycle tests passed; all 32 remaining previously failing tests passed. Architecture validation checked 25 Python files; deferred validation checked 32 Markdown files; security routing had zero errors/warnings. Explicit selector recommended full pytest, UI imports, smoke imports and command registration. Scoped Ruff and sequential Black passed. Smoke imports passed using the repository's synthetic test environment; command registration retained 36 primary commands and 102 grouped subcommands without drift or duplicates.

Final full-suite/log-isolation result: PENDING. The first full run recorded 11,222 passed, 31 failed, 120 setup errors, 1,114 skipped and 8 subtests in 1,069.68 seconds. Source-pin failures led to the exact additive updater family; two isolated teardown tests needed the new helper in their namespace. No failure was suppressed or reclassified as unrelated to avoid fixing it.

Other exploratory failures: smoke imports initially lacked required test environment and hit Windows stdout encoding; rerun with UTF-8 and synthetic values passed. Black's multi-file CLI stalled and was interrupted; sequential `format_file_in_place` completed. The first updater-focused run exceeded the old registry size/count bounds; narrowly increased fixed bounds and rejection tests passed. These do not establish live configuration validity.

## H09 measurements and adverse evidence

The experiment executes 1,000 projection/render samples for each of eight states and 30 alternating baseline/candidate workload pairs, each with 20 observers, 100 card updates and 25 useful cache operations. SQL, Sheets and log adapters are inert and counted. Candidate counts were zero SQL/Sheets/log scans, 100 edits and 25 business operations per pair. There were no new persistent threads or tasks.

The original simulator used a single `asyncio.sleep(0.002)`. Runs 1 and 2 failed elapsed-time gates. The baseline could finish 25 purported 2 ms operations in less than 50 ms: Windows asyncio timer early wakeups violated the simulated external-work contract. Timer-resolution normalization alone did not fix this. Run 3 enforces the same minimum deadline for both versions and scopes Windows timer resolution to 1 ms, releasing it in `finally`. The first two raw failed runs remain retained; no acceptance threshold was changed and no application optimization was selected merely to affect the benchmark.

Run 3 (`h09-run3-deadline.json`): baseline/candidate median 76.134/77.039 ms (+1.19%, limit +2%); p95 82.021/81.648 ms (limit +5%). Loop-lag p95 1.976/1.962 ms (limit +5 ms). Maximum across state-specific render p95 was 0.051 ms and p99 0.103 ms (limits 5/10 ms). Maximum serialized projection 5,063 bytes; retained growth after 2,000 reads 1,336 bytes; zero new persistent workers. Pure rendering excludes unchanged mandatory command telemetry. This synthetic controlled experiment does not establish deployment-host performance or provider acceptance.

## Security and review

Changes only, Deep off. Scan `839fc90c-2916-4c46-98f9-c264021c7ff7` covered the initial 14-source checkpoint `7f0a867` with zero reportable findings. Final scan `bd664ced-76de-4f25-bbf2-278f96dbbdd1` covered all 16 changed source files at `31552caf..38c9e897`, including updater and benchmark additions, with zero reportable findings. Disjoint UI/state/updater reviews were reconciled; unchanged coverage was reused only after exact blob equality verification. Final scan reported 1,957,241 tokens (1,934,976 cached input tokens). It does not certify live configuration, ACLs or services. Subsequent documentation-only receipt/navigation corrections have no executable/security-sensitive change and receive a precise diff skip.

Review verdict: final full-suite and private preparation pending. No remaining code finding in the reviewed source. Required document/archive carry-forward is part of the PR, not optional history. The complete report, manifest and coverage remain in the Codex Security workbench. Daybreak access was reported not granted; protected artifact display may be unavailable even though review completion succeeded.

## Residual limits and deferred scope

An uncertain initial Discord send is not repeated in the same process. Across restart, an unrecorded send cannot be identified without a new persistence/reconciliation contract; that is not introduced here. No external whole-bot outage detector is added. Natural deployed callback acceptance and configured destination permissions remain later deployment checks. P04 owns broader delivery escalation; P02/P03 retain their active-work and recovery obligations. The explicit log viewer's synchronous whole-file scan remains the separately captured deferred item in the design; it was not changed opportunistically.

Both PR descriptions must identify this receipt and the documentation carry-forward manifest. No SQL PR is required. Publication, CI/review comments, merge and deployment remain separate from this local preparation.
