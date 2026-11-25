# MGE finalisation: deployment and confirmation plan

29 October 2026. Source merge and private promotion are authorized. **This is a
deployment plan, not permission to execute it or an executable release manifest.**
The [qualification packet](P1%20MGE%20Finalisation%20-%20Native%20SQL%20and%20Updater%20Qualification%20Packet%20-%202026-10-29.md)
owns the detailed N00–N16 / U00–U14 checks and approval ledger. Record actual merge
SHAs, native results and final package hashes in the handoff; do not infer them from
branch labels or this document's date.

## Changes and expected outcomes

| Change | Expected outcome and limit |
|---|---|
| Atomic completion and original-board target capture | An event becomes completed with its original delivery inventory in one transaction. This removes the gap between completion and recording final delivery work. |
| Immutable first payload and revision-qualified delivery settlement | Lost edit acknowledgement stays unknown; matching readback confirms it without another edit. Missing/inaccessible messages remain explicit holds. No replacement message is sent. |
| Completed event, signup and award freeze triggers | Later roster/event mutations are rejected at SQL even if a stale caller reaches persistence. Independent result import/read workflows remain supported. |
| Terminal and legacy-completed exclusion from routine refresh | Completed/confirmed/held/retired historical boards add no routine Discord work. No numerical latency or throughput improvement is claimed before measurement. |
| Bounded MGE updater profile and source transition | The existing combined release protocol coordinates the exact table/index/three-trigger family, source and startup seed with retained attempts and verified resume. Arbitrary profile SQL is not admitted. |
| Native harness and exact target guards | Disposable SQL can exercise real drivers, triggers, transactions, races and process loss after approval. Offline tests alone do not qualify Windows custody or production behavior. |

No new dependencies or activation flags are required. The configured ADMIN_USER_ID
remains the completion/retirement authority. Shared lifecycle policy does not enable
new Ark, voting or calendar behavior.

## Targets and preparation gates

| Target | Binding / required action |
|---|---|
| Reviewed Bot source | Mirror PR [459](https://github.com/cwatts6/K98-bot-mirror/pull/459), then an independently based private K98-bot PR. Deploy only the selected merged private-main commit. |
| Reviewed SQL source | PR [134](https://github.com/cwatts6/K98-bot-SQL-Server/pull/134); retain the final merged commit and migration/profile hashes. |
| Disposable SQL | Canonical `9SX2VF4\K98DEV`, transport `lpc:localhost\K98DEV`; proposed absent database `K98_MGE_Finalisation_Qualification_20261029_A`. Exact data/log/backup paths and unresolved backup access are in the qualification packet. |
| Production | Intended host `MINI_AMD`, database `ROK_TRACKER`; these are documented defaults, not a current live observation. Verify instance, database, installed Bot commit, tool manifest, source policy, custody, retained releases and SQL history/backup evidence before authoring bindings. |
| Protected rehearsal | A separately approved isolated root, exact predecessor tool/source, synthetic SQL target, elevation/account and fault-injection scope. No live repository or retained S11 database is a substitute. |

1. Complete source CI/review and merge SQL, mirror and private PRs. Preserve exact
   file/blob equivalence between mirror and private promotion; do not push mirror
   history into the private repository. Merge does not install anything.
2. Obtain scoped approval for disposable database creation, fixture writes, backup
   and named child interruption (A3). Resolve backup access/capacity first; create
   only the approved absent database, then bind its observed creation time, login,
   files, collation and compatibility. Retain fixtures and evidence; no cleanup.
3. Run N00–N16 at the exact reviewed source pair. Capture per-case results, ledgers,
   postimages and rollback/commit outcomes. Correct any failures through reviewed
   PRs; rerun the affected qualification. Do not mark unrun cases passed.
4. Obtain the bounded production read-only inventory (A4). Generate and review the
   production MGE profile and changed Bot descriptor from those observed values.
   Commit the SQL profile first, pin that reachable SQL commit/hash in the Bot
   descriptor, then review and merge the binding follow-up PRs. The old KVK
   descriptor is not an MGE release and must not be reapplied or deleted to bypass
   initial adoption checks.
5. Generate the authenticated updater upgrade against the actual installed tool
   manifest. Run installed-version compatibility and U00–U14 qualification,
   including protected Windows and end-to-end interruption/resume rehearsal (A5).
   Record the exact candidate/upgrade hashes and retained predecessor. A first-use
   installer cannot replace the used-updater upgrade protocol.
6. Present the final private target, SQL profile/commit/hash, tool upgrade/package
   hashes, native results, backup evidence, maintenance window and recovery plan
   for tool-installation and production preparation/deployment approvals (A8/A9).
   `-PrepareOnly` stages protected files and requires approval too.

## Deployment sequence after those gates pass

Use the [Promotion Guide](../reference/Promotion%20Guide.md) and
[combined updater contract](../reference/Combined%20Updater.md) on MINI_AMD in
elevated Windows PowerShell 5.1. Do not run development tests in the live checkout.

1. Verify the approved package still selects the exact private-main release and
   that no conflicting/uncertain release owns the operation. Stop on drift.
2. Install the approved authenticated updater upgrade if required, retaining its
   predecessor and upgrade receipts; independently verify installed member hashes.
3. Run the installed updater under the approved preparation/deployment scope.
   Retain its selected release identity and generated package. If preparation is
   separate, approve that concrete package before proceeding with deployment.
4. Request one `/ops graceful_restart` only when the runner prompts. Require the
   protected drain receipt and old issuer exit before any SQL/source/seed effects.
5. Let the runner apply/verify the selected MGE SQL profile, then install exact Bot
   source/index and startup seed, start one successor and verify readiness. Preserve
   activation flags, held/uncertain work and successful historical receipts.
6. Retain the transcript, stage intents/completions, SQL attempts/applied ledger,
   postimages, successor native/SQL/source/seed identities and `verified.json`.

## Verification and operator confirmation

| Stage | Evidence required | Confirmation |
|---|---|---|
| Code ready | Merged SQL/mirror/private SHAs; passing final-head CI; no unresolved review findings; retained security and test evidence | Source merges complete; operational qualification may still be pending. |
| Release ready | N/U matrix results; observed installed bindings; merged descriptor/profile; exact package and upgrade hashes; backup and recovery evidence | Operator approves this package/window. No guessed target values remain. |
| Deployment complete | One drained predecessor and one successor; exact SQL postimage/receipt; source/seed/native identities; readiness and verified receipt | Operator confirms the selected version is running. Startup success alone is not functional acceptance. |
| Functional acceptance | Authorized admin controls visible; ordinary active boards still refresh; a naturally completed event captures its original target and reaches confirmed or explicitly held state; completed history adds zero routine Discord IO | Record event/target IDs, original message identity, final state and evidence time. Do not replay a completed business action for a green check. |
| Residuals | Unknown, missing, forbidden, legacy-frozen and retired inventories remain distinct; import/export freshness reported separately | Accept or assign each residual explicitly. Historical retirement, live mutation tests and cleanup need their own scope. |

Post-deployment checks must be read-only observations unless live actions are
explicitly approved (A10). Do not infer event acceptance from a healthy process,
successful PR merge, attached controls, or unrelated import/export health.

## Stop and recovery

On an unknown outcome, drift, concurrent owner or verification failure, retain the
exact release and stopped-stage evidence. Independently establish ownership and
durable outcome before resuming the same release. Do not delete receipts, replay
SQL, request another restart, start a second process, or manually pull live source.

After SQL commits, the old bot is not a safe rollback: its historical sweep can
edit Discord before frozen SQL rejects the write. Keep the bot drained and use a
reviewed compatible forward correction. Preserve frozen data and finalisation
receipts. Dropping guards, database restore, historical message deletion and fixture
cleanup are separate operations requiring explicit scope and approval.
