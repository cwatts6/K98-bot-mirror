# Exact portable schema reader source admission

## Scope summary

The complete private release projection from installed commit
2c31de42eb91cf6b7f9f61f3aaf3efc3597c4ea6 to private main
adfdc7c5f4b82ac6f70761bd4fa16772b93db1a4 plus the reviewed portable contract
patch rejects five already reviewed schema reader files. Native portable updater
qualification U passed, but did not claim complete source preparation.

## Affected areas and architecture

Keep operational admission in scripts/prepare_k98_update.py and its installed
k98_update_transitions.json. Add one exact, indivisible five-member family,
application_schema_portable_v1, bound to original installed and current private
Git blobs. Members: services/export_contract_resources.py,
services/export_execution_dal.py, services/export_runtime_composition.py,
services/export_schema_fingerprint.py, services/export_sql_direct_permissions.py.
The new fingerprint and contract-resource modules must be absent in the predecessor. Preserve all prior
52 registry entries byte-for-byte as parsed values; raise only the entry limit to
53. Keep the existing byte bound if the final registry fits. Enforce the complete
five-path family. Existing source inventory and whole-bundle hash checks remain
the authority; the target cannot supply its own admission rules.

## SQL and persistence review

No SQL, comparator, connection, permissions, schema, process, task or runtime
implementation changes. The admitted files are already reviewed source with
accepted native archive checks. This work only permits their exact reviewed
before/after bytes through the installed updater. No SQL repository mutation or
live query is needed. Full combined migration/recovery remains unqualified.

## Refactor triggers

Reuse existing finite transition machinery and tests. No new general policy
abstraction, import execution or target-controlled exemptions. No unrelated
refactor or deferred item introduced.

## Security review decision

Changes review required for installed deployment admission. Target the new
focused mirror branch after PR472, exact base/head to be recorded once committed;
Deep off. No whole-repository scan. Preserve all predecessor families and validate
target self-admission refusal. Production deployment remains separate.

## Test strategy

Pin original 52-entry canonical digest and exact five-file before/after digests.
Exercise every member changed/missing on either side, predecessor absence,
missing/extra/duplicate family members, registry entry/byte bounds, LF/CRLF,
omitted changed paths, old installed policy refusal and target self-admission.
Classify the complete exact private projection and retain its result; no placeholder
projection is a deployment target. Run focused transition/preparation tests,
architecture/deferred/security-routing/select-tests gates, then review the diff.
Existing full regression for PR472 must finish before editing its worktree.

## Approval and evidence boundaries

Covered by the user's approved updater extension and continue-to-deployment-ready
instruction. No new account, SQL, network or production action. Native U is frozen
and accepted; never alter its payload, hashes or receipt retroactively. Any new
native packet must bind U as predecessor and receive its own review before the
operator runs it in the retained elevated session.
