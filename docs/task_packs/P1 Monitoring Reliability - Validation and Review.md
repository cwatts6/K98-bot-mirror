# P1 monitoring reliability — local validation and review

> **Current status - 28 October 2026:** Monitoring and import/export reliability is
> accepted and complete for the deployed private `f6a929c0597ce257ce18380af1ab6f7ad8ddcc5d`
> runtime. Report 59, correct-data confirmation and `/stats player` acceptance close
> fresh-runtime R18. MGE signup/withdrawal remains open and leads the next Discord/domain
> scope. Full P1, natural event/publication checks and P0 rollover acceptance remain separate.
> See the [accepted closeout and complete remaining ledger](P1%20Monitoring%20and%20Import%20Export%20Reliability%20-%20Closeout%20-%202026-10-28.md),
> [next scope](P1%20Discord%20Domain%20Completion%20and%20MGE%20-%20Scope%20-%202026-10-28.md) and [new-chat starter](P1%20Discord%20Domain%20Completion%20and%20MGE%20-%20Chat%20Starter%20-%202026-10-28.md).
> Earlier dated status/next-action statements below are historical where superseded.
> This documentation update requires no bot restart, repeat import/export or SQL apply.


26 October 2026. This records the approved local implementation and review;
publication, promotion, deployment and runtime acceptance are separate.

## Review verdict

Ready for mirror PR review as an integrated local candidate. No unresolved
implementation finding remains from this review. Production promotion is not
approved or prepared by this task. The bot/authority release must retain the
protected paired-release process and obtain a separately reviewed exact source
transition. No updater capability or production source pin was changed here.

Base: `01b6a9905176b6e8a9f4d34776c172fd01a76d01`.
Increment A: `fddc4b6b` (retained observations and private acknowledgement diagnostics).
Increment B: `4333a1bc` (active priority, history budget, shared SQL probe), corrected
by `30847695d17d87f19148253abff4b9b7f3ee7ae7` (verified history recovery).
The integrated branch is `codex/p1-monitoring-work-budget`; the A branch is an
implementation checkpoint, not a separately fully validated publication bundle.

The implementation and its explicit detection-latency tradeoff are described in
[the implementation record](P1%20Monitoring%20Reliability%20-%20Implementation.md).

## Findings resolved

- Client-side response validation now recognises the exact bounded, read-only
  history-page contract. Malformed keys, Boolean flags and UUIDs fail closed.
- A failed reference cannot starve catalog rotation. A later unrelated successful
  page cannot clear its failure. Waiting/deduplicated checks do not constitute a
  verified sweep; a successfully observed empty catalog can recover an initial
  inventory failure.
- Shared process-local monitor state is isolated between tests. Notification tests
  create separate exceptions per attempt so accumulated mock traceback frames do
  not manufacture distinct error fingerprints.
- Historical source assertions traverse an exact test-only successor mapping.
  The mapping and successor bytes are both pinned; altered source, altered mapping
  and missing mapping are rejected. Original release fixtures and production
  updater scripts/registry are unchanged. This is verification data, not authority
  to install this candidate.

## Tests and validation checked

The first full offline run used the existing root-checkout interpreter:
**9,539 passed, 1,080 skipped, 36 failed, 8 subtests passed**, in 17m32s.
The captured result is `.pytest-monitoring-full.log` in the worktree, outside
production logs. It must not be described as a green full-suite run.

All 36 failures were accounted for: 18 exercised the real interpreter-location
guard; 17 detected changed source bytes through historical release assertions;
one used the reused-exception notification fixture. The guard was preserved. A
real worktree-local `.venv` was created and uses the already installed dependency
directory through a test-environment `.pth` file. No installation or credentials
were changed in the root checkout.

The final combined affected suite, run through
`scripts/analyse_pytest_log_noise.py` with the worktree interpreter, completed:
**546 passed in 36.84s; production operational logs unchanged**. It includes every
historical-hash helper consumer, all originally failing areas, the new negative
source-bridge tests, monitor/runtime/notification tests, private responses, retained
health workers, evidence RPC, backlog and complete reports. The log is
`.pytest-monitoring-final.log`. Two new isolated-fixture omissions encountered
during the combined rerun were corrected before this passing result.

The whole unrelated suite was not repeated after these fixes: the full run already
covered it, and the final run exercises every changed helper consumer and all
failures. No unresolved test failure is being waived. Live SQL integration tests
retain their explicit disposable-database opt-in and were skipped; no installed
database or provider was used.

Additional checks passed:

- Ruff and Black checks on changed Python files; Git whitespace check.
- Architecture validator (48 Python files at final validation).
- Deferred-item validator (18 Markdown files) and security-routing validator
  (zero errors and warnings).
- Test selector, using the exact base-to-candidate file list. Its initial default
  comparison also included earlier unreleased mirror history; that broader list
  was not mistaken for this task's diff.
- Smoke imports using the repository's isolated test environment. An initial run
  without that environment failed on required configuration; no real secrets were
  loaded to satisfy it.
- Static command registration: 36 primary commands, 102 detected grouped
  subcommands, no unexpected drift or active duplicates.

The controlled before/after run executed the original observer function from the
base Git object and the new function against the same 17,631-reference fixture:
active delay 100s to 0s before history; inspections per turn 100 to 10; modeled
inspection-cycle time 100s to 10s. This measures the intentional scheduling tradeoff,
not production throughput. SQL/provider costs and production sweep targets remain
unmeasured. The complete-report regression retains all historical rows.

## Security review gate

Both reviews used **Changes**, with Deep off, and completed with zero reportable
findings and complete requested diff coverage:

- Primary `370d2e1e-f7c2-4fcb-a15c-5c2121531883`:
  `01b6a990..4333a1bc`, all 11 production files and seven test/documentation files.
- Follow-up `04af553b-d91f-41d8-9951-4f7397b86b9c`:
  `4333a1bc..30847695`, the corrected runtime and accompanying tests/documentation.

Canonical reports are retained by Codex Security. The primary review's reliability
observation was fixed and covered by the follow-up; zero security findings did not
substitute for correctness review. No production exploit, SQL, provider or Discord
operation was performed. The supplied root SECURITY.md model was retained.

The final source-hash fixtures, historical-test adaptations and this review record
received a documented security-scan skip: they run only in the offline test harness,
pin exact generated source hashes and preserve negative checks. They change no
production source, deployment registry, permission, configuration or input path.
The runtime tree remains exactly the tree reviewed through `30847695`.

Tool-reported usage, including cached input: primary 3,843,566 total tokens
(3,757,056 cached input); follow-up 603,742 total (598,784 cached input). These are
the plugin's accounting figures, not a new-token or cost estimate.

## SQL, promotion and residual boundaries

New DAL queries were checked against authoritative SQL repository `1e95e41d`:
RecoveryIncident scope/kind/state and RecoveryAction incident/state fields,
constraints and indexes. Queries are parameterised and read-only. No schema,
ProcConfig, activation, permission or migration change is needed for this source
change; installed SQL performance and integration remain unverified.

At the local implementation checkpoint, no PR was published, pushed or merged. No production deployment, restart,
provider action, SQL operation, incident reopening or release acceptance was
performed. A clean local candidate does not establish loaded production code.
Preserve R01–R18, WS1–WS6 and P0 F04/F01–F05/new-runtime export boundaries exactly
as carried in the implementation record. SQL timing/index follow-up is captured
there in the required deferred format; it is not part of this implementation.


## Publication and updater preparation

The release adds one fixed installed-tool transition,
`p1_monitoring_reliability_v1`, for the exact 11 runtime files. It authenticates
both predecessor and target bytes, requires the whole bundle, and keeps historical
transitions unchanged. The registry remains below the existing 64 KiB bound.
Tests reject missing, extra, renamed, duplicate, foreign and altered members,
including both ends of the typed pending-page RPC. Target metadata cannot grant
itself admission; the installed updater must first receive the reviewed policy.

The production publisher previously excluded the generic private-status response
module and its synthetic tests because their filenames matched `**/*private*`.
Two exact root-anchored exceptions now retain those reviewed source files. Broad
credential filters remain; nested copies, backups and key-suffixed files remain
excluded. The exact publication payload passed a redacted Gitleaks scan.

This deployment/filter change requires a new Changes security review with Deep
off on the final mirror and production ranges. The earlier test-only skip above
does not cover these release-policy changes. Final PR, merged-source, updater
package and verification evidence belongs in the local operator release packet.
