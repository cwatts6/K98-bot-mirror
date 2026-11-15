# Portable application contract transition

## Problem and scope

The rebuilt qualification database has equivalent schema definitions but SQL Server allocates different internal IDs and generated constraint names. The reviewed version-3 application comparator handles those differences, but the installed updater still creates the old raw version-2 successor contract. This change adds an explicit, exact transition to the portable contract for the original production predecessor and the unchanged MGE migration.

The new version-2 combined descriptor selects `mge_application_schema_v2`. Its SQL profile remains `mge_finalisation_v1`; the descriptor version is not the SQL profile or application contract version. The original version-1 descriptor and raw-contract transition remain supported. The existing descriptor builder intentionally continues producing its legacy version-1 output; it must not be used to regenerate this separately reviewed exact portable descriptor.

## Fixed bindings and independent derivation

| Binding | Value |
| --- | --- |
| Bot predecessor | `2c31de42eb91cf6b7f9f61f3aaf3efc3597c4ea6` |
| Old application contract SHA256 | `814a7e6be4ac3865ee29b65e3c55ec7ad06d4a2ddeb0831f5cf1480d39d9f49f` |
| SQL commit | `9344a37656b034dd43867435e7c039ed20ae1c5e` |
| Migration | `20261029_001_mge_board_finalisation` |
| SQL profile SHA256 | `8fea59034c0ac0d14cfb6f72e03a3eda9c823648ec2c0fead6cd208bd4312bb0` |
| Portable before metadata | `d5a37fc143af0e487f4bfad9b40f66dc986b943a232f58c5f9f70558852bd92f` |
| Portable after metadata | `2825f1e9fb60d022a974951959f8443dfadabcb8e163d2fdb79e13ca6174648f` |
| New application contract SHA256 | `e124283154b15e57427626f929aff27c508fd4da20ac95f05f2b24c95da410c3` |
| Transition review ID | `9d113843-0cf0-5f31-a1c6-296e5b335156` |

The retained source catalogue, independently reviewed three-trigger after snapshot and unchanged canonicalizer were recomputed offline. Only the trigger category differs. The exact committed SQL profile bytes were read from the authoritative SQL repository and their hash verified. No post-deployment observation supplies an expectation. Private receipts retain input file hashes and the full contract; public documentation retains only binding hashes.

## Boundaries and recovery

The preparer changes only `version`, `fingerprint_format`, `metadata_hash` and `review_id` in the application contract. Installation and legacy contracts, permissions, source scope, target and principal remain unchanged. Independent protected-object checks still apply. The old raw comparator verifies the predecessor; the new portable comparator verifies the successor. Candidate template, plan, policy and launcher hashes are rebound through the existing release-seed path.

The installed updater must itself be upgraded through its reviewed custody path before accepting these new bytes. Target source cannot grant itself this authority. A distinct rebuilt lab contract is not the original production predecessor and needs a separately declared lab baseline. No SQL runner, DDL, account permissions, runtime comparator, process activation or network behavior changes here. There is no generic format negotiation or downgrade path.

Full combined native preflight, drain, migration, policy/source publication, startup/readiness, interrupted resume and rollback qualification remain required. The earlier native entry-point receipt covers the prior installed updater bytes, not this new authority. Production deployment requires separate approval after final bindings and rollback evidence are reviewed.

## Review and tests

Focused tests cover exact transition, immutable predecessor, every contract field, format/version confusion, altered descriptors, wrong predecessor, complete package resealing and independent legacy protection. Legacy transition tests remain active. Run repository validators, test selection, smoke imports, command registration, focused/full pytest and Windows updater checks. Security routing is Changes review of this bot commit range, Deep off; the unchanged SQL repository does not receive a new scan. No unrelated refactor or deferred item was introduced.
