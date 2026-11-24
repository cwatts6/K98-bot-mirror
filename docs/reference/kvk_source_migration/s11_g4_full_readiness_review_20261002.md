# S11 full readiness review — 2026-10-02

**Review complete. DO NOT PROMOTE or activate S11.** Local report calculation and the standalone real Sheets demonstration succeeded, but the complete coordinated application does not yet satisfy the settled operating model. This review closes the review work, not G4, G5, S6/S8 operational acceptance or production rollout.

This is the current overlay for dated readiness statements in the September handoffs, release packet and S11 closeout. Preserve those bodies, receipts and seals. Local evidence is retained at `C:\Users\cwatt\Documents\Codex\s11-full-readiness-review-20261002`; see `ROLLOUT-AND-ROLLBACK.md`, `candidate-preservation.json`, `historical-member-comparisons.json`, `capacity-review.json` and the final manifest there. No SQL connection, provider request, Discord/RDP observation, provisioning, deployment, restart or Git publication was performed for this review.

## Candidate and completed evidence

- Bot HEAD `2046ecdbd983450ab5098ec2a0caebfda91e41ab`; SQL HEAD `4cd1554dc3d063e323f22350c88df1444cd0ed4b`. Pending changes remain unpublished. All 165 Bot and 18 SQL pending/recovered files were copied before review edits. Both initial diff checks passed. Local refs were read without fetching.
- All 26 executable members of the October 1 repair seal still match individually. The old manual-pool v3 seal has 5 unchanged and 14 subsequently changed members, none missing. Old seals remain intact; changed documentation is not source loss.
- All 540 SQL application source members match canonical source-list digest `f082cd0cbf28261cddf966a954a4564d34a81a552d796707eb90dc75a6baf3cf` (raw list SHA256 `06735c6f245e3c77f7506d18581f6c2d595c19a4484c6485a619abd544411aa0`). Source comparison normalizes CRLF to LF and preserves a UTF-8 BOM. This is source verification, not installation of 540 objects. Earlier 538-object and September digests describe older candidates.
- Local overall calculation: 5,806 eligible players, 5,417 paired, 389 missing end scans and 303 excluded; independent counter/DKP, ranking and aggregate comparisons passed. Coverage is the approved overall baseline-to-end interval, not Pass 4 alone. See [overall result](s11_g4_overall_local_publication_20261002.md).
- Real standalone Sheets demonstration: twelve sections read back exactly; second equivalent request reused the receipt without provider writes. This was **one upload and two requests**, not two independent uploads or changed-generation rollover. Existing owner, service-account Editor and link Viewer access remained. No automated file creation. See [demo result](s11_g4_standalone_sheets_demo_20261002.md). Demo seal SHA256 `800eb28c64dc425b81eb8d10b1841599513c1849b10792ad72b6543ef32b0c01` remains historical evidence.
- Retained DB23 minimal installation/permission rehearsal and DB24 real calculation are useful scoped evidence. Neither is complete application installation or production acceptance.

## Blocking review findings

### R1 — Full coordinated path still requires private staging

`kvk/services/new_source_delivery_service.py` rejects `preserve_public_staging` at line 290 and later requires private generation proof. The standalone transport option used successfully in the demonstration does not amend coordinated authority, durable attempts, reconciliation or recovery. Manual enrollment accepting public Viewer access does not resolve this mismatch.

Required next implementation: carry the settled public Viewer contract through the complete coordinated path and its durable state/recovery semantics. Partial public writes and uncertain outcomes must remain protected. Do not simply remove the private guard, fabricate a private proof or reinstate a private interval without a separately justified operator decision. Existing Viewer practice is settled.

### R2 — Typed key custody and writer exclusion do not represent the accepted two-host model

`core/export_execution_host.py` requires `credential_holders == [manifest.authority_sid]`; its writer-drain proof also requires actual exited process incarnations and ended SQL-session identities. Known copies are production and this development machine, using the existing account/key. The user confirmed the sole active key and no other consumers. Those facts cannot be transformed into exclusive custody or a current global drain by filling the present singleton field.

Required next implementation/review: explicitly bind the accepted production/development custody and writer coordination model, followed by bounded evidence for actual process/session exclusion. No new service account, new key, human OAuth or fabricated process evidence. The temporary no-write assurance for the completed demonstration has ended and cannot authorize a future window. Preserve the pending shared-account amendment.

### R3 — Referenced demo files are no longer blank enrollment candidates; capacity is insufficient

The index `1ydIKNmq74VWfD52u_Ft_l7hd7qOQgLWdpX8erQw7j7o` and report file `1Sfa6NJw4urC2ldTu16q5EGFSRR4VFPX0Pgt4paLiM1g` now contain the final referenced report. Keep both intact. Manual enrollment rejects nonblank files and does not implement adoption of this report.

Three blank spares remain: `1oNTj1W2OzdzZP4dpWNwvU3I81qRvnnlcn_uhoI8QVLQ`, `1m6R1p4hInf-CtL9bAK-fzc4emB38XoP8ViJEpuI9jA4`, `1JsMrUOCav1mQu2570M8tQ7RPauJD6fft_ztLhkx61mE`. Their retained evidence is not a fresh provider observation.

The actual manifest is one part, 23,388 data rows and 2,162,035 allocated generation cells. Current capacity rule is `1 + P + P + max(P,Q) + P + R`: minimum **five total files** for P=1,Q=0,R=0; six with one protected slot. Three files meet the structural enrollment minimum but fail operational capacity. At least two additional manually created blank files would be required to combine with the three spares for the minimum fresh one-part pool, subject to actual workload, retention/quarantine and role selection. Do not clear the completed report, assume referenced files are reusable, or automatically create anything. Larger workload sizing remains required; illustrative multipart calculations are not measured production load.

### R4 — Seven current typed proofs remain incomplete

| Proof | Retained support | Outstanding binding / acceptance |
|---|---|---|
| host_acl | Local protected copy and credential ACL checks | Exact final source, dependency/config inventory and deployed production path/custody closure |
| bot_identity | Historical identity observations; native/source tests | Actual Bot/authority process incarnation, token and held-handle evidence for the future deployment |
| identity_issuance | Existing service-account provenance, project/client/key facts | Current issuer/admin/impersonator closure and reviewed existing-identity binding |
| key_inventory | User-confirmed sole active key, expiry and two known copies | Representable reviewed two-host custody model and fresh exclusion evidence |
| file_access | Dedicated five-file access/readback from demo | New exact pool roles/grids, manual origins and complete protected/reference closure; occupied demo files excluded |
| writer_drain | Completed owned demo process exited; temporary production assurance | Fresh actual prior-writer process and SQL-session closure for the approved operation |
| sql_installation | DB23 minimal synthetic rehearsal; DB24 report calculation | Complete intended application contract, effective permissions/signatures and dynamic-output inventory on the actual deployment target |

### R5 — Installation, operational cases and G5 are not accepted

The production missing-object plan must be derived from fresh, narrowly approved metadata against the exact intended deployment target. `20260924_002_export_legacy_module_permissions.sql` needs exact deployment/signature tables, public-only module certificates and reviewed signature/countersignature material, including matching Import/master prerequisites. Sysadmin/db_owner or CONTROL/ALTER/IMPERSONATE/grant bypass does not prove application permissions. No signature bytes or installation state were inferred here.

The repaired migrations `20261001_001` through `006` substitute the older affected bodies; then apply `007` through `010` only where their source preconditions and installed state require them. Do not replay every migration by date, replay old bodies after corrections, or execute source snapshots as installers. See the gated rollout packet for dependencies and rollback limits.

S6 OPS01, PERF01 and CAP01 have real retained observations; older “not run” statements are superseded by `release_evidence_log.md` around lines 2922–2924. Remaining work is operator acceptance of limits, retained publication-pending handling, verified shared scheduling/exclusivity and capacity/retention/quarantine budget acceptance. The settled expectation remains 2–3 exports/day with no hard duration cap. S8 and G5 remain open. Native authority/pipe/child/drain/cooldown/queue/rollover cases require their own exact runtime bindings; source tests are not those observations.

Preserve uncertain publications `e19c89ac-7977-5f28-ae4c-031807cd1728` and `54a2480a-26fb-5bad-a3f5-9321525a731c`. No blind retry, clearing, retirement or fallback is approved.

## Checks, corrections and security review

Architecture, deferred-item validation, security-routing validation, test selection, smoke imports and command registration passed. The broad **offline** suite excluded the two explicitly gated live SQL suites: initial result **6,043 passed, 16 failed, 65 skipped, 8 subtests passed**. All 16 failures were stale fixtures in `tests/test_export_authority_launcher.py` and `tests/test_export_runtime_composition.py`: old automated-enrollment name/authorization and an uninitialized transport option. Fixtures now use the manual registration contract and explicitly select the ordinary private transport for the recorded-authority rejection test. No runtime source was changed.

Both affected modules were rerun: **391 passed**, including all 16 previously failing cases; the log-noise check confirmed operational logs unchanged for that rerun. The broad suite was not repeated after this test-only correction, and its failed invocation did not reach its final log-noise assertion. Do not report a single all-green full-suite run or combine overlapping test counts. Tests and complete commands/log hashes are in the review evidence directory. SQL live tests were deliberately excluded, not treated as passing.

Bot canonical Changes scan `a1b481ba-191f-4ed1-81aa-fc952094cfeb`: complete, 13 pending executable/config/deployment members, no reported findings; snapshot `6fe9092e5934cefcc0b9d66b13b7e51cbd5e1feb2d13ccd609d596e9b1221887`.

SQL canonical Changes scan `1b56fce5-048f-4084-b1a5-6f1255a4666a`: no reported findings, all 16 executable members reviewed, but the sealed tool report remains **partial** because it retained an earlier generic deferred-progress record. Preserve this qualification. Snapshot `ecfbbf776281109dc3b110c2fe3825fed97b39473437120232b4504c892f9a37`. A separate clarification records completed static work; it does not rewrite canonical coverage. Earlier SQL scan `7fc6e83f-5ef1-4b60-a772-3697b2287386` is complete, and its 16 executable source members still match individually. Both histories remain evidence. Neither scan is runtime acceptance.

After those scans, only the two offline test fixtures and review documentation changed. Routing decision: skip an additional security scan for this mechanical fixture/documentation delta because no runtime/configuration/dependency/permission/input/data-access/deployment/persistence behavior changed. The diff was inspected and the affected tests passed. Deep scan was off; no Codebase scan was launched. Token usage for the security agents was unavailable, not zero.

## Protection and actual next work

Retain DB22 `S11_G4_Recovery_20260928_97337` ONLINE/RESTRICTED_USER/read-only/Broker-disabled with all 119 media files. Actual historical restore and clean CHECKDB/DATA_PURITY are evidenced; the 15-table baseline covers 2,410,159 rows, with 352 other tables outside content scope. Keep B02 timeout and B04R1/B05 command-provenance qualifications. Do not rerun restore/baseline or make it writable. Retain DB23/DB24 and all receipts.

Production remains the last observed isolated hotfix `bd980c0f497faf2048eaf1fb6b79600662911763`, not production/main. Its successful startup/409-row upload/14 transfers are historical hotfix evidence. Memory investigation remains deferred; never rerun the withdrawn collector/helper. Empty KVK reports and view-rehydration warnings are separate issues.

Next work is the focused coordinated-path and two-host proof-contract amendment, then targeted validation and review of its actual diff. After that, bind a sufficiently sized fresh pool and prepare exact runtime validation commands. Production observation, deployment/activation, publication and G5 acceptance need separate explicit operator decisions. Local review does not need a maintenance window, and the expired September window is not reused.

Genuinely missing facts are the final pool file/grid roles and measured capacity/retention allocation; reviewed two-host custody/exclusion bindings; exact final deployment paths/config/dependency/source identities; current installation/signature/effective-rights inventory; actual future process/session identities; and named Discord actor/guild/channel/role cases for G5. The existing service account, owner, single account, single Bot, manual creation, public Viewer practice and key copies are settled and must not be asked again.
