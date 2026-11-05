# P01.2b handover: early issuer evidence and offline collection

Status: E75, 4 November 2026. Operator decision: close the proactive startup-observer/instrumentation proposal without deployment. Its theoretical coverage benefit does not justify the measured cost, complexity and risk. Preserve the bot and startup behavior; use existing evidence and simple best-effort collection. No replacement observer, shared-memory/native issuer helper or mandatory new exporter is queued. Future additions require a demonstrated incident/evidence gap and proportionate cost and safety justification. This is a scope decision, not delivery or passing qualification of P01.2b instrumentation. Earlier designs and E72-E74 results remain historical evidence.
Owner for delivery: Codex in the P01.2b chat. Policy/acceptance owner: Chris Watts.
This is the next slice after [P01.2a closeout](Startup%20Import%20Export%20Reliability%20-%20P01.2a%20Closeout%20-%202026-11-04.md)
(E68); E69 records the requested documentation update and chat start. Do not ask
again whether to start the agreed review. Runtime implementation follows a concrete
reviewed design, as required by AGENTS.md; production actions remain separate.

## E75: operator decision - simplicity and startup safety take priority

The operator accepted E74's value/cost conclusion and explicitly rejected pursuing a theoretical requirement at additional cost or risk. Close proactive P01.2b startup instrumentation without deployment; do not treat it as waiting for optimisation or a different transport. The rejected pipe, external observer and shared-memory/native issuer helper are not active implementation tasks.

Use the already-delivered evidence collection and existing supported logs, receipts and reports. Capture or present additional available information on a best-effort basis where it helps an actual investigation. Missing early detail is an accepted coverage limitation, never proof of success or of no failure. Do not add startup dependencies, background workers, polling, retries, stream interception or stronger durability requirements solely to fill hypothetical gaps. Existing mandatory operational receipts and safety checks remain unchanged.

No standalone offline exporter is mandated or authorized for implementation by this decision. If an incident reveals a useful collection gap, first identify the precise question, existing evidence source and smallest safe on-demand improvement; justify its resource cost and failure behavior before adding infrastructure. No guarantee of complete evidence or zero resource cost is made.

The prior P01.2b feature-specific implementation manifest, B01-B09 delivery gates and theoretical early-coverage promises are historical conditional designs, not outstanding blockers for a feature the operator declined. This does not waive the established non-interference, custody, redaction or validation obligations for any future actual change. P01.1/P01.2a acceptance and the outstanding issue-driven P01.3-P01.6/P02-P05 and incident-recovery work retain their owners; no incidents are cleared and no business result is inferred.

Preserve E72-E74 and the private inert fixtures as rejected-design evidence; do not install or rerun them automatically. No runtime, SQL, task, policy, service, production or deployment change accompanies this decision. The documentation/archive carry-forward obligation survives cancellation of the instrumentation feature and belongs in the next appropriate authorized reliability PR/promotion; this creates no PR or publication authorization.

This update is documentation only. Validate links, current status, archive preservation and the documentation gates. Runtime tests, smoke imports, command registration and a Changes security scan are skipped because no runtime, imports, configuration, permissions, dependencies or executable fixtures changed. This decision adds no optimisation backlog item: the proposal is declined, not deferred for tuning.

## Starting state and required reading

1. Read root AGENTS.md, README-DEV.md, the reference index and required core standards.
2. Read the P01.2a closeout above, the active scope/tracker, and the P01 design's
   P01.2b and R1-R8 sections. Preserve all existing finding/acceptance IDs.
3. Read the protected startup/shutdown/diagnostics runbooks, Windows ownership/access
   contract, S11 deployment/restart contract and Promotion Guide where applicable.
4. Inspect exact deployed-equivalent source and installed-binding evidence before
   finalizing the file manifest. Do not use the old root checkout as deployed source.

Observed source pins at handover:

- Deployed private `67c4e12a8ecf0c25280770860480ac65a6826602`; updater manifest
  `b7dd6757ea4405ff7e89b5f5290d4d046bf410688b4e06536d994ed9c55b81a7`.
- Existing private checkout:
  `C:/discord_file_downloader/.codex_artifacts/a1b-updater-correction`, reviewed HEAD
  `6889d1cfc5c5db230d1f57adab475bbf8effb1f0`; `production/main` has the merged target
  with the same tree. Recheck before use; retain this completed branch/evidence.
- Existing mirror checkout:
  `C:/discord_file_downloader/.codex_artifacts/p1-mge-mirror-review`, reviewed HEAD
  `6f58f87829de1f663eda8a091c9169dc5afd6ca6`, mirror merge
  `cb705ad938dfeff53abb8c7ec0df06066af23791`. Mirror/private histories differ;
  production promotion remains patch-based after local validation.
- Canonical local programme documents are in `C:/discord_file_downloader/docs/`.
  Root HEAD at this handover is older `a025adb7a69aac321fd62794b871ed5903338f44`
  on `codex/p1-mge-a1b-design`, with pre-existing uncommitted docs. Do not reset,
  stash, discard, indiscriminately stage or treat this runtime tree as current.
- SQL source of truth: `C:/K98-bot-SQL-Server`, locally observed
  `7e91989f619deb46836194c7e705b0a9eb2ebe11`; no SQL change is assumed. Revalidate
  any SQL-facing design against definitions before implementation.

The closeout retains exact source/test/security/package paths. Latest production
inputs are Report 73 ZIP, ordinary part 2, updater transcript and logs, all hashed
in `p012a-recoverable-qualification-20261104/report73-validation.json` under the
private artifact root. Earlier Reports 70-72 are evidence of corrected gaps, not
current acceptance blockers. Preserve their original observations and failed tests.

## Problem and intended result

An issuer can fail before a successor journal or ordinary Python logger exists.
The wrapper starts it with `Start-Process -PassThru` and records a PID; PID alone
does not establish that startup succeeded or why it exited. The earlier archived
launch gate is historical source evidence, not proof of current installed binding.

P01.2b must let an authorized operator reconstruct the attempted launch, early
failure and handoff to normal evidence even while the bot is offline. Reuse the
P01 contract for safe reporting. Never turn diagnostic evidence into authority to
release ownership, replay a request, start a second issuer or weaken protected custody.

## Required scope and ownership

| Work | Required result | Likely layer / source to inspect |
| --- | --- | --- |
| Installed binding census | Identify actual wrapper, gate, issuer, Python path, policy/source digests, principal/elevation and enabled scheduled/manual paths; distinguish source/archived/installed facts | Protected launcher and existing installed updater/status evidence; P02/F31 retains wider installed-path inventory |
| Launch evidence | Attempt identity, intent/reference, source/policy binding, issuing/executing actor where known, PID plus creation identity, spawn/exit UTC, exit code and allowlisted stage/type | `start-bot-after-sql.ps1`, `scripts/run_export_startup_issuer.py`, reviewed launch gate/package |
| Pre-logger failure | Useful evidence for missing Python, invalid policy/custody rejection and immediate issuer exit, even without a Python journal | Narrow launcher/supervisor path; no arbitrary text edits in `release_seed` |
| Bounded stderr | Redacting collection with bounded retained bytes and bounded resources; drain/discard overflow so capture cannot block the child; explicit truncation/loss | Privileged capture and safe projection, using existing helpers where appropriate |
| Journal/exit race | Correlate early record with later incarnation/journal without deleting the first attempt or inferring success from exit/PID | Existing issuer/pair/deployment contracts; diagnostic and correctness receipts stay distinct |
| Online/offline access | Safe early-start projection in the existing bundle; bounded operator export through installed protected updater/status when Discord is unavailable | Service/report projection plus protected tool; unelevated bot must not read privileged raw evidence |
| Compatibility and rollout | Exact reviewed source/reader/updater transition; preserve all historical transitions and old-reader boundaries; state upgrade prerequisite | Preparation policy, transition registry, package/installer/upgrade tests only if necessary |

Review the actual runtime ownership and whether supervision can observe exit without
extending blocking work or changing parent task behavior. Choose the narrowest
supported design after inventory; do not assume the provisional file list is final.
No new top-level Discord command is assumed. No SQL schema mutation is assumed.

## Invariants and resource decisions

- Exactly one launch per original authorized start intent. No fallback launcher,
  automatic repeat start, synthetic incarnation or timer-based release.
- Unknown exit or partial evidence stays unknown. PID/exit code is not proof that
  the issuer/bot pair or SQL work terminated. Recycled PID must not inherit identity.
- Preserve original logs/artifacts and authoritative receipts through failed reads,
  malformed evidence, capture failure, custody rejection and interrupted publication.
- Keep step, initiating/executing actor, requester, logical owner, physical holder,
  timing and outcome separate. Record explicit collection limitations, not fabricated
  identities. Native SQL holder coverage stays P02.
- Optional capture cannot change the business result, weaken ACL/owner/reparse-point
  checks, consume unbounded memory or deadlock on stderr. Privileged raw content is
  not exposed to the bot or copied wholesale into a report.
- Set and justify numeric byte/node/count/queue/history/time limits in the design.
  A collection budget is not a worker lifetime. Preserve bounded useful evidence and
  recoverable export progress; document any intentionally unavailable source.
- Retain first entry, first failure, deadline/cancellation and terminal milestones,
  schema/version/provenance, current versus restored counters and publication status.
- Respect the P01.2a two-generation/fixed-expiry frozen diagnostic retry contract
  when adding online components. Offline behavior needs its own explicit custody,
  retention and restart contract; do not silently inherit in-memory durability.

## Required qualification matrix

| ID | Required evidence before acceptance |
| --- | --- |
| B01 Binding and identity | Real deployed-equivalent gate/wrapper/issuer trace; known initiating/executing actors; PID/create-time reuse negatives; exact policy/source correlation. Installed uncertainty explicitly blocks only the dependent claim. |
| B02 Before Python/journal | Missing executable, bad policy, custody rejection, immediate/nonzero exit, no journal and normal journal creation. Preserve original failure; zero fallback/duplicate starts. |
| B03 Capture pressure | Unicode/invalid encoding, multiline/redaction attacks, oversized stderr, full pipe/queue, slow/failing reader/writer, disk/permission failure. No child blockage or secret escape; explicit truncation/drop provenance. |
| B04 Races and interruption | Journal appears before/after exit observation; cancellation while physical work remains; repeated cancellation; interrupted artifact write and lost reply; no false settlement/release. |
| B05 Access and offline export | Authorized offline operator can collect with bot absent; unauthorized/cross-scope/untrusted path or link rejected; raw privileged evidence inaccessible to bot; bounded ZIP/member/hash/continuation/retry semantics. |
| B06 Compatibility/custody | Actual historical readers, missing/corrupt/mixed schema and downgrade/re-upgrade; native Windows 5.1 execution plus owner/ACL/default inheritance/metadata/link/stream/handle cases and preserved originals. Distinguish surrogate-account fixtures from elevated installed qualification. |
| B07 P01.2a non-regression | Q01-Q12/R1-R6: eight startup neighbours, known actors, typed child/parent/verifier results, first/terminal milestones, publication/restore/counter provenance, 850-style retained incident prefix, exact cursor/hash/count, frozen retry, final authorization and physical ownership. |
| B08 Combined failure/cost | Actual multi-minute held work (retain the real 125-second regression), unavailable monitor plus budget expiry, cancellation and delivery failure; matched caller/latency/RSS/loop/drain tests with unchanged gates and no business effect. Do not weaken thresholds to pass. |
| B09 Release and natural acceptance | Exact Bot and any separate SQL diff review; package/source equivalence, required updater transition, reviewed operator plan, protected single start, then passive real online/offline evidence without manufacturing production failure. |

Confirm current names before selecting tests. Starting suites:
`test_export_startup_issuer.py`, `test_export_startup_custody.py`,
`test_startup_correction.py`, `test_prepare_k98_update.py`,
`test_combined_k98_update.py`, `test_export_issuer_deployment_exit.py`,
`test_p012a_recoverable_reports.py`, `test_recovery_evidence_bundle.py` and the
existing evidence-contract/operation/startup/owned-worker suites. Inventory shared
callers, not just these files. Use the chosen checkout's own Python interpreter.

Run architecture/deferred/security-routing/test-selection gates; applicable lint,
typing, pre-commit, smoke and command registration; focused and full suites with
operational-log isolation as warranted by the final diff. Parser-only checks do not
qualify launcher runtime behavior. Installed native SQL contention is not claimed
by fixture tests. Tests are not a substitute for exact Changes security review.

## Incident recovery and other carried work

P01.2b is not the fix that releases the old pipeline. The closeout's obligation table
assigns all remaining work. P02 addresses F09 contention/prevention; remaining P03
provides safe original-intent/remaining-stage continuation, durable receipts and
F28 sibling cancellation convergence; P04 handles grouping/retention/escalation;
P05 performs mandatory combined repository confirmation. P01.3-P01.6 remain open.

At the first design step, refresh the **plan** for the six historically open records
from retained evidence and identify the exact current read-only inputs needed.
Do not pretend Report 73 is a full incident census or use the old Report 68 IDs as
fresh authority. Do not require all 17,747 rows just to decide one exact dependency.
Before any affected deployment or repair, obtain current exact owners/versions,
receipts/closure and live-worker status through supported passive tooling.
Supported recovery may precede P02/P03 if independently safe; unsupported recovery
needs its reviewed implementation first. Never clear incidents to make a status
screen green, re-upload inputs or resend a provider mutation to repair bookkeeping.

The actor/holder distinction, unavailable admission preview, partial monitor detail,
512-root retention/child omissions, no first-failure-bearing Report 73 sample,
unobserved live retry/cancellation, empty event cache and degraded provider freshness
remain explicit evidence limits. They must not be silently converted into passes.
No P05 deferral may be used to leave a known in-scope P01.2b defect uncorrected.

## First deliverable in the new chat

Produce one concrete architecture/implementation/qualification packet: verified
current source and installed-evidence inventory; early-launch sequence and failure
boundaries; proposed record/export schema and bounds; exact changed-file/shared-caller
manifest; required native/isolated tests; compatibility/updater/security decision;
incident/deployment dependencies; and explicit residual owners. Reconcile B01-B09
with D01-D06/A13-A14 and the carried P01.2a tests.

No fresh runtime approval is inferred solely from the instruction to start the chat.
Do not ask to reapprove the accepted scope; present any needed implementation
decision only after the concrete packet is reviewable. No production repair,
deployment, restart, provider action, permission broadening or whole-repository
security scan is authorized by this handover.

## Documentation carry-forward

All root programme documents were already uncommitted at entry. Preserve them,
the new closeout/handover, both navigation updates and the three merged correction
task packs copied into the older documentation workspace. The closeout validation
manifest under `p012a-closeout-handoff-20261104/` lists exact files/hashes and the
pre-edit backup. These local docs are not yet a new merged documentation PR.
Carry the complete intended document set into the next authorized PR; do not
drop untracked scope files when moving to a current source checkout. Do not
commit unrelated root changes or re-promote mirror history into private production.

## Delivered-document archive - 4 November 2026

The user requested archiving delivered packs after this handover was created. P01.1/P01.2a records now reside in `docs/task_packs/archive/`; follow the updated closeout links and [archive register](Startup%20Import%20Export%20Reliability%20-%20Archive%20Register%20-%202026-11-04.md). All active documents retain their current paths. The newer `document-archive-20261104/archive-manifest.json` under the private artifact root supersedes the older closeout file-location manifest; preserve both receipts and carry the destination files into the next authorized PR.

## Required next-PR and production carry-forward

The operator explicitly requires all documentation updates and all ten archive moves in the next P01.2b PR and its private production promotion. Follow the [portable documentation/move manifest](Startup%20Import%20Export%20Reliability%20-%20Documentation%20Carry-forward%20-%202026-11-04.md). Verify actual PR file lists and final trees against every required path, including source removals where applicable, repaired links and both navigation indexes. Missing documentation is a release-readiness failure. Carry this requirement into the implementation packet, PR description, promotion checklist and final handoff; do not rely on ignored local artifacts or runtime-only patch selection.
