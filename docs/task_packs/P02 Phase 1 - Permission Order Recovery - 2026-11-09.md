# Phase 1 permission-order recovery

The Phase 1 SQL migration, source and startup seed installed successfully. The
first successor started, but startup verification rejected the application
permission fingerprint. Deployment is not yet verified and fresh import/export
testing remains separate.

The private comparison establishes identical schema, object and column
permission rows. The projection had sorted within-object rows using Python's
case-sensitive string order, whereas the SQL reader uses the database collation
for subentities. The corrected expectation preserves the protected predecessor's
within-object ordering and the independently qualified new-object groups. It
does not learn or grant new production permissions. Runtime comparison stays
exact; SQL metadata, scopes, legacy and coordinator contracts remain unchanged.

## Delivery and recovery boundary

- The original release remains incomplete, with its first start outcome retained.
  Never create an original readiness receipt or replay the committed SQL step.
- Only the exact inventoried partial release and its first successor are eligible
  for the corrective updater upgrade. Current protected bytes, receipt inventory,
  startup policy and absence of another deployment request are rechecked.
- A new source-only package authenticates the exact old and corrected contracts.
  Its stages are source, seed, start and readiness; SQL and recovery-seed stages
  are prohibited. Its live preflight checks source, native process/session identity,
  contracts, retained work and the ordinary deployment protections.
- Selection records the candidate preparation before atomically replacing the
  active pointer and retaining its original bytes. Interruption resumes only an
  exact recorded old/new state. Original receipts and failure evidence stay in
  place; selection does not certify health or restart anything.
- After preparation review, the normal updater performs the coordinated drain
  and one prompted graceful restart. The new seed contains the corrected
  expectation. Normal native, SQL-session and startup/readiness checks apply.
- Keep all resource limits, activation flags and held work unchanged. Production
  import/export and provider delivery remain separate acceptance work.

## Validation and review

Regression tests cover predecessor/candidate drift, permission changes, extra SQL
work, complete package construction, seed hashes, preserved flags, native partial
release admission, atomic selection interruptions and changed pending evidence.
Private qualification also checks the real collected protected bytes and the
independently derived permission expectation. Local fixtures do not substitute
for fresh production custody, process or application-token checks.

Run the complete test suite with operational-log protection, native Windows
recovery tests, architecture/deferred/security-routing validators, smoke imports,
command registration and formatting checks. The deployment/permission surface
requires a Changes security review of this Bot patch, Deep off. SQL repository
source is unchanged; no SQL PR or installation is part of this correction.
Final results and exact promoted identities belong in the release handoff.

## Operator sequence after qualification and promotion

1. Run the generated reviewed updater upgrade with `-Phase1PermissionRepair`.
   It replaces tooling only and preserves the old package and active release.
2. Run `Update-K98.ps1 -RepairPhase1Permissions -PrepareOnly`. Review the returned
   target and source-only package before proceeding.
3. Run the same updater normally, requesting one graceful restart only when
   prompted. Preserve any stopped output and do not replay it blindly.
4. Verify deployment readiness before authorizing fresh import/export testing.

If any identity, custody or outcome is uncertain, retain both releases and inspect
the exact state. Do not force hashes, modify SQL permissions, delete receipts or
use an ordinary restart to bypass the reviewed replacement policy.
