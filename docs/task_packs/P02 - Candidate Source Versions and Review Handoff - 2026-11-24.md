# P02 - Candidate Source Versions and Review Handoff - 2026-11-24

## Hosted CI correction follow-up - 24 November 2026

The source drafts are [mirror #550](https://github.com/cwatts6/K98-bot-mirror/pull/550),
[private Bot #751](https://github.com/cwatts6/k98-bot/pull/751) and
[SQL #159](https://github.com/cwatts6/K98-bot-SQL-Server/pull/159). They remain
unmerged. SQL CI passed all steps. Private updater, release-identity and credential
checks passed on the earlier candidate; the full Quality job exposed one missing
blank line, then 26 type-check errors in P02 qualification/release helpers. Both
first failures are retained. The formatting-only fix has identical AST/literals.

The focused correction makes ten type-only changes with identical executable
logic after annotations are removed. It also explicitly refuses a protected
policy that disappears between the existing selection reads, before reading any
source blob. Its negative regression checks that boundary. No SQL statement,
privilege, native packet, retry, physical ownership or receipt behavior was changed.
The type check passed with the shared interpreter (87 files, zero errors/warnings).
All 184 focused cases passed: the first group passed 131 and skipped 53 needing
retained source inputs; those 53 then passed against the genuine authenticated
archive and SQL worktree. Operational logs were unchanged. Required static gates,
in-process formatting and Ruff without fixes passed.

The exact twelve-file Changes review `9ff3839c-446a-4802-8ba6-cf71ba1ccf82`
completed with Deep off and no findings; canonical results were read back.
This following status prose has a precise documentation-only security skip.
Evidence is retained under `A/ci-types-24-01`, including before-images and
annotation equivalence. The post-commit receipt records the updated mirror and
patch-equivalent private revisions; earlier source identities below remain dated
checkpoints. All original SQL candidate/migration bytes remain unchanged.

The installed-updater controls require actual private `main` and exact SQL
ancestry on SQL `main`; a draft branch must not be relabelled to pass them.
Complete the source checks and normal source delivery before binding the final
release specification, registry and independent contracts. Rebuild the protected
tool package from those exact inputs: candidate 06 retains its old byte identity
and is not silently rebound to this correction. The grouped G0-G5 VM plan remains
non-executable until those inputs and the faithful fresh startup fixture are ready.
No merge, native execution or production deployment is performed by this checkpoint.

## Source review follow-up - 24 November 2026

The agreed continuation has published draft source reviews:
[Bot mirror #550](https://github.com/cwatts6/K98-bot-mirror/pull/550) and
[SQL #159](https://github.com/cwatts6/K98-bot-SQL-Server/pull/159).
Both are open drafts, not merged or deployed. The local-only statements below
remain the earlier source-freeze checkpoint.

The SQL source candidate is now `3dedeae2fde42a42d0bfa4102d3a36634b9d97eb`.
Its parent `3acf026cf9532ce647d643a6cd8a394d2cf8daab` and all 130 original
candidate files are unchanged. Six additional CI/test changes correct three
stale historical assertions and classify authenticated before/after release checks
separately from executable migrations. Original D3/D4 source pins and historical
payloads remain intact. The three corrected source checks and twelve sidecar
membership/refusal cases passed; the SQL repository validator passed with zero
errors and 36 retained warnings. The first long-path fixture failure is preserved;
the successful short-path run used fresh owned fixtures and executed no SQL.

The six-file Changes review `252b8d5a-ab0a-4001-8406-059f8268e07b` completed with
Deep off and no findings, followed by canonical readback. The retained earlier
Bot/SQL reviews still cover their unchanged executable bytes. This follow-up Bot
delta is status prose only and uses a precise documentation-only security skip.

The actual private main was verified as
`d3ca554cc0e706d9d18856ef74f07685e2c894dd`. The existing clean private worktree
is reused: all 148 mirror paths matched their expected private before-image and
31 private-only files are preserved. The private counterpart must be derived by
the normal patch-equivalent flow, not by pushing mirror history. Its eventual
commit is recorded in the local source-review receipt; neither the mirror SHA nor
a generated substitute may serve as the private release identity.

Evidence for this follow-up is under
`A/continuation-20261124/source-review-preparation-01`. The immutable initial
source-freeze evidence remains in `candidate-source-versions-01`.
No native packet was run, existing fixture was changed, or private configuration
copied. Review submission is distinct from merge, release readiness and installation.
The exact release specification/registry, installed startup and authority IPC,
compatible return/reupgrade and interruption qualification remain the next gates.
P02 remains OPEN; D7 remains 1/4. All remaining owners and no-replay boundaries
below continue to apply.

## Current decision

The user agreed to continue source review and record proper Bot and SQL Git
candidate versions. This is local source delivery preparation. No production or
VM change, source push, PR, merge, deployment or restart is performed by this
checkpoint. P02 remains OPEN and D7 remains 1/4.

The SQL candidate is committed on `codex/p02-observer-sql-proof`:
`3acf026cf9532ce647d643a6cd8a394d2cf8daab` (parent `73b004d4a834f87fe3e559480d99dd597995fd91`).
It contains the 130 reviewed SQL paths, including the observer and its bounded
compatible return/reupgrade. Its working tree is clean; original source bytes
are unchanged.

The Bot candidate is the local commit containing this handoff on the existing
`codex/p02-observer-proof` branch, based on
`8ef8514821783c0422c4747e61c0222f7ba3c459`. The post-commit receipt records its exact
identity without embedding a self-referential hash in this document. The candidate
contains the 147 previously reviewed paths plus this handoff. Existing historical
statements that the work was uncommitted describe their dated checkpoints.

Private local evidence:
`A/continuation-20261124/candidate-source-versions-01`, where
`A = B/.codex_artifacts/p02-observer-proof-20261119` and B is the existing Bot
worktree. `scope-and-baseline.json`, `sql-commit.json`, `bot-commit.json` and the
final validation receipt bind the exact source versions. Ignored evidence remains
in its existing directories and does not transfer through Git.

These are candidate source identities. The private Bot target is still pending
normal mirror-first review and patch-equivalent private promotion. Do not use the
mirror candidate commit as an installed private revision. The recorded running
Bot `3a2694f7fc61606a3758eb8bf64065209f90c7d4` and private parent
`d3ca554cc0e706d9d18856ef74f07685e2c894dd` remain dated evidence, not fresh production
observations. No private configuration was copied, replaced or invented.

## What the candidate changes

The Bot uses coherently versioned catalogue observation and shared admission
controls across the reviewed import, reporting, maintenance, startup and recovery
callers. The companion SQL observer invalidates that evidence when the covered
catalogue or lifecycle state changes. Existing ownership, uncertain-outcome and
producer controls remain authoritative.

The bounded return/reupgrade reuses existing release locks, drain and resource
checks, transactions and receipts. It preserves original migration/incarnation
history. Operator-controlled return is eligible only in the proved drained
no-business window. Acknowledged business effects, unknown absence of effects or
unresolved physical ownership stop return and require review/forward correction.
The original observer migration is never replayed or relabelled.

## Review and validation

All executable files match the retained completed Changes reviews. The latest
Bot review is `6d5d6cf3-f614-4b5a-9aa5-86e7945c7a94`, carrying the earlier
`fa8c79fd-ebd3-4063-9c74-7529bb0c0058` and predecessor coverage. The SQL review is
`d33d3f57-624e-417d-b1aa-687217860f00`, carrying its exact-byte predecessor
coverage. All three canonical completed results were read back; no findings were
recorded. Deep was off. Native limits and the previous review exclusions retain
their documented reasons. No generic new scan is substituted for that evidence.
The current delivery delta changes status prose only; a precise documentation-only
security skip covers it.

Architecture, deferred-item, security-routing, SQL-alias inventory and command
registration checks passed during source preparation. Test selection was run.
Prior focused checks are reused because executable bytes have not changed:
149 Python return/policy/release cases; 18 return, 22 observer, 22 D4 and 33 Phase1
PowerShell runner cases with external SQL/process boundaries substituted; later
24 readiness-launch, 12 reader-ownership and 33 startup-read checks within their
recorded scopes. Existing native report/cost/type/concurrency evidence is retained
without replay.

The historical full regression is not all green: 15,922 cases included 14,590
passes, 55 failures and 1,277 skips. The 37 related stale fixtures were later
corrected with 130 focused passes; 18 unchanged Windows shared-interpreter guard
failures remain. Private-free smoke imports still lack required `OUR_KINGDOM`
configuration. Neither limitation is hidden or repaired by copying private config.
No additional full suite or VM test is justified solely by recording unchanged
source as a commit.

Staging exposed 42 trailing-whitespace warnings in the three new migration files.
Every warning is inside the exact authenticated `sp_ExcelOutput_ByKVK` definition,
14 in each forward/return/reupgrade image. Those historical body bytes are required
by exact comparisons and are deliberately preserved. The first staged-check output
and line-by-line adjudication are retained; all other staged SQL paths pass.
No repository-wide whitespace exception or formatting change was introduced.
The staged blob comparison accepts only unchanged bytes or normal Git CRLF-to-LF
conversion, and rechecks that the working files remain unchanged.

## Remaining source and VM gates

1. Complete normal mirror-first source review and patch-equivalent private Bot
   promotion. Obtain the actual final private Bot target and reviewed SQL target;
   preserve private configuration and do not manufacture source or migration
   history. Source publication/merge is distinct from installation.
2. Bind those exact targets to the protected release specification, registry,
   complete dependency package and independently derived successor contracts.
   Rehearse complete release preparation offline against the observed updater.
3. Prepare the faithful protected lab startup fixture, preserving the original
   disabled task, guest-only XML, policy and ACLs. The accepted metadata read
   proved the task/operator account match, while the action/state binding remains
   opaque. A new standalone metadata read is not selected.
4. Seal one grouped VM packet for native tool transition, actual configured-runtime
   preparation and authority IPC, necessary interruption/drift stops, exact
   no-business return/reupgrade and owned settlement. No full ordinary bot startup,
   provider login or business acceptance is claimed by this isolated group.

The accepted metadata packet `startup-binding-20261124093331147` has raw receipt
SHA256 `4d1ad156c8408f46c692f84b7d1592e69c206ef29930254206d7e4aa60c6b845`.
It and every completed/failed predecessor remain forbidden to rerun. Retain
`P02LabSession`, `P02StartupBindingJob`, `P02ReadinessJob` and
`P02ReadinessPriorJob`. DB27 remains ineligible for return because it contains
acknowledged business effects. Existing fixtures, protected spool and backups
remain untouched; attached virtual disks are not read or changed here.

Genuine admitted legacy all_kvk capture remains a separate P02 gap. The retained
census found closed genuine KVK 13-15; KVK16 uses the snapshot route. Do not ask
for a nonexistent KVK16 Full Data scan, fabricate input/checkpoints or reopen a
season. The original 68 requirements, 73 policy pairs and L1-L9 are unchanged.
P03, essential P04 corrections, provider receipts, fresh E5 and P05 combined
acceptance retain their separate owners. E1 is closed; failed/not-applied E2 is
retained; E3/E4 remain paused. This handoff is not deployment approval.
