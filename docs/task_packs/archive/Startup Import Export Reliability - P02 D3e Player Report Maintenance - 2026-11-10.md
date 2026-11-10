# P02 D3e: player report maintenance

Scope: move only STATS_FOR_UPLOAD FULLSCAN out of SP_Stats_for_Upload. Register player_report due inside its actual transaction/savepoint after required names and publication validation, before standalone commit. Preserve every other business statement, capture/provenance and D2 actual statement limit. Do not widen timeouts.

The existing standalone publication mutex K98:StatsForUpload:Publish must prevent optional FULLSCAN from racing its transaction. Worker takes that exact mutex in Session scope at zero wait for every maintenance kind before claim (post_import sp_updatestats also touches this report); conflicting publication leaves pending. The child requires all physical guards. Bot fresh-session custody explicitly verifies/releases this additional guard on success and failure. No new producer lock or permission grant.

Test actual full SP_Stats_for_Upload with authoritative tables and required naming helper, standalone and outer commit/rollback, invalid provenance, transactional due rollback, physical publication contention, real FULLSCAN and failure-after-business-commit without replay. Retain exact business-source comparison and D2 caller budget regressions. One focused mirror/SQL PR pair, Changes-only security reviews, Deep off. D4 installed/manual/signing and D5 scale costs remain; no deployment. Existing all-D3 authorization covers this work.

D3d predecessor is merged: Bot mirror PR516 b80c58139718e900b6c87f2c3c28fa1b338194b3;
SQL PR144 adb5f8a7f662be667fe0326d195ffaf5569704fa. Both automated reviews found
no issues; both SQL CI runs passed. D3d correction Changes scan
1e657dd2-fd12-45a9-b22d-2abd4ed7b631 completed with no findings across both changed
files, total331716 tokens (329606 input,324480 cached,2110 output).

D3e initial qualification: nine actual player-report native cases and36 DAL/D2
statement-budget cases pass. The native fixture loads the real full report,
required naming helper/view and table definitions, including actual name replacement.
It omits only the known absent KS4 sequence default and explicitly supplies SCAN_UNO;
this is controlled fixture qualification, not installed permission/signing proof.
Standalone and outer commit/rollback, invalid provenance and due-write rollback,
real FULLSCAN statistics, publication-holder deferral for player_report/post_import,
and real missing-object upkeep failure with committed data retained all pass.
Exact business SQL comparison permits only FULLSCAN -> transactional due registration.
116 focused updater cases pass:86 total entries, prior85 digest
7bf133f5b87e0bb3b0179592ba66de47c151f7c600252a04b6aa03a1d66500a9,
eight members/one changed. Byte cap and installed combined-jump refusal unchanged.

Coverage reconciliation found the historical finite-form test had not yet
accounted for D3c UPDATE_ALL2 or D3d CREATE_DELTA_TABLES; its first broader run
failed2 cases (129 passed). Test-only bridges now require each exact successor
hash before selecting the immutable predecessor; the delta predecessor JSON
retains exact Git source faddbd12 with fixed normalized hash, and player-report
inversion is authenticated before the existing frozen names/permission checks.
Mutation refusals cover all three successors. All36 historical compatibility
cases pass. No runtime installed allowlist, migration or grant was amended.
The restricted formatter stalled after writing3 files; its exact two owned
processes were stopped and formatting completed successfully with ordinary
host file access. Final updater checks passed116 cases after hashes refreshed.

Final combined selection:134 passed, one existing Google Python-version warning,
27.22seconds. SQL repository validator, exact business preservation, all13 source
mutation refusals and immutable P0 receipt checks pass. Architecture, deferred,
security-routing and test-selector gates pass. Full suite is reserved for the
stable combined D3 result after D3g; D3b full and D3c broader results remain recorded.
