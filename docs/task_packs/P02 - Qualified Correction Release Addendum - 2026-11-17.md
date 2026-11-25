# P02 qualified correction release addendum

## Scope and authority

Update existing mirror PR540 and private PR745. The operator has authorized
source delivery, review fixes and merges, followed by release/readiness
preparation. No VM execution, production deployment or recovery is performed by
this source task. Native acceptance and its limits are recorded in
[the acceptance handoff](P02%20-%20Native%20Qualification%20Acceptance%20and%20Release%20Handoff%20-%202026-11-17.md).

## Runtime and delivery changes

The qualified shared observer avoids transaction-owned APPLOCK_MODE when SQL
Server reports no active transaction. It preserves both transaction states,
isolation, existing lock refusal and uncertain ownership custody. MGE and PreKVK
queries delimit the existing RowCount column/alias. SQL source-of-truth confirms
both column names. No SQL migration, index change, permission grant, dependency,
credential or configuration change is required. Deferred maintenance remains.

The updater adds one complete direct source family,
`p02_maintenance_qualified_v1`, over the deployed D6 predecessor. It includes the
original eight compatibility members with the qualified helper plus the two
identifier fixes. All 91 prior transition objects remain unchanged. The original
seed amendment remains exact; the preparer accepts either complete reviewed
source pair, never a composition of historic transitions or a target-supplied
policy. Every changed source member and predecessor hash must match.

The inventory-discovering reserved-identifier guard runs in pre-commit and pytest.
It includes new tracked and untracked Python, PowerShell and SQL source. It is a
lexical regression guard, not universal SQL grammar or engine qualification.
Portable release tests cover transaction states, the original SQL3918 failure
model, delimiter handling, complete packet preparation and mutation of every
source member on both sides. Existing lab tools, receipts and lab-specific tests
remain preserved locally; they are not added to the deployable source delta.

## Validation and review plan

Recheck focused runtime and updater tests, every historical transition, portable
SQL guard and the full clean candidate suite with native opt-ins disabled and
operational log isolation. Run architecture, deferred, test selection, security
routing, smoke imports, registration, lint and diff checks. Reuse native evidence
only for byte-identical qualified runtime files. Packaging changes require offline
complete source/seed/start/readiness checks; they do not justify another lab run.

Security routing: Changes review of the source addendum against each existing PR
head, Deep off. Reuse previous exact source review only where hashes still match;
review the new preparer/transition behavior and supporting caller paths. No SQL
repository diff is introduced, so no separate SQL change scan is required.

## Deployment order and failure handling

After final review and checks, merge the existing mirror and private PRs. Pin the
private main merge SHA, build the matching updater package against the actual
installed updater manifest, and prepare a fresh MINI_AMD read-only readiness
packet. Require exact source/seed/SQL identity and changed-path/ancestor custody.
Then upgrade the updater and use its normal prompted restart flow. Deployment
receipts must pass before separately resuming E2-E4 and later fresh Discord
import/export acceptance. The release adds no SQL migration step.

Do not roll back to the strict guard while retaining the deferred database state
or amended policy. On failure preserve the exact release and receipts and review
a forward correction; no replay or index creation to satisfy a guard is implied.
All accepted evidence, original failures and allowance balances remain unchanged
by this offline source work.
