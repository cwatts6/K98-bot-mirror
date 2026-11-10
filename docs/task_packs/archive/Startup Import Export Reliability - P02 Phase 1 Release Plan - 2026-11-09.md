> **Archived 9 November 2026:** Superseded or completed Phase 1 instructions. Preserve the dated evidence below; do not replay its commands. [Current P02 scope and dependencies](../Startup%20Import%20Export%20Reliability%20-%20P02%20Remaining%20Work%20Handover%20-%202026-11-09.md) govern remaining work. Deployment is verified; standard production import/export acceptance remains open.

# Phase 1 coordinated release plan - 9 November 2026

Status: isolated functional qualification and source security review passed.
The fixed SQL package is in draft PR 138. Bot mirror review, private promotion,
final remote checks and separate production approval remain release gates.
No production installation, restart or business action is authorised by this document.

## What changes

- Summary SQL calculates the required endpoints directly instead of rebuilding
  the old full-history intermediate tables for each report. Existing report
  meanings, player membership, aggregates and rolling windows remain checked.
- All reports use the same latest nonempty player name. Historical reports show
  the latest display name while their historical statistics stay historical.
- 139 columns across 31 summary/output tables use exact integer types of the
  required size. Large counts use bigint; this is not an indiscriminate int conversion.
- The Bot preserves exact numbers through capture, saved exports and reload.
  Existing queued payloads keep their own immutable content and identity.
- The selected recovery inspections use short snapshot reads, avoiding the
  demonstrated reader/writer interference while preserving action-time checks.
  ALLOW_SNAPSHOT_ISOLATION becomes ON; READ_COMMITTED_SNAPSHOT remains OFF.

Expected results: less repeated SQL work, consistent latest names, exact integer
exports, and recovery/status inspections that do not obstruct the tested import.
The 13.375-second isolated producer/report result is evidence for that rehearsal,
not a production speed guarantee or a name-performance benchmark.

The deployment installs definitions and types; it does not recalculate reports,
rewrite queued exports or run an import. Materialized report names are published
by the new report-completion path on the next separately authorised normal run.
Shared-name views read the latest name directly. No stale cached output should be
presented as newly recalculated merely because installation succeeded.

## Evidence already established

- One final integrated 415-row import; all 14 local exports independently verified
  across 49,468 rows and 827,683 cells, including actual immutable Bot payloads.
- Observer-first and writer-active inspection, 30-second metadata reader, exact
  connection cleanup and five balanced OFF/ON timing pairs qualified.
- Full production inventory matched both protected startup fingerprints and all
  139 starting column definitions. Native local fixtures reproduced all 57 exact
  deployment before-images and the 26 qualified installed SQL bodies.
- Full migration batch: fractional/out-of-range refusal, late-failure rollback,
  exact postimages and exact transactional rollback checked locally.
- Both old and new startup contract validators passed offline against the sealed
  evidence; successor values are derived independently, never adopted from a
  live post-deployment observation.
- Production inventory recorded no active resources, nine open incident records,
  a full backup at 01:00 on 9 November and a log backup at 10:00. These are a dated
  observation, not a substitute for deployment-time revalidation.

Private receipt references and checksums remain under `.codex_artifacts/p021`.
Do not publish raw inventories, player data, installed policies or private receipts.

## Fixed installation boundary

The single migration identity is `20261109_001_p02_phase1_sql_exports`, selected
through the `p02_phase1_v1` coordinated profile. The profile is pinned to
`520b58c1b25d80bd28f32324d99b5fede0d6191ddab93ac93469ed5c1f6e4041` and its SQL batch to
`6cc6cb23b0af1123d7c86b4e47c2485880aee0cbfc097b2b5306a746da8a23fb`.
Only the 57 reviewed objects are eligible. Existing coordination/ownership
objects, permissions, provider settings and retained incidents are not amended.
The installed Bot predecessor is `6cb5d8ed532a8b1e34ad58ed230daa74d5ba77a3`.

The updater admits the complete 25-member Phase 1 runtime/source family together,
bound to this SQL profile and the exact old/new startup contracts. A partial family,
source-only introduction, changed SQL body or mismatched predecessor is refused.
All 68 earlier transition definitions remain unchanged.

## Delivery sequence

1. Finish separate Bot and SQL Changes reviews and local validation. Record the
   exact SQL commit, final Bot candidate and updater package hashes. Do not use a
   placeholder revision or a regenerated live SQL fingerprint as release authority.
2. Review/promote the SQL source, preserving the exact selected commit in SQL main.
   Review the Bot mirror PR, then create the production branch from private main
   using the authorised patch-based promotion flow. Never deploy mirror history.
3. Present the exact reviewed production target, updater upgrade and stage-specific
   recovery instructions for separate production approval.
4. On approved production MINI_AMD, install only the exact-version updater upgrade.
   It preserves the installed predecessor and does not itself install Bot or SQL.
   Prepare the coordinated release using private Bot main and the pinned SQL commit.
5. Before drain/apply, revalidate changed-file custody including new paths and
   ancestors; original policies, source/SQL fingerprints, process ownership,
   retained work, backup freshness and resource capacity. Require a full backup
   within 24 hours and log backup within 30 minutes under the existing FULL model.
   An unresolved active owner stops the release; incident counts alone do not.
6. Drain through the existing coordinator. Record the same release identity,
   enable snapshot allowance, then apply numeric and SQL definition changes in
   one transaction with exact before/after checks and the durable Applied receipt.
7. Install matching Bot source and protected successor startup templates, recheck
   all three actual application SQL contracts and permissions, start through the
   protected path, and verify readiness. Do not bypass any failed startup check.
8. Record installation separately from production acceptance. Resolve any exact
   retained-work prerequisite through its own reviewed recovery action; perform
   one separately authorised normal import/provider export for exercised acceptance.
   Never replay a completed operation or treat installation as provider delivery.

## Stop, rollback and resume

| Observed stage | Required response |
|---|---|
| Preflight refused, no mutation | Preserve the receipt and fix the specific discrepancy. No reset, retry of business work or relaxation of limits. |
| Snapshot setting enabled, SQL not committed | Inspect same-release status. Schema preimage must still match; snapshot allowance may remain ON and is reported separately. Resume only that release after drain; do not blindly toggle settings. |
| SQL batch fails before commit | The SQL transaction rolls back definitions/types and ledger changes. Verify exact preimages and actual snapshot state before deciding the next step. |
| Commit acknowledgement lost | Read the exact migration/deployment identity and postimages. A committed result continues remaining stages; it never reapplies SQL. An unknown or conflicting outcome stops. |
| SQL committed, source/seed/start incomplete | Keep the application stopped/drained and resume the same sealed package. Do not launch the old Bot against the new schema. |
| Failure after new imports or exports | Preserve outcomes and inputs. Use a separately reviewed corrective release or database recovery plan; never restore over subsequent work or replay unknown provider actions. |

There is intentionally no automatic post-commit downgrade to the old policy.
Recreating five primary-key constraints preserves their names but changes SQL's
system-generated-name flag, so simply restoring the old protected fingerprint is
incorrect. After new activity, the old full-history caches may also be stale and
reverse conversion can lose integers beyond the exact float range. Qualification
rollback utilities are fixture tools, not production rollback commands.
Same-release forward completion is the supported recovery after a committed SQL
step. A backup restore is an operator recovery decision with explicit treatment
of later writes and durable import/export outcomes, not an automatic release step.

## Limits and work remaining outside this release

Keep disk reserve at least 8 GiB, sampled log use below 70%, version store below
512 MiB, and existing command/timing limits. The one-run 21-input allowance is
exhausted and no additional rehearsal input is requested. No production memory
allocation, RCSI change, file-command enablement or permission widening is included.

The nine retained incidents are not cleared by the installer. The two newly
examined player-report preparations were unavailable and had no linked output
streams; that observation is not evidence of delivery or permission to replay.

P02 D2-D4 remaining observer/connection/maintenance/legacy work, wider D5 fault and
restart qualification, and deployment/provider acceptance remain open. Raw-history
snapshot readers crossing DDL (SQL 3961) remain separate from the qualified
metadata reader. Existing unspecified equal-score ranks remain unchanged; stable
tie ordering stays recorded as a separate decision, not a silent release addition.

## Final source review and packaging record

The selected SQL commit is `a202a51440f17233800b49801bd31c3ead2a9227`.
It includes the original [SQL PR 138](https://github.com/cwatts6/K98-bot-SQL-Server/pull/138)
and the bounded preflight correction described below.
The Bot descriptor and installed updater candidate pin this exact revision.

- 130 native SQL tests passed. The later migration header added only a closed
  720-byte comment; its executable suffix is byte-identical to the qualified batch.
- 23 fixed-package runner tests, repository/encoding/selection gates, P0 business
  equivalence, 863 historical permission checks, 80 direct-permission checks and
  historical target-publication checks passed. Historical manifests remain
  immutable and are tested at their pinned predecessor; they do not admit new
  Phase 1 bodies. The current package has its own authenticated admission checks.
- The actual old/new startup contract validators passed 11 checks; the complete
  six-member SQL payload and tamper refusals passed seven integration checks.
  Final release/transition tests passed 154 cases; Windows fixture checks passed 45.
- Bot and SQL Changes scans completed with no findings. The additional four-file
  SQL validation/CI change received a separate completed Changes scan. These are
  source reviews, not proof of production installation or provider delivery.

The post-scan comment and derived hash/commit updates were independently checked:
no executable SQL, permissions, object scope, limits, ownership or deployment
decision changed. The legacy expected metadata digest was re-derived because it
includes the fixed migration receipt checksum; application and coordination
contracts remain unchanged. The one-file Git line-ending rule preserves the
same authenticated migration bytes on Windows. The three test-fixture callables
now accept the new optional scope argument without changing their assertions.
The older MGE descriptor test retains historical admission checks and verifies
the current approved Phase 1 descriptor separately.
These mechanical packaging/test-fixture corrections do not require another
discovery scan. Retain their bounded delta proofs with the completed scans.

The first broad Bot test run stopped progressing while an unchanged maintenance
test repeatedly attempted a temporary file in an unwritable folder. A stack
capture identified the exact permission loop; no product fix was made for it.
The remaining test files were run with writable test space. Missing local Windows
DLL discovery was corrected for the test process only. Do not describe the
interrupted run as an uninterrupted full-suite pass; retain both logs and the
final remaining-file result in the release evidence.

SQL whitespace checks retain a narrow exception for historical SQL text embedded
inside three hash-bound migration bodies. All other changed lines pass. Do not
format those retained strings or weaken their fingerprints to silence whitespace.

No merge, production updater installation, restart, import, report, provider
export or incident clearing is authorised by source publication or this record.

Final regression reconciliation covers all 13,341 collected cases: 12,216 passed
and 1,125 intentionally skipped across the retained runs, with 33 overlapping
cases agreeing. All nine earlier failures were rerun successfully in a 116-test
follow-up. The completion run passed 1,025 tests with 117 skips. This is complete
case coverage across runs, not one uninterrupted run. Final mirror release,
numeric and snapshot checks passed 183 tests; lint passed for all changed Python.

## Production preparation correction

The first approved production preparation stopped before drain or SQL apply:
the actual server reports `mini_AMD`, while the release helper compared its name
case-sensitively against `MINI_AMD`. Read-only follow-up confirmed no active
update, no Phase 1 migration receipt, and unchanged database settings.

The corrected helper accepts casing differences only. Different hosts, named
instances, suffixes, surrounding spaces, database identities and disallowed
database settings remain refused. Native Windows PowerShell 5.1 reproduced the
original refusal, then passed all 33 corrected runner checks. A focused SQL
Changes security review completed with no findings. The migration body, profile,
startup contracts, object scope and resource limits are unchanged.

The Bot descriptor and updater pin the corrected SQL commit together. Preserve
the stopped preparation as evidence and upgrade from the inventoried currently
installed updater before preparing the corrected release. Production deployment
is separately approved; import/export testing remains outside deployment until
installation is verified.
