# P02 Phase 1 - Permanent Release Regressions

## Scope and deployment checkpoint

The operator's 9 November updater output verifies corrective release
`fa1e52e1-afe5-4e26-9932-fde16ebb6e50`, source
`97abcce1b2a9e71b3959eff74525c57930a703e6`, source/seed/start/readiness and Discord
online. The supplied successor log records successful startup, player caches
and the normal ProcConfig import. No repeat deployment or restart is needed.

Fresh stats import, complete report/export delivery and retained incident
acceptance remain separate. Recovery report part 1 is incomplete: its monitor
is progressing, its previous completed check is older than the freshness
threshold, and its retained operation failure predates this successor. It must
not be interpreted as a fresh recurrence or complete incident clearance.

This package adds permanent offline regression coverage and CI only. It changes
no installed SQL, application runtime permission checks, resource limits,
activation flags or production permissions. No production workload is required.

## Failure causes and permanent coverage

| Boundary | Regression and negative controls | Always-run gate |
| --- | --- | --- |
| SQL server identity | SQL repository `tests/test_p02_phase1_release_runner.ps1` executes the actual runner with `MINI_AMD`, `mini_AMD`, `mini_amd`, `MiNi_AmD`; different hosts, instances, whitespace, database and mode changes remain refused. | Existing SQL validation workflow runs the runner on every PR and main/codex push. Locally rerun under Windows PowerShell 5.1. |
| Permission expectation generation | `tests/test_release_identity_regressions.py` reproduces the old Python tuple sort with mixed-case subentity names, proves that the real startup verifier rejects it, and verifies the native-order projection. Missing/extra rights, changed columns and allow/deny values still fail. | New Windows `Release identity regressions` workflow on every PR/main push, without path filters; local selector always recommends the same suite. |
| SQL column/catalogue ordering | Existing `tests/test_export_schema_fingerprint.py` covers reordered result rows and regenerated catalogue allocation IDs. Added explicit rejection of a real change in visible column order. | Same Windows gate and full pytest. |
| Corrective release safety | Existing P02 and P01.6 application-contract recovery tests, including the native Windows recovery cases. | Same Windows gate and full pytest; Windows avoids silently skipping the native cases on Linux. |

The prior schema fingerprint test already distinguished result enumeration
from schema identity. It did not cover permission projection: those permissions
have a separate exact hash, and their inner ordering follows SQL collation.
These are related comparison risks, but not interchangeable test cases.

## Release preparation rule

Use `scripts/project_application_permissions.py` when adding qualified new
objects to a protected permission expectation. Verify the protected predecessor
hash, exact new-object scope and unchanged schema rights. Retain every native
within-object row in order; only merge the binary object-name groups. The helper
is deliberately limited to the reviewed BMP object-name ordering domain.

The helper is offline and does not authorize grants or deployment. Inputs must
be independently captured using the qualified reader, principal and collation;
compare the resulting expectation with native candidate evidence before release.
Never replace a protected expectation with an unreviewed live hash just to make
startup pass. Never globally case-fold or sort permission entries. Keep the
original failed compiler/evidence intact; corrected preparation uses this helper.

Private retained Phase 1 inputs reproduce the deployed permission hash exactly
with this helper. Synthetic public fixtures retain the mixed-case failure
without publishing the production permission catalogue.

## Validation and review

- Focused Python tests and native SQL runner tests are required.
- Architecture, deferred-item, security-routing, test-selection and formatting
  gates apply; there is no new deferred optimisation item or runtime refactor.
- The small offline permission projector and CI execution receive a Changes-only
  security review. SQL source is unchanged and its existing regression is rerun.
- Full production CI remains the merge gate. No new production deployment or
  fresh business action is part of this regression-test package.
