# P02 running-release verification correction

## Approved scope and evidence

The operator approved implementation, offline tests, review management and merge
of mirror first, then the equivalent private patch once all gates are green.
Keep MINI_AMD running. No restart, failed-release replay, business recovery,
provider probe, SQL migration or VM action is authorized here. This follows the
[retirement correction](P02%20-%20Failed%20Readiness%20Retirement%20-%202026-11-18.md).

The original failed release is retired without readiness. The fresh release
completed source/seed and launched its successor; initial admission reported
installed. Its bot, authority and issuer matched the retained creation times and
executable paths in the passive snapshot. Independent post-start SQL schema
observation refused admission. Start completion and readiness remain
unconfirmed/unstarted. Preserve both failures, receipts and active selection.

The original SQL result and holder remain unknown: the old message combined
timeout, cancellation, deadlock and invalid-request results. Contention with a
live publisher is plausible, not proven. Separately, readiness classified a
historical observer-busy warning as permanent admission failure. This later
branch was not reached in the observed failure.

## Design and invariants

Do not replace Exclusive schema observation with Shared or unguarded reads.
Publishers hold Shared transaction ownership while changing outputs; maintenance
uses Exclusive session ownership. Retain exclusion and the complete installation,
legacy and application SQL comparators. Do not retry acquisition, pause producers,
start transactions, widen permissions or infer health from admission alone.

`SchemaObservationRefused` retains the acknowledged code and remains compatible
with existing `SourceConflict` callers. Only the separate verification entry
point treats -1 as pending. Cancellation, deadlock, invalid requests, contract
drift and unconfirmed acquisition/release/cleanup refuse acceptance. Initial
startup remains fail-closed, without automatic retry.

An offline builder seals current reviewed helpers and the complete contract
archive into a new protected packet. The private profile pins host/SID, active
selection, target, manifest/bindings, five receipts, start request, successor
journal, original retirement and failure evidence. No installed updater, live
source, task, policy or old sealed packet is overwritten. Profiles and host
evidence stay outside Git.

The launcher holds the operator and original release execution locks, and native
process handles across verification. It validates protected source, seed, task,
policy, physical drain, three-process identity and original receipts before and
after observation. Python also checks token/executable identity, publication,
manifests, recorded termination, exact initial admission, all SQL contracts,
closed predecessor and single open successor session, retained preparation and
resource ownership, and contained-stream evidence. Other streams must belong to
the verified successor. No business action is dispatched.

New dedicated application connections use no pooling or retry, a 3-second
statement timeout and zero lock wait. One 45-second/256-statement dispatch budget
spans SQL observations; an already dispatched statement or connection setup may
finish under its own timeout. No forced worker termination occurs. Cleanup is
attempted once per owned resource; uncertainty cannot become pending or accepted.
These verifier budgets do not add runtime or production memory prerequisites.

Both readiness paths preserve refusal for explicit closed/disabled admission and
unknown coordinator errors. Exact `error_type=ObservationBusy` warnings retain
degraded fresh import/export evidence; they cannot replace current contract and
native checks. Startup log reads remain bounded to 8 MiB, including growth.

After current Discord confirmation and one successful verification, the launcher
writes a separate immutable `verified.json`, kind
`running_release_verification_v1`, with profile/attempt hashes and explicit old
stage limitations. Original start/readiness receipts are unchanged. The active
pointer is retained for a subsequent reviewed metadata-only finalization. A
matching existing acceptance is historical evidence, recognized without another
SQL attempt. Pending/refused attempts are retained; they authorize no retry.

## Architecture and validation

Operational code stays in `scripts/`; the shared schema guard owns its typed
refusal. Reuse the existing source/custody/native helpers and full comparators.
No commands, views, caches or business flow changes. The older closeout helper
has a different pinned two-incarnation contract and is not valid for this release.
The next source transition registers the two shared Python changes as one exact
family; all 93 historical registry entries and their hashes remain unchanged.
This future-update registration does not authorize applying source on MINI_AMD.

Validated against `C:\K98-bot-SQL-Server`: ExportExecutionSession,
ExportExecutionStream, ExportPreparation, ExportResource and publisher schema
locks. Query values are parameterized. SQL uniqueidentifier transport values
are canonicalized to match retained SqlClient evidence; hashes and other text
are not normalized. No SQL diff/migration; SQL Changes review is a no-diff skip.

Regression coverage includes profile/payload pinning, malformed inputs, exact
lock results, no repeated acquisition, observation budgets, cleanup uncertainty,
native and journal drift, failed admission, session lineage, retained ownership
and contained streams, transient versus terminal readiness, actual PowerShell
orchestration and immutable acceptance. External effects use fixtures; this is
not native SQL or production acceptance. Preserve intermediate test failures.

Security routing: **Changes**, Deep off, immutable final mirror base/head, then
the equivalent private patch. All changed files and relevant custody/persistence
callers require review. Final hosted reviews/checks and actionable-comment
disposition precede each merge. No repository-wide scan is selected.

## Delivery and operator sequence

1. Complete focused tests, architecture/deferred/security-routing/SQL guards,
   test selection, imports, command registration and full hosted CI. Complete
   final-head Changes and hosted reviews, then merge mirror.
2. Apply the reviewed delta onto private main. Verify equivalence, pass private
   gates and merge. This does not deploy or restart the bot.
3. Build/hash the private packet from final reviewed source and retained profile;
   validate the complete generated packet in PowerShell 5.1. Supply exact files,
   hashes and a fresh host-custody preflight before operator execution.
4. Run only the separate verifier after preflight review. Preserve pending or
   refused attempts without retry. After acceptance, review updater `-Status`
   before selecting the existing metadata-only pointer finalization path.

## Preserved programme accounting

The prior adjudication remains authoritative: setup 400; native 563 (grouped
389); Windows 42 (grouped 13); control 0; prior reserve 32; insertion intents 7;
generated reserved 91,244 and remaining 908,756; historical rows 95, inputs 21.
Offline tests are separate; no refund/reset or qualification charge.

E1 stays closed; E2 is retained without replay; E2-E4 remain paused. All three
observed activation flags stay unchanged and do not override that pause. P02 D7,
P03 actual blockers, essential P04 corrections, P05 acceptance, P01.4/5 natural
checks, P03a.2 whole-flow acceptance and P0 remain open. Merge and verification
do not certify fresh provider delivery or whole-flow health.
