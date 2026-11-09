> **Archived at E104, 6 November 2026.** P01.6 is closed for its agreed scope. See [accepted closeout](Startup%20Import%20Export%20Reliability%20-%20P01.6%20Closeout%20-%202026-11-06.md) and [active P02 handover](../Startup%20Import%20Export%20Reliability%20-%20P02%20Handover%20and%20Scope%20-%202026-11-06.md). Dated approvals, candidate status and commands below are historical evidence, not instructions to replay deployment or recovery.

# P016 application startup contract correction

## Incident and scope

The P016 procedure rewrite and covering index were applied successfully, but the
Bot release retained the previous protected application SQL contract. Both
`dbo.usp_GetPersonalStatsDaily` and `dbo.KingdomScanData4` are inside its activation
scope. After restart, Discord came online while application runtime admission
refused the changed metadata. The installation and legacy SQL comparators passed.

This correction belongs to the installed updater and release verification layer.
It preserves the reviewed SQL optimisation, runtime comparator, scope, permissions,
activation flags, retained work and other two SQL contracts. No command, cache,
business workflow, SQL migration or provider request is added. The earlier embed
render timeout remains a separate functional acceptance observation.

## Exact authority and independent derivation

The installed verifier admits one amendment from deployed Bot
`8f1023e2d89e2d4da06ddde39da5b4b6df32ff03`, whose complete application contract is
`e124283154b15e57427626f929aff27c508fd4da20ac95f05f2b24c95da410c3`.
It changes only the metadata fingerprint and review identifier. Candidate source
cannot supply this authority; the reviewed updater must be installed first.
The ordinary source policy, immutable package and administrative custody checks
continue to apply.

The retained approved catalogue reproduces predecessor metadata
`2825f1e9fb60d022a974951959f8443dfadabcb8e163d2fdb79e13ca6174648f`.
Projecting the procedure and index from SQL commit
`dad628c7a353cc6391868d097a6ae5fb7a8d9e84`, migration
`20261106_001_personal_stats_daily_read_plan` (deployed CRLF file SHA256
`bb0e3161d8c3df96452e2631dfcbb8bbb9e0637877631624716129e76d7129a8`),
gives successor metadata
`b5b33d42b15db44ab2bee1ebefa3dfd54557d9b8a8b1cb3340be30253a540f73`.
The index shape and unchanged procedure dependencies were checked against the
retained qualified local fixture. Exact stored module text was reproduced in a
fresh local disposable database: SQL Server stores the `CREATE OR ALTER` header
as `CREATE` followed by three spaces before `PROCEDURE`. The existing comparator
still compares that text exactly; no normalization was added to runtime.

The resulting full contract is
`b2e93a617114ca73abd6f1290d108a7199f4e00b120df2ec464bccf6022e0366`,
with review ID `9dcb6602-a4a4-5bf5-9073-d00a6db99f76`. The read-only production
snapshot subsequently matched the independently derived whole metadata and
unchanged permissions using the complete existing application comparator.
This is captured evidence, not proof that the running Bot has installed the fix.

## Deployment gates and order

1. Review, qualify and merge the correction through mirror and private PRs.
2. Verify current host custody and installed updater identity; upgrade the updater
   through its reviewed replacement path, retaining the predecessor tool.
3. Prepare the corrective source release. Before drain, authenticate the exact
   live predecessor and both old/candidate templates, then verify all three SQL
   contracts against the reviewed successor expectation. Refuse any unrelated
   schema or permission drift. Do not replay the already-applied migration.
4. Perform one prompted graceful restart through the coordinated source/seed
   deployment. Reverify all SQL contracts, source, native pair and readiness.
5. Confirm runtime admission and exercise `/me stats`. Observe import/export only
   through authorised natural activity; successful startup does not certify provider
   delivery or justify replay of retained work.

All future source-only releases now run the complete SQL comparators before drain
and at successor verification. Explicit closed runtime admission blocks readiness;
missing fresh whole-flow/provider evidence remains truthfully degraded.

## Failure and rollback

Before publication, a failed gate stops without drain or deployment. Preserve its
evidence and correct the mismatch. After publication/start, do not retry startup,
edit sealed templates, reset live source or downgrade the updater to bypass a
gate. Preserve the exact stage/receipts and inspect ownership and retained work
before preparing a coordinated recovery.

Returning only to the previous Bot would retain the original contract mismatch
while the new SQL remains installed. A rollback must coordinate the reviewed SQL
rollback and a matching protected Bot/seed expectation; it is not a blind Bot-only
revert. This release performs no SQL rollback automatically. The preferred repair
keeps the independently validated optimisation.

## Validation and security route

Tests cover exact authority, every predecessor field, descriptor substitutions,
unchanged permissions and other contracts, immutable originals, complete package
resealing, preflight and successor template checks, source-only native SQL gating,
and refusal to accept Discord readiness with closed runtime admission. Full
repository gates and updater Windows qualification remain release requirements.
Security review is **Changes**, Deep off, over this correction only. SQL source
is unchanged and does not require a second SQL diff scan. Private catalogues and
host evidence remain outside the published repository. No unrelated refactor is
included.
