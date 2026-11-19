# P02 D5f grouped release qualification

The operator approved a 90-entry registry and the proposed 80-member
`p02_d5_qualified_combined_v1` family. The 232,448-byte ceiling remains unchanged.
This implements the [reviewed extension](Startup%20Import%20Export%20Reliability%20-%20P02%20D5f%20Accounting%20and%20Release%20Gate%20-%202026-11-15.md).
The original qualification total remains **128/128**. Release qualification is
tracked separately as twelve groups; its final status and exact test/review pins
belong in `.codex_artifacts/p025/d5f-release-acceptance-20261115.json`.

## Implementation and ownership

`scripts/prepare_k98_update.py` admits at most 90 entries, and permits 80 members
only for the named qualified family with its exact path set. The unchanged D4
family and all 89 historical registry definitions remain available. The registry
uses compact formatting and fits both LF and CRLF representations below the
original byte limit.

The committed release descriptor selects the qualified family while retaining
version4, profile `p02_d4_v1`, migration `20261111_001_p02_d4_combined`, SQL commit
`ba5c6acbefba0eb89cb18842a7f6c6811096759b`, profile and batch hashes. Historical
D4 descriptors still select the original family. Admission now verifies that
the complete direct source pair matches the family selected by the descriptor;
a mixed family or partial inventory cannot borrow another family's admission.
The shared exact-pair matcher is reused by protocol and descriptor checks.

The two already-qualified application fixes are unchanged: Personal Stats waits
for render settlement before executor shutdown, and maintenance validation
requires all six receipt kinds and bounded integer generations. Their delivery
pins are added to the qualified family. Test-only successor bridges authenticate
these exact bytes before exposing the unchanged historical assertions. A bridge
does not authorize production installation.

No command, service, DAL, SQL schema, grant, scheduler, application behavior,
activation flag or startup contract is changed by this release-binding slice.
Operational tooling remains in scripts; no new framework or duplicate runtime
mechanism is introduced. Historical registry policy remains intentionally
explicit; redesign is outside this bounded change. No new deferred item arises.

## Evidence preservation

Before editing, all 2,403 accepted preservation pins and the six latest closeout
pins were verified. Exact preimages of the fifteen potentially affected files
are retained under `.codex_artifacts/p025/d5f-release-preimages/files`, indexed by
`manifest.json`. Approved source/test evolution is reconciled to those original
bytes; old receipts are never rewritten to point at new source. All unrelated
accepted artifacts and runtime fixes remain unchanged. Old packets are historical
evidence, not instructions to rerun against the evolved checkout.

The original failed test log and receipt remain alongside the passing result.
The first new run recorded304 passed and two test failures: it called the
adoption-only descriptor helper when the full source-plan entrypoint owns the
already-present/foreign marker and wrong-predecessor checks. Those tests now
exercise full admission and still require refusal. The grouped revised run
passed **996/996** tests. No production change was needed for those two failures.
An interrupted parallel formatter was replaced by in-process formatting; this
did not consume native or Windows fault-test allowance.

## Twelve release groups

| Group | New evidence and retained boundary |
| --- | --- |
| R01 historical preservation | Exact canonical digest of all89 earlier definitions; historical D4 direct pair and descriptor; historical transition regressions |
| R02 qualified family | Real80 current postimage hashes; all80 predecessor bytes checked against retained installed Git identity; complete direct-pair admission |
| R03 missing/mismatched members | Every member tested for missing target, altered target and altered preimage; unchanged peers remain authenticated |
| R04 mixed/wrong predecessor | Wrong predecessor, old maintenance, old Stats, partial inventory and opposite descriptor-family refusals through full source admission |
| R05 bounds | 91 entries,81 members, unknown family/path, missing/duplicate members/IDs, invalid hashes and oversized bytes refuse; LF/CRLF remain within232448 |
| R06 exact SQL binding | Qualified/historical descriptors retain exact predecessor, SQL commit, migration/profile/script and three startup contracts; foreign descriptor fields refuse |
| R07 incomplete adoption | Source-only and incomplete changed-family inventories refuse before drain or effects |
| R08 updater delivery | Actual current updater/registry packaged and self-hashed; retained old installed manifest requires upgrade; new package admits exact candidate |
| R09 source and seed | Retained841 source pins validated; candidate852 pins include both fixes; all three contract postimages remain the accepted D4 contract tuple; complete package seed wiring tested |
| R10 custody/archive | Source preimages come from Git/installed pins; archive delete/add exact payload and no runtime pin; path/case/tool-copy refusal controls; seven accepted archive moves retained |
| R11 ordering/recovery | New-descriptor package has SQL, source, seed, start, readiness order; historical runner/PS5.1 rollback/forward-only receipts preserved with unchanged runner hashes |
| R12 final review/handoff | Exact patch Changes review, changed-source preimage reconciliation, final counts, source/document manifest and immutable handoff |

Unit hash fixtures are inert and portable to the mirror. A separate private
offline qualification reads the authentic retained installed receipt, fixed
predecessor and private baseline Git trees; overlays only explicitly selected
files; packages the updater without executing it; validates real source pairs,
source-plan pins, three contracts and seven SQL payload files; and refuses seven
damaged candidates. It preserves private-only baseline paths. The candidate uses
an explicitly labelled offline target sentinel, not a published private-main
revision. Its result is `d5f-release-candidate/result.json`.

The retained SQL source repository is read-only for this task. Fixed payload
bytes, profile images and migration prerequisites remain authoritative. There
are no guessed objects, catalog-header normalizations or new SQL queries in the
implementation. Earlier CREATE/CREATE OR ALTER/spacing and bracketed
`[RowCount]`/`[backup]` documentation and regressions remain intact.

## Validation, review and limits

The selected tests cover changed registry consumers, descriptor selection,
complete package/source/seed construction, historical compatibility, source
custody and updater replacement. Architecture, deferred-item, security-routing,
test selection, lint/format and whitespace gates apply. Broad application pytest,
application smoke imports and command registration are not rerun: no application
or command behavior changes in this slice, and those do not establish updater
admission. The selected tests isolate their logs from operational logs.

Security routing is **Changes**, Deep off, for the frozen release-binding patch
and directly supporting code. No whole-codebase audit is implied. Existing
reviewed runtime-fix evidence is preserved; the new review includes their exact
delivery bindings. Final scan identity, findings/coverage, test totals and usage
are recorded in the acceptance/handoff, not inferred from this plan.

No native workload, real Windows fault schedule, input, row, database or backup
is consumed by offline release preparation. Remaining allowances stay
**774 native seconds,49 Windows fault-test seconds,zero row attempts**, with
the21-input, database and backup allowances consumed. No old workload is replayed.

D5 source/fixture qualification is not installed-host or provider acceptance.
Final private-main delivery and D6 deployment need their own reviewed target and
fresh installed source/updater/seed/effective-identity/path-and-ancestor evidence.
The old installed updater must be replaced by the exact reviewed package before
preparation; no direct SQL or alternative launcher bypass is introduced. Before
SQL commit rollback remains possible; after commit use the same verified receipt
to continue forward, without SQL replay, reverse datatype conversion, old-Bot
fallback or a second forced start. P03 actual blockers, essential P04 convergence,
Q04 diagnostic fingerprint semantics and D7/P05/provider/natural acceptance retain
their existing owners and limitations.
