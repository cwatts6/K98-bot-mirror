# P01.3 closeout: passive health and complete evidence delivery

Date: 5 November 2026. **CLOSED: implemented, reviewed, merged, deployed and live-validated for the agreed P01.3 scope.** The operator requested formal closeout and progression to P01.4. This is not whole-programme or incident-recovery completion.

## Delivered contract and accepted decisions

- Health card, Refresh and `/ops dl_bot_status` share retained observations. Rendering never starts SQL/Sheets probes, automatic log scans, journal reads, repair or retry. Reads consume immutable loaded state without waiting for a lock; busy/unknown is not a failure.
- The existing dashboard rereads every five minutes. No extra recheck worker or failure alert is created. Provider freshness is 60 minutes; the recovery monitor's 90-second completed-cycle freshness remains separate from its 300/900-second progress rules. Stale means old evidence, not proof the dependency failed.
- Unknown data remains unknown, including queue depth and providers with no observations. Observations are not write authority or durable business receipts. Mandatory checks at actual write boundaries and existing command-usage telemetry remain intact.
- Automatic log scans, last-20-errors and count-derived spike alerts are removed. Explicit `/ops logs` remains. Actionable failures use the existing status/recovery routes and shared interpretation. P04 owns broader delivery/escalation work; the operator accepts user reports for very rare whole-bot outages.
- Refresh uses persistent registration, stable identity, early acknowledgement and bound guild/channel/message checks. Restart/legacy-button migration and bounded registrations are covered. Shutdown and replacement drain owned edits; confirmed send rejection/deletion is distinct from unknown delivery. Unknown delivery preserves identity to avoid duplicate messages; process-local uncertainty is not a promise of restart durability.
- Ordinary evidence reports and the actual complete ZIP contain passive health with source-specific provenance, timestamps, truthful availability and existing redaction/bounds/continuation controls.

## Delivery and reviewed identities

| Delivery | Mirror | Private production | Outcome |
| --- | --- | --- | --- |
| Original P01.3 | [PR 486](https://github.com/cwatts6/K98-bot-mirror/pull/486), merge `e90b587ae55e2277120ac1f4a7a423eb58464116` | [PR 726](https://github.com/cwatts6/k98-bot/pull/726), merge `190f6be14603c438129c5898aeeb1455a9e89d80` | Deployed; persistent Refresh, automatic refresh and command/card parity accepted. |
| Complete ZIP correction | [PR 487](https://github.com/cwatts6/K98-bot-mirror/pull/487), final head `2f2883a98dfc30dff0373dd38800bb4795f1b652`, merge `a9b49774fcf6aa559830dd5066c7277647b9c419` | [PR 727](https://github.com/cwatts6/k98-bot/pull/727), final head `65ad4fa6d765a88b45cfbb6bba8b6b32af802f6e`, merge/deployed `6ec393f71626d15fcb8c50c840854fb681d5f09e` | Both merged trees equal reviewed heads; Report 75 closes live acceptance. |

Mirror/private histories are independent. The mirror scrubber's `209ab395b2d2e6c167d234022da6db768113c0a6` had the same tree as the original mirror merge; it is not a production deployment identity. All 20 changed files and six supporting blobs for the correction matched across the reviewed branches.

Review findings were actioned/responded to and resolved. Exact-final-head Codex review reported no findings. Copilot's plan/policy limitation was not a complete independent review; the late test-helper `next`/StopIteration diagnostic suggestion was answered as non-blocking, not represented as an implemented fix.

Current installed updater manifest SHA256: `845aa1a349fc6d387b0a48d5b8c53e5f4bdb8d1fa6c72f56c5a00464aed495de`.
The correction adds only exact `p013_health_archive_v1` authority for `services/recovery_complete_report.py`, predecessor `9ad48bce5e303b1e3cef03c87d75a09a8ef6c46529af129994b29e557c300cad`, successor `3dc22b5a825edaf3d67ed03d5d04a5cc070019d33683b00bcc5683308ec6a09f`. All 62 prior records retain structured digest `4b36fd4a0996b43ebe5e81303b5813ee54f5e0499d9097a487d8273c783648c9`; count limit is 63 and byte cap remains 139264. Old tool requires upgrade; exact new tool is routine-compatible. Do not rewrite historical pins or authorize from target files alone.

The retained operator package is private evidence under `.codex_artifacts/p013-zip-fix/K98-P013-ZIP-Correction-6ec393f7`; its ZIP SHA256 is `7f54977d5ab8dd363c7431a70f407aba0fd98e565ff46f93a0b9c5f2b467446d` (822067 bytes, 14 files). It is a completed deployment record, not an instruction to redeploy.

## Regression found and corrected

Report 74 declared health available but omitted it from the ZIP. The collector/schema had been updated while the final archive member list had not. The passive-health test stopped at collection. The correction adds the member after existing optional evidence and tests the real service's delivered ZIP. Every available descriptor must have a delivered member with matching SHA256/size; bounded omission must have explicit continuation. No other collector/archive omission was found.

Four regressions failed before the fix and passed after: available, unavailable, oversized and capacity-limited health. Tests preserve incident priority, redaction, actor-bound frozen continuation, expiry, exact reconstruction, previous-part hashes, retries without recollection and existing budgets. Lesson: validate the user-visible artifact and equivalent paths, not only the helper returning its inputs.

## Validation evidence

- Final correction CI: 11293 passed, 1280 skipped, 19 warnings, eight subtests passed (744.61 seconds). Windows: 315 Python tests and seven PowerShell 5.1 fixtures passed. Two unchanged PowerShell subprocess timeouts on the first run remain recorded; no timeout/assertion was weakened, affected families and final reruns passed.
- Local related validation: 359; private focused: 163; historical updater transitions: 465; nine new transition cases. These counts overlap and must not be added as unique coverage.
- Architecture, deferred-items, security routing, explicit-path selection, scoped Ruff/Black/diff checks, Pyright, smoke imports and command registration passed for the release. Operator guide parsed in PowerShell 5.1; read-only ZIP check qualified with five fixtures, including defective Report 74.
- Separate Changes reviews, Deep off: mirror `c00cd8c3-7c69-4f39-bb84-7122b3120998`, private `49567b11-b14f-46ba-a706-20c19fcc8bda`; all three changed source files covered, zero issues. Subsequent prose-only changes had a documented skip.
- Original H09 cost qualification retained 1000 samples across eight states and 30 matched workload pairs. Business median 76.134 to 77.039 ms (+1.19%, limit 2%); p95 82.021 to 81.648 ms; loop-lag p95 1.976 to 1.962 ms. Render p95/p99 below 0.051/0.103 ms against 5/10 ms limits; maximum projection 5063 bytes against 16 KiB. Zero SQL/Sheets/log calls or added persistent task/thread. This is controlled qualification, not a production performance claim.
- Two adverse benchmark runs remain retained. Equal minimum completion deadlines and scoped Windows timer resolution corrected a simulator early-wake artefact; acceptance limits were not waived. No instrumentation should create the failure it purports to observe.

## Live acceptance: Report 75

The supplied deployment transcript confirms updater upgrade, source/seed/start/readiness, exact source/tool identities and no active update. The bot is online. Readiness's `fresh_import_export_health_evidence_unavailable` remains a qualification limit, not a failed deployment or instruction to replay business work.

The independently checked complete ZIP has seven members: incidents, summary, startup, diagnostic health, operations, health observations and manifest. CRC and all delivered hashes/sizes pass; no available component is omitted. Health is 3701 bytes, SHA256 `cd3e1a52d9758dda3c908d77dd9e4e8f312161974a7db08bf12a083c7c20dc66`, captured `2026-11-05T09:41:07.113369+00:00`. The ordinary report at `09:42:04.017735` has the same process/retained values/source timestamps, with expected age/capture changes and newer recovery progress. Generic descriptor fields marked unknown do not erase source-specific timestamps inside the health JSON.

Eight startup steps are retained. Tracked views attached 21 with no failure. Stats cache and tracked-view rehydration completed after their observation deadline but physically settled successfully; retain both facts. Supplied 493 log lines contain no ERROR, CRITICAL or traceback. Expected shutdown cancellation/disconnect and command inventory warnings are not newly inferred failures. An empty valid event cache explains pending event-dependent work; it is not evidence of a fault.

Incident coverage is explicitly partial: 370 of 17754, with 17384 omitted under the 30-second budget; incident reads took 27.2657 seconds. All included incidents were resolved, so this subset cannot diagnose the six open incidents. Incident continuation is available, diagnostic continuation is not required. A full history download is not a health acceptance gate.

## Evidence locations and remaining ownership

Private local receipt: `.codex_artifacts/p013-zip-fix/report75-live-validation.json`; ZIP SHA256 `94d2d9897b774a501f4b4496af43af070641ce9dae9cb92e07210d3ff300724f`.
Operator inputs: `C:/Users/cwatt/Downloads/K98-recovery-complete-report (75).zip`, `K98-recovery-report-part-1 (8).json`; deployment attachment `952cb9be-c4fc-4b94-ad47-a98a94e26112/Pasted text.txt`; runtime attachment `787817c8-6bac-4bdc-a44c-399db6254f84/Pasted text.txt` under `C:/Users/cwatt/.codex/attachments/`. Preserve raw evidence privately; do not commit runtime reports/logs or credentials to the mirror.

Original validation is under `.codex_artifacts/p013-validation/`; correction/review/updater proofs under `.codex_artifacts/p013-zip-fix/`. Documentation pre-edit copies, move hashes and validation are under `.codex_artifacts/p013-closeout-p014-20261105/`.

P01.4 owns F17/F30; P01.5/P01.6 remain. P02 owns contention/holder attribution (including F09/51421), P03 safe original-intent continuation/recovery, P04 convergence/history and delivery, P05 mandatory final repository confirmation. Do not assert all six incidents are actionable only in P02: each needs exact evidence and its actual owner. Fresh end-to-end import/export and natural acceptance remain unproven. Explicit whole-file log-reader optimisation keeps its existing deferred owner. No incident was cleared, provider probed, work replayed or deployment repeated for this closeout.


## Related records

- [P01.4 handover](Startup%20Import%20Export%20Reliability%20-%20P01.4%20Handover%20and%20Scope%20-%202026-11-05.md)
- [documentation carry-forward](Startup%20Import%20Export%20Reliability%20-%20P01.4%20Delivered%20Documentation%20Carry-forward%20-%202026-11-05.md)
- [programme scope](../Startup%20Import%20Export%20Reliability%20-%20Scope%20-%202026-11-02.md)
- [tracker](../Startup%20Import%20Export%20Reliability%20-%20Tracker%20-%202026-11-02.md)
- [P01 design](../Startup%20Import%20Export%20Reliability%20-%20P01%20Design%20-%202026-11-03.md)
- [P01.3 design and qualification](Startup%20Import%20Export%20Reliability%20-%20P01.3%20Design%20and%20Qualification%20-%202026-11-04.md)
- [implementation receipt](Startup%20Import%20Export%20Reliability%20-%20P01.3%20Implementation%20and%20PR%20Readiness%20-%202026-11-04.md)
- [ZIP correction](P01.3%20Complete%20ZIP%20Health%20Correction%20-%202026-11-05.md)


## Documentation closure validation (E86)

The local closeout changes 24 Markdown files, moves five completed/superseded records and adds this final archived closeout plus the active P01.4 handover/carry-forward manifest. All five moved bodies match their retained originals after accounting for historical banners and link rebasing. All 527 checked relative links resolve, with no references to removed active paths. The manifest exactly matches the documentation delta. Architecture (zero Python files), deferred-items (24 Markdown files), explicit-path test selection, security-routing (zero errors/warnings) and diff whitespace checks pass. Runtime tests, smoke imports and registration are explicitly skipped for this documentation-only change. No runtime, SQL or production change occurred.

These documentation updates remain local and are listed for the next authorized mirror PR/private promotion. Validation receipts and final hashes are under `.codex_artifacts/p013-closeout-p014-20261105/`; raw production evidence remains private. The next chat starts P01.4 review/scope under the linked handover.
