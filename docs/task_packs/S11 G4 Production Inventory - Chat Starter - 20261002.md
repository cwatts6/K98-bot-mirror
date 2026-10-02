# S11 G4 production inventory — copyable chat starter

Continue S11 with **bounded production inventory and staged rollout preparation**. Chris has explicitly **accepted and closed the local implementation review** and **approved this next stage**. Carry that approval forward; do not ask again. Publication/PR/push/merge, production installation, deployment/restart, enrollment/export writes and G5/activation remain separate decisions.

Read first:

1. `docs/reference/kvk_source_migration/s11_g4_production_inventory_handoff_20261002.md`
2. `docs/task_packs/S11 G4 Production Inventory and Staged Rollout - Task Pack - 20261002.md`
3. Current AGENTS/core references, then the linked accepted result, decision packet/seals, SQL repair checkpoint and authoritative `C:\K98-bot-SQL-Server` source. Resolve older dated statements using the new handoff.

Reconcile and preserve local evidence before live reads. Accepted evidence is at `C:\Users\cwatt\Documents\Codex\s11-operator-readiness-20261002`; final-manifest SHA256 `c739b758ab37d90ff36df6110c0d85291ab4a1722e528e3a7975f5342c768c67`; final source pins are in `security/final-reviewed-source-pins.json`. Later approval/docs have a separate manifest at `C:\Users\cwatt\Documents\Codex\s11-production-inventory-handoff-20261002`. Preserve old seals and compare source members individually.

Accepted source includes coordinated Viewer generation/retirement/recovery and **version 5 operator control**. Chris controls both machines and all export-command/import triggers. Do not reintroduce remote shutdown, process/session inventories, disabled-launcher proofs or fixed duration caps. Future writes need an actual no-conflicting-work/hold-until-completion-or-reconciliation confirmation, with active deployment identity/ownership safeguards unchanged. Read-only inventory needs no no-write period.

Production comparison target: MINI_AMD; SQL `mini_AMD` / `ROK_TRACKER`; last observed Bot is isolated hotfix `bd980c0f497faf2048eaf1fb6b79600662911763`, not production/main. `StartDLBotAfterSQL` is known; never invoke it. Establish exact access/identity, then prepare finite source-derived path/object read allowlists and full sealed commands/hashes. Execute approved grouped reads without another general approval cycle. Default limits: 60 seconds per operation; SQL connect 5s / statement 15s / lock 1s; at most 1,000 metadata rows/query and 20 MiB output. Stop on mismatch/access gap/timeout/uncertainty and retain partial results. No broad collectors, withdrawn helper, memory investigation, data scans or DBCC. Ask only for genuinely missing facts or broader effects.

Settled: one Windows account `single_account_application_v1`, Chris operator/reviewer, one production Bot/no test Bot. Manual Sheets owner `chrislos35@gmail.com`; existing Editor `sheets-service@statsupdate.iam.gserviceaccount.com` in `statsupdate`; sole key `0d8b70356ef2fb1ea002daac8e9533463aab5d18`, copies only production/local. No new service account/key, OAuth, key bytes or personal Drive substitute. Viewer access stays.

Five blank candidates Slots 02–06 were verified on 2026-10-02 at 11:43:04Z, each grid 0 / Sheet1 / 1000×26. Exact IDs and all 11 exclusions are in accepted `pool-bindings.json`. Slot 02 is proposed index, Slots 03–06 generation slots. No enrollment yet; no additional file creation needed for measured P=1,Q=0,R=0. Protect the completed demo index/report; do not repeat Google reads merely to refresh this handoff.

Preserve DB22 `S11_G4_Recovery_20260928_97337` ONLINE/RESTRICTED_USER/read-only/Broker-disabled and 119 media; DB23/DB24; all receipts and uncertain publications `e19c89ac-7977-5f28-ae4c-031807cd1728` / `54a2480a-26fb-5bad-a3f5-9321525a731c`. No restore/baseline/predecessor rerun; retain B02/B04R1/B05 qualifications. S6 measured rehearsal is already accepted; remaining S6/S8/G5 operational gates stay open. Empty-report/view-rehydration issues remain separate.

Deliver current production source/config/installed-state comparison, minimum source-backed staged SQL/deployment/enrollment/coordinated-validation/rollback proposal, exact commands/budgets/hashes where factual bindings exist, and explicit unresolved inputs otherwise. Never derive expected metadata from unreviewed runtime or install all 540 source objects. Future process identities and restricted SQL permissions cannot be fabricated from administrator access or tests.

Prepare separate complete draft Bot-mirror/SQL publication manifests: recommended now to checkpoint accepted source, but **publication is not authorized by this starter**. Inventory proceeds independently. No standalone docs PR, mirror-history push to production, reset/clean/stash, main pull onto the hotfix or automatic new task. Finish authorized inventory/preparation before presenting the next concrete publication/mutation decisions.

[Full handoff](../reference/kvk_source_migration/s11_g4_production_inventory_handoff_20261002.md) · [Task pack](S11%20G4%20Production%20Inventory%20and%20Staged%20Rollout%20-%20Task%20Pack%20-%2020261002.md)
