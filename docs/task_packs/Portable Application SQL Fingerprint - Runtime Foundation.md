# Portable application SQL fingerprint: runtime foundation

Equivalent schema-only rebuilds can receive different system-generated constraint
names, column-ID gaps and filtered-index IDs. The existing application fingerprint
includes those allocation details and therefore rejects the rebuilt qualification
database even though its compared definitions match.

This slice adds an explicit application contract version 3 using fingerprint format
`application_schema_v2`. Contract versions 1 and 2 retain their original readers and
raw-hash comparisons. No current startup policy, installed updater capability,
release descriptor or deployment target is changed by this slice.

## Implementation

- [The pure fingerprint implementation](../../services/export_schema_fingerprint.py)
  validates complete raw metadata and catalogue provenance before normalization.
  It retains visible column order, whole constraint/index groups and duplicate
  multiplicity. It removes only catalogue-proven generated labels and resolves
  dependency IDs according to their actual class.
- [The application catalogue reader](../../services/export_execution_dal.py) adds
  separate, parameterized provenance reads only for the explicit new format.
  The shared fixed-coordination metadata queries remain unchanged.
- [Startup contract verification](../../services/export_runtime_composition.py)
  requires the pinned activation scope and exact new format for version 3.
  Target identity, source manifest, dynamic objects and effective permissions keep
  their independent strict checks. Unknown versions and mixed observations fail.

User-assigned names remain significant, even when they look system-generated.
Generated labels referenced in module text are refused by the portable format.
Module definitions remain byte-sensitive; this is not general SQL equivalence.
Unsupported dependency/index classes, standalone filtered statistics, incomplete
provenance and conflicting identities are refused rather than guessed.

The accepted native input shape includes object/column references, filtered-index
references and type references. Referencing columns are resolved separately from
indexes; a coincident column ID does not explain an INDEX dependency. Referenced
column names, qualification and binding/caller/ambiguity flags remain material.

## Evidence and limits

The complete retained source and guest inputs cover the existing 465-name scope.
Their unchanged original raw metadata hashes are respectively
`12b7d6f1178e66708210088f59296a885ed7b11f894273bdfae874460ba96b07` and
`1dfd62ebe5ad02391819e043f4bae497f45ae0f4fe03cd7679cca5a377313f7e`.
The new implementation gives both the candidate before fingerprint
`d5a37fc143af0e487f4bfad9b40f66dc986b943a232f58c5f9f70558852bd92f`.

Applying the same implementation to the independently retained expected MGE
after-metadata, whose only changed category is the three reviewed triggers, gives
candidate after fingerprint
`2825f1e9fb60d022a974951959f8443dfadabcb8e163d2fdb79e13ca6174648f`.
These are review evidence, not installed authority or approved release bindings.
The raw receipts remain unchanged; no observed target value is adopted as an
expectation merely because it passes comparison.

Private retained evidence records the input and implementation hashes. Complete
catalogue/module captures are not published as test fixtures. Unit tests use a
synthetic schema with independently specified definitions and relationships.

## Validation

The dedicated suite covers equivalent rebuilt identities and row ordering,
material type/shape/index/FK changes, explicit names, missing/invalid provenance,
unsupported classes, duplicates, generated-name references, format/scope/target
rejection and preservation of permission checks. Existing runtime, activation-scope
and MGE transition suites verify the legacy path remains unchanged.

Local regression tests are distinct from SQL integration and the combined native
qualification. Native SQL qualification, account changes and deployment remain
separately approved operations. Final test/review results belong in the PR and
retained delivery record; this document does not predeclare them passing.

## Remaining release work

1. Complete the required Changes security review and ordinary PR review of this
   immutable slice. Promote the exact reviewed patch through mirror/private PRs.
2. Implement and review the installed updater transition separately. Its current
   MGE authority changes only the raw metadata hash/review ID; it cannot silently
   reinterpret this new format. Bind the exact predecessor policy, new format,
   reviewed before/after expectations, verifier source and migration.
3. Ensure preflight, source/policy pairing, successor observation, interruption,
   resume and rollback all understand the new version. The old predecessor must
   not be assumed to load a new verifier. Target-tree code must not grant itself
   installed updater authority, and no legacy receipt may be manufactured.
4. Rebind release commits/packages and complete separately approved lab setup and
   native qualification. Previous rehearsals do not qualify this new code path.
5. Present the exact production deployment, rollback, verification and operator
   confirmation packet for separate deployment approval.

This foundation alone is **not ready for deployment**. No SQL schema migration is
introduced here. The recovery database, sequence and added dependency tables remain
untouched; account and permission preparation remain separate.
