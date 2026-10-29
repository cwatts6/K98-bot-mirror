# P1 MGE A1b updater inventory correction

## Observed failure and scope

The operator upgraded the installed updater, then preparation on 29 October 2026
refused with `Incomplete reviewed protocol transition inventory.` The transcript
reported that the bot remained running and no restart was requested. This is a
preparation failure, not evidence of an application or SQL mutation failure.

The defect reproduces from accepted A1a source
`87c1b39325daaa0ca1a8c0cbca656df82d7fa46b` to merged A1b source
`e1487bf7edb61cffa6487ae332ffa8a24a412e4e`. The installed A1b transition contains
41 authenticated dependencies, but only 36 changed. Five intentionally unchanged
members are absent from Git's changed-file list:

- `core/coalesced_work.py`
- `core/operation_outcome.py`
- `core/operation_timing.py`
- `core/owned_work.py`
- `mge/dataset_errors.py`

Preparation incorrectly required every bundle member to appear in that list.
Previous qualification missed this because the compatibility classifier did not
apply the same inventory rule and synthetic fixtures changed every dependency.

## Correction and preserved boundaries

Preparation and compatibility classification now share the inventory gate. It
first authenticates the complete registered predecessor/successor bundle. A member
may be absent from the changed-file list only when its actual Git bytes are equal
at both revisions. Missing or altered dependencies, omitted changed members,
newline-only changes omitted from the inventory, and invented changed paths are
still refused. The transition registry and its historical entries are unchanged.

This changes updater admission and its development classifier only. It adds no
MGE runtime behavior, SQL migration, dependency, configuration or activation change.
Source pins, installed-tool authentication, ownership checks, drain, retained
outcome evidence and restart controls retain their existing requirements.

## Validation and evidence mapping

| Evidence | What it establishes |
| --- | --- |
| Actual committed-source reproduction | Original source planner refuses the 98-file release delta with the reported error. |
| Corrected source planner against the same commits | All 98 source/payload members prepare using a synthetic complete 789-pin predecessor policy; no live host state is read. |
| Nine inventory regression cases | Real 36/41 shape, LF/CRLF, missing/altered dependencies, omitted actual and newline-only changes, invented inventory entries. |
| Focused updater suite | 358 tests pass across inventory, A1b transition, preparation and application compatibility. |
| Architecture, deferred-item, security-routing and test-selection gates | Pass; selector recommends full pytest, smoke imports and command registration. Smoke and registration also pass. |
| Changes security review | Scan `7db23a24-817b-4e63-a9f1-e0582d4f1cc6`; both changed source files reviewed, zero findings. Documentation added afterward introduces no executable change. |

The release handoff must retain final-head full-suite/CI results, PR review
dispositions, exact package hashes and a source-plan qualification against the
final merged private commit. Classifier output alone is insufficient preparation
evidence. Local source-plan fixtures do not attest elevated host custody, running
process identity, provider outcomes or successful production deployment.

## Deployment sequence and recovery

The operator has already installed the first A1b updater. The correction package
must therefore authenticate that installed manifest as its predecessor:
`01467e5bca1f5f5cc1b8a78531478259f169e59f17a5a24c4c198eeef332651d`.
Do not repeat the earlier A1a-to-A1b upgrade helper or manually edit installed code.

After mirror review and patch-based private promotion/merge, build the exact
correction installer and used-updater upgrade helper. Qualify the candidate tool
against the installed bot's A1a source and the final private-main target. Supply
the resulting package and checksums in a separate deployment handoff.

On the bot machine, retain the failed transcript and updater backups. Install the
reviewed correction through its exact-version helper in elevated Windows
PowerShell 5.1, then run the installed `Update-K98.ps1`. Request the graceful
restart once only when the updater prompts. Confirm the selected private commit,
source/startup/readiness receipts and Discord online before functional checks.
Do not reset the checkout, delete retained deployment state or blind-replay an
uncertain apply. An unexpected refusal requires its fresh evidence to be examined.

The updater upgrade does not deploy bot source. Merge, deployment and MGE natural
acceptance remain separate. Preserve the existing A1b functional verification and
residual acceptance ledger; this correction does not close those runtime cases.
