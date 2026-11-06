# S11 G4 context: standalone Sheets demonstration completed — 2026-10-02

Chris explicitly selected **option1: separately scoped real-provider transport demonstration** and assured no production write activity during the test. This scope completed; it does not close full S11/G4/G5 acceptance. The local overall report calculation/publication was already validated in [the preceding result](s11_g4_overall_local_publication_20261002.md).

Actual Google run completed at 09:16:40Z, owned process exit0. [Report directory](https://docs.google.com/spreadsheets/d/1Sfa6NJw4urC2ldTu16q5EGFSRR4VFPX0Pgt4paLiM1g/edit#gid=1548835227); [fixed index](https://docs.google.com/spreadsheets/d/1ydIKNmq74VWfD52u_Ft_l7hd7qOQgLWdpX8erQw7j7o/edit#gid=0). The temporary production no-write period can end; no production operation was executed.

## Proven result

- Five exact files passed fresh intended owner/direct existing SA Editor/link-only Viewer and blank-grid checks before writes.
- One real upload to slot01; all twelve sections matched exact local content/row/column manifests on provider readback. The directory and index were verified.
- Second identical export request reused the confirmed receipt without provider writes, followed by a separate fresh complete provider readback. This is two requests/one upload, not changed-generation rollover or two independent uploads.
- Only index/slot01 changed. Three spare files remained blank and unchanged. Zero automatic spreadsheet creation, permission mutation or requests to the nine protected historical exclusions. Existing Viewer access was preserved throughout.
- DB24 `ROK_TRACKER` on `9SX2VF4\K98DEV` has one confirmed SourceDelivery, attempt1/fence1, publication `07f4ba4e-c69d-5102-be61-ea9f97eff343`; content key `db5ff926257d2f9231de0f4aa3464e84afa56b0df92f746dd539a16bdbcee238`. SQL-backed selected/final and unknown-generation reuse both denied. Routing remains disabled.

Successful v2 measured 390.172 seconds, 290 API requests/62 mutations, one token exchange, 23,760,014 request bytes, 91,172,695 response bytes, 23,414 submitted value rows and104 counted DAL statements plus connection guards. All requests received HTTP200. No schema change or source import/recalculation was needed.

## Source correction and evidence

An explicit standalone-only `preserve_public_staging` option fixes the older transport's temporary Viewer revocation for this test. Default private and coordinated authority paths are unchanged. Public attempts checkpoint exposure before writes and retain uncertainty on failure; private recovery/retirement reject this mode. Full authority records are not fabricated or weakened.

Final reviewed export-service SHA256 `10df183fda9e3fb0d0d30042dfa5ca33ac717be3599739565d64bf4ef06af8ee`; delivery-service `d398dc86bab0ebec521095fe2c7268cfd8f8b2df845f88d3a8dd917313afbc6c`. Affected regression suites351 passed; final four public-stage tests passed, overlapping counts. Ruff/architecture/deferred/security-routing checks passed. Independent ordinary scoped review had no remaining blocker. Canonical Changes review was not completed because its Git-baseline API could not isolate the retained three-file preimages from unrelated pending changes; do not claim final release review.

First provider attempt stopped read-only after two GETs due an over-strict blanket inheritance check; zero mutations and no delivery claim. Preserve it. V2 used the unchanged reviewed manual-permission validator, admitting only the intended owner's subordinate inheritance. No blind write retry occurred.

Complete packet, working/sealed commands, individually compared source plan, command/application copies, provider evidence, actual SQL receipt, source verification and result:

`C:\Users\cwatt\Documents\Codex\s11-sheets-transport-demo-20261002\`

Successful runner SHA256 `574d95d773333803555a8189e2a7b4580793b3825779978c44b3388baffffee6`; source-plan `5c865ca059886694fb891067f77766a3bf36be706df6196bb0f48cc47a03bcac`; launcher `00ac6f1d6ffea86d5b89a25868661ed5e4724f1620f7436deba25e6b396c8605`. Original seals remain preserved; two application members intentionally changed from the prior549-member source plan. Documentation has a separate completion manifest.

## Preserve and do not overclaim

The index and slot01 now contain a referenced final report. They are no longer blank enrollment candidates and must not be cleared, treated as retired, or overwritten to force another test. Future full S11 enrollment must explicitly account for them under the reviewed adoption/retirement policy. Three spare files retain their observed blank state as of this run.

All seven complete typed G4 proofs remain incomplete. Full authority/manual enrollment, S6/S8 gates, G5 and production rollout remain separately scoped decisions. Operator key/no-write statements are not global writer-drain or automated IAM inventory proof. Offline uncertainty tests are not an induced real-provider uncertainty experiment. Production remains the retained isolated hotfix; no new runtime observation or deployment claim. Preserve DB22 read-only/restricted/Broker-disabled,119 media, DB23, all old files/receipts/uncertain publications and pending shared-account amendment. Memory investigation remains deferred; no withdrawn collector was run. No Git publication or new task.
