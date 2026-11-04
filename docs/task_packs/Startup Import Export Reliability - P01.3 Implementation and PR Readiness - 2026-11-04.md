# P01.3 implementation and PR readiness — 4 November 2026

Status: implementation and local validation complete; both independent branches and PR descriptions ready for publication/review. Nothing has been published, merged, installed or restarted. This receipt supersedes the earlier design-only status, while retaining its agreed scope and limits.

## Delivered behavior

The command, pinned card and persistent Refresh use one bounded passive health projection and renderer. Reads do not acquire writer locks, start probes, scan logs, inspect receipt journals or schedule retry workers. Existing owners publish immutable summaries; busy sources retain their previous observation or unknown, with the next existing five-minute update rereading state. Provider observations become stale after 60 minutes; the existing 90-second recovery-cycle freshness rule remains separate from in-progress/stall ownership.

Refresh has a stable custom ID, no view timeout, prompt acknowledgement before edit, exact guild/channel/message binding and bounded registration. Startup restores the existing message ID, and a successful edit migrates old buttons. Transient fetch failures retain identity; confirmed deletion permits replacement only after the old view closes admission and drains its admitted edit. A settled closed view is replaced with an open successor even when startup registration failed; an active view cannot be discarded by the factory. Shutdown closes interaction admission and drains an admitted edit before teardown. Reconnect cannot restart the loop during shutdown.

The card directs administrators to the existing recovery-centre command in the notify channel. Only a fresh observed access failure with a concrete action or a sustained dashboard delivery problem can use the existing health alert route; generic failed checks, stale observations, unknown and deferred admission alone do not. Attempted but unconfirmed delivery does not become proof of delivery or trigger repeated attempts for the same observation. Recovery incidents retain their existing notification owner and route.

Automatic log scans, ten/sixty-minute error counts, spike alerts and the last-20-errors button are removed. Explicit `/ops logs` remains separate. Ordinary and complete evidence reports optionally include the same compact projection through existing authorization, redaction and budgets. Original report components retain priority. No SQL schema, activation flag, dependency or credential change is required.

The related review corrected startup deadline states that could incorrectly appear settled, normalized an active profile refresh to in-progress, and made invalidated cache summaries unknown rather than a newly dated success. Original business outcomes and receipts are unchanged. SQL/Sheets active compatibility APIs remain available, but the migrated UI no longer drives them and no autonomous collector is added. If no existing owner publishes an observation, the card can remain unknown indefinitely; refresh does not imply a successful provider check.

## Source and updater compatibility

- Mirror baseline: `31552caf24efcd03ed542d68a65e2fb72c602f5a`.
- Reviewed runtime/tool checkpoint: `9410928e417c94bfe59674869a5051e0ab1ded6e`, branch `codex/p013-passive-health`.
- Private baseline fetched: `67c4e12a8ecf0c25280770860480ac65a6826602`; independent local branch `codex/p013-passive-health-private`, source checkpoint `223e5af25f02dfa07ba9f893304418ac8333906a`; equivalent runtime and supporting test/policy files verified.
- SQL diff: none; existing active admission and write/receipt authority remain unchanged.

The protected updater requires a new exact `p013_passive_health_v1` successor containing all 13 runtime members, including the two new modules. All 61 historical transition records are unchanged. The registry cap increases from 128 KiB to 136 KiB to accommodate the complete family and Windows newlines; record count remains bounded at 62. Every predecessor/postimage, missing member, changed peer and incomplete inventory is checked. A target registry cannot grant authority to an installed reader that lacks the new family. Historical tests authenticate the new successor before mapping to their original immutable pins.

An independent offline check also passed `check_transition_inventory` and `check_source_only` against the actual baseline Git blobs and candidate files for all 13 members, with no synthetic hash mapping (`actual-source-transition-final.json`). This is local source compatibility preparation, not installed-tool acceptance. Deployment still requires the normal reviewed updater installation/source-policy protocol; no live updater, native fixture, provider, SQL or restart operation was performed.

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
| H07 restart/lifecycle | Repeated registration and restarted client, transient lookup identity retention, uncertain initial send, existing-card rebinding, admitted edit drain, cancellation during replacement, failed-registration/deleted-card recovery and loop self-stop. Actual factory/binding adapters and successor callback usability are exercised. |
| H08 evidence | Optional ordinary/complete report component, bounded size, unavailable health fault isolation and existing report priority; original redaction/receipt tests retained. |
| H09 cost | Controlled offline matched experiment passed after simulator correction below. No production timing claim. |

Final affected-path validation: 1,434 tests passed in 78.32 seconds, including the final 37 passive-health tests, updater transition/source-admission suites and lifecycle regressions; operational logs remained unchanged. Earlier focused runs (134, 70, 201, 32 and 512 tests) also passed after corrections. Architecture checked 30 Python files; deferred validation checked 33 Markdown files; security routing had zero errors/warnings. The explicit selector recommended full pytest, UI imports, smoke imports and command registration. Scoped Ruff and sequential Black passed. Smoke imports passed with the repository synthetic test environment; registration retained 36 primary commands and 102 grouped subcommands without drift or duplicates. These import/registration results remain applicable: the final factory correction adds no import, configuration or command surface.

Private validation: 144 final focused tests passed in 9.36 seconds, with operational logs unchanged. Private architecture, deferred, security routing, scoped Ruff, smoke imports and registration passed. A duplicate private full suite is not required for local preparation: all changed Python/policy/test files and supporting controls are identical to the mirror; private-specific unchanged files are outside the diff.

Full-suite/log-isolation result: 11,435 passed, 1,114 skipped, 8 subtests and one dependency FutureWarning in 1,060.05 seconds (17:40); operational logs unchanged (`full-pytest-qualified.txt`). This green full run preceded the final two narrow card-replacement lifecycle corrections. Those corrections are qualified by the final 1,434 affected-path tests and 144 private tests above, rather than represented as a second full run at the final runtime checkpoint. Unchanged whole-suite coverage is reused; CI remains a subsequent PR gate.

The final related-path review reproduced two lifecycle defects before fixing them: replacement could discard an admitted old-view edit, and failed startup registration followed by confirmed deletion could reuse a closed view. Retained before-fix runs show two and one failures respectively. Replacement now drains the old owner before sending; the factory retires only a closed, settled view and creates an open successor. Actual callbacks, registration bounds and cancellation are covered.

Adverse full-run evidence is preserved. The second full run recorded 11,424 passed, 11 failures, 1,114 skipped and 8 subtests in 1,083.25 seconds; all failures were old tests expecting 61 registry records or the old 131,072-byte cap. Five tests now expect exactly 62 records and 139,264 bytes, preserving historical digests and one-byte-over-bound refusal. The first full run recorded 11,222 passed, 31 failed, 120 setup errors, 1,114 skipped and 8 subtests in 1,069.68 seconds. Source-pin failures led to the exact additive updater family; two isolated teardown fixtures needed the new helper in their namespace. No failure was suppressed or reclassified as unrelated to avoid fixing it.

Other exploratory failures: smoke imports initially lacked required test environment and hit Windows stdout encoding; rerun with UTF-8 and synthetic values passed. Black's multi-file CLI stalled and was interrupted; sequential `format_file_in_place` completed. The first updater-focused run exceeded the old registry size/count bounds; narrowly increased fixed bounds and rejection tests passed. These do not establish live configuration validity.

## H09 measurements and adverse evidence

The experiment executes 1,000 projection/render samples for each of eight states and 30 alternating baseline/candidate workload pairs, each with 20 observers, 100 card updates and 25 useful cache operations. SQL, Sheets and log adapters are inert and counted. Candidate counts were zero SQL/Sheets/log scans, 100 edits and 25 business operations per pair. There were no new persistent threads or tasks.

The original simulator used a single `asyncio.sleep(0.002)`. Runs 1 and 2 failed elapsed-time gates. The baseline could finish 25 purported 2 ms operations in less than 50 ms: Windows asyncio timer early wakeups violated the simulated external-work contract. Timer-resolution normalization alone did not fix this. Run 3 enforces the same minimum deadline for both versions and scopes Windows timer resolution to 1 ms, releasing it in `finally`. The first two raw failed runs remain retained; no acceptance threshold was changed and no application optimization was selected merely to affect the benchmark.

Run 3 (`h09-run3-deadline.json`): baseline/candidate median 76.134/77.039 ms (+1.19%, limit +2%); p95 82.021/81.648 ms (limit +5%). Loop-lag p95 1.976/1.962 ms (limit +5 ms). Maximum across state-specific render p95 was 0.051 ms and p99 0.103 ms (limits 5/10 ms). Maximum serialized projection 5,063 bytes; retained growth after 2,000 reads 1,336 bytes; zero new persistent workers. Pure rendering excludes unchanged mandatory command telemetry. This synthetic controlled experiment does not establish deployment-host performance or provider acceptance. Its measurements remain applicable after the final exceptional replacement fixes: projection, rendering and the measured normal update adapter did not change. Replacement/cancellation behavior is separately tested above.

## Security and review

Changes only, Deep off. Completed reviews compose across immutable source targets:

| Repository | Range | Completed scan | Result |
| --- | --- | --- | --- |
| Mirror full source | `31552caf..38c9e897` | `bd664ced-76de-4f25-bbf2-278f96dbbdd1` | 16 source files; zero reportable findings |
| Mirror owner drain | `38c9e897..c69aa35b` | `7e0f3305-ac58-4c51-a203-728d0bdd5ce3` | Two source files; zero reportable findings |
| Mirror open successor | `c69aa35b..9410928e` | `88b59ab6-6486-4d9e-878c-b384df0d5626` | Two source files; zero reportable findings |
| Private full source | `67c4e12a..e9ecacaf` | `4b22af87-df08-46b5-b75d-cf8caa5ec3dc` | 16 source files; zero reportable findings |
| Private owner drain | `e9ecacaf..de6a0bb3` | `72898b57-fde6-442a-a11a-02ce4c9b41fc` | Two source files; zero reportable findings |
| Private open successor | `de6a0bb3..223e5af2` | `9c4fe03c-a341-4060-bade-96d76fe4bf39` | Two source files; zero reportable findings |

The initial 14-source review `839fc90c-2916-4c46-98f9-c264021c7ff7` is retained as earlier evidence. Disjoint UI/state/updater reviews were reconciled. The functional closed-successor follow-up recorded against the earlier immutable owner-drain target is resolved by the final successor correction and regression test. Final documentation-only receipt/status updates receive a precise Changes-scan skip: no production code, permissions, SQL, file/network access, configuration or persistence behavior changes after the final reviewed runtime checkpoints. Test-only count/limit corrections and lifecycle qualification preserve historical pins, authority and refusal assertions.

All changed source/policy/test files and directly supporting controls are equivalent across the independent private and mirror candidates. The private branch descends from its private baseline without mirror ancestry. Reviews do not certify live configuration, ACLs or services. Tool-reported usage for the full-source mirror/private reviews was 1,957,241/2,010,275 tokens (1,934,976/1,993,856 cached input); owner-drain reviews each reported 2,754,498 tokens (2,736,512 cached input). Final successor reviews each reported 542,658 tokens (503,552 cached input). These are tool accounting values, not independently measured incremental scan costs.

Review verdict: ready for local PR publication and review; no unresolved code finding. CI, PR review and installed/runtime acceptance remain subsequent gates before merge/deployment. Required document/archive carry-forward is part of both PRs. Completed reports, manifests and coverage are retained in the Codex Security workbench. Daybreak access was reported not granted; protected artifact display may be unavailable even though review completion succeeded.

## Residual limits and deferred scope

An uncertain initial Discord send is not repeated in the same process. Across restart, an unrecorded send cannot be identified without a new persistence/reconciliation contract; that is not introduced here. No external whole-bot outage detector is added. Natural deployed callback acceptance and configured destination permissions remain later deployment checks. P04 owns broader delivery escalation; P02/P03 retain their active-work and recovery obligations. The explicit log viewer's synchronous whole-file scan remains the separately captured deferred item in the design; it was not changed opportunistically.

Document verification: all 30 required documents, 14 archive moves and 467 checked links are present and valid in both candidate trees. Canonical Git/LF bytes match; raw Windows newline hashes are retained separately. The three readme indexes preserve newer base content while merging programme navigation. The existing promotion script publishes branches as part of its workflow; local preparation used its file-delta method with `git apply --index` and no push, keeping publication outside this authorization.

Both PR descriptions must identify this receipt and the documentation carry-forward manifest. No SQL PR is required. Publication, CI/review comments, merge and deployment remain separate from this local preparation.

## PR review follow-up

The operator subsequently authorized publication, review corrections and merge; deployment remains an operator action. Mirror PR #486 and private PR #726 are open. Private review identified that a confirmed Discord send rejection left creation suppressed until restart. Four before-fix regressions reproduced this for Forbidden/NotFound during first creation and deleted-card replacement. These confirmed non-delivery outcomes now clear the suppression flag so the existing five-minute update can recover. Uncertain transport/server outcomes still suppress duplicate sends; no retry worker or new cadence is added. All 148 focused tests pass with operational logs unchanged, including existing uncertainty, shutdown and cancellation cases.

Private CI also identified an inferred-string type error in the developer-only benchmark namespace. An explicit local dictionary annotation fixes Pyright with no executable bytecode/constants change; source-column tables differ. Scoped Ruff and sequential Black pass. Local Pyright reports zero errors; unresolved optional platform/dependency imports remain warnings. The full suite and hosted review/checks will run again at the corrected PR head. The unpublished P01.3 updater family changes only its exact bot postimage, preserving all 61 historical records and complete membership. Final review/merge receipts and the operator deployment plan are retained with the release package.

A second PR review corrected the initial SQL/Sheets reason label: a never-observed scoped probe now says `not_observed`, while an actual different-scope or unscoped completed observation remains `scope_mismatch` and exposes no retained result. The original mismatch guard is unchanged. The new initial-label regression failed before the fix; the cross-scope safety regression passed before and after. All 127 focused health/probe/updater tests passed with operational logs unchanged.

The related private review now also has an explicit SQL configuration-unavailable guard, matching the Sheets facade. When configuration is not loaded, the passive SQL snapshot returns unknown/source_unavailable with no retained result and never imports configuration. Its regression reproduced the prior behavior; all 128 focused health/probe/updater tests pass. Active SQL execution and scope binding remain unchanged.
