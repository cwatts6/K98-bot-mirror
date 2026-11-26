> **Current handoff, 23 November 2026:** [Programme/P02 scope refresh and remaining work](P02%20-%20Scope%20Refresh%20and%20Remaining%20Work%20Handover%20-%202026-11-23.md) records the completed five-pair business comparison and fixed-reader timing follow-through. P02 remains open; D7 remains 1/4; all 68 requirements and 73 policy pairs retain their owners. The new chat starts with review and a finite remaining plan, then waits for the user to reconfirm before implementation or VM checks. Earlier pending/quota/design-only wording is historical; completed work and original failures must not be replayed.

# P02 D7 reconciliation and remaining P02/P03/P04 scope

Date: 19 November 2026. Status: offline review and scope; no new implementation or host operation.

## Decision and current position

**P02 is open. D7 remains 1/4 accepted: installed contracts.** The original retained workflow, required provider receipt and a fresh normal whole flow remain incomplete. E1 is closed; E2 failed and is retained. E1–E4 are the retained-work execution sequence, not the four D7 criteria. The original packet also requires E5, a fresh normal import/export, for the fourth criterion.

The running-release verification and active-pointer closeout are complete on the operator-supplied evidence. This closes the deployment-verification detour, not D7 or the programme. The running bot remains at `3a2694f7fc61606a3758eb8bf64065209f90c7d4`. Later code is merged and its standalone verifier has been used successfully, but those later runtime changes are not deployed in the bot.

The original D1–D4 deliveries and accepted D5/D6 evidence remain delivered under their recorded scopes. The remaining work is D7 plus specific correction obligations exposed during it: D2 observer/connection policy and D3 ownership must address the new coexistence gap; D4 must cover the next exact installed-tool/source transition; D5 must qualify those changed paths and missing integration cases. This does not reset earlier accepted qualification or require repeating the whole programme.

Current authorization is this offline review and documentation. Keep MINI_AMD running. Do not restart, replay either failed release, repeat E1, replay E2, execute recovery, import/export, maintenance, provider probes, SQL diagnostics or VM qualification under this scope. Earlier implementation and release approvals were used for their named corrections; this document does not extend them to a new design or business action.

This checkpoint supersedes older **current/pending** statements in the linked delivery records for present status only. Original receipts, refusal records, qualification limits and dated documents remain historical evidence. No accepted work is reset or replayed.

## What is merged, running and accepted

| Surface | Evidence and disposition | Remaining work |
| --- | --- | --- |
| Running Bot | Last verified private source `3a2694f7fc61606a3758eb8bf64065209f90c7d4`; release `45d2b070-5c20-43fe-a390-dd9980ae047c`; runtime incarnation 107. This includes deferred-KVK-index compatibility and initial admission settlement. | Later shared runtime corrections require a future reviewed deployment to become running code. Do not infer a fresh host state from today's offline source comparison. |
| Private main | GitHub branch read during this review: `d3ca554cc0e706d9d18856ef74f07685e2c894dd`. PR748/749/750 added running-release verification, rotated startup evidence, and catalogue/cleanup corrections. | A merge is not a bot update. Refresh the chosen target at the next release boundary. |
| Mirror main | GitHub branch read during this review: `8ef8514821783c0422c4747e61c0222f7ba3c459`. | Continue mirror-first review and identical private promotion for any subsequent approved change. |
| Standalone verifier | Corrected sealed package ran on MINI_AMD; `RUNNING_RELEASE_VERIFIED` at `2026-11-19T14:37:46.765736+00:00`. It used separate tool/dependency files. | Its success does not replace live Bot files, deploy shared DAL changes, or prove provider delivery. |
| Installed updater | Previously supplied checkpoint pins remain distinct from repository source: entry script SHA256 `7839e9830a9bff31c5b7e364c3f603a87b46b14437d036d51829f225e713f032`, source library `4c55bb82f055485689e574b6a5dded5d8e215ac730a0797f4c0d4e401f6ac7ab`, tool manifest `aa3f06a13ed342c404e48a42b36b0e3a0f859a4607abf6f773419d3aa030a337`. | Standalone verification did not upgrade the installed updater. Qualify the exact installed preparer, registry and target before proposing another release. |
| SQL | Recorded installed source `8a7aace75c55a6d17c9051edef9026dc25355af8`; authoritative local SQL checkout `b924cedd53e29dd88c0e9e7b66208b4fdc1e53ba`. Offline comparison found no `sql_schema` delta between these commits. | Latest verifier patches do not require a SQL migration. Any later lock-protocol redesign must be checked against the SQL repository and separately qualified if it changes SQL. |
| Updater bookkeeping | Operator reported `VERIFIED_HISTORICAL`, then completed finalisation, then `No active update. Historical evidence is retained under the updates directory.` | Closed. No updater execution or restart is needed to re-prove this. |
| Business acceptance | Verification reports `import_export=degraded`, `provider_delivery_verified=false`. Discord status is responsive; stale/unknown health fields are not fresh business evidence. | D7-R/P/N and their actual P03/P04 dependencies remain open. |

The successful verification recorded 50 normal SQL statements plus one dedicated schema-release statement, no first failure, three acknowledged connection closures and an unchanged bounded startup interval before/after. Original start remained `unconfirmed_preserved`; original readiness remained `unstarted_preserved`. Separate acceptance was recorded without rewriting those outcomes. Earlier failed release `67c57800-78ba-4293-a243-d314643c8b42` remains retired without verified readiness. Both failure histories and earlier verifier refusals remain intact.

The live-to-private diff includes three shared runtime modules: `services/export_execution_dal.py` (four catalogue query optimizations), `services/application_maintenance_dal.py` (typed refusal and optional verifier cleanup adapter), and `services/runtime_admission_diagnostics.py` (classification). Remaining changes are operational tooling, packaging, tests and documentation. The dedicated cleanup adapter belongs to the verifier; ordinary runtime lock release is not silently replaced by it. This delta does not eliminate the Exclusive observer conflict below.

## How we got here: missed contracts and introduced blockers

| Finding | Evidence and cause | Corrected scope and remaining limit |
| --- | --- | --- |
| Original E2 schema refusal | E2 completed input reading but did not commit configuration. The application comparator rejected the legitimate absence of exactly two deferred nonunique indexes on `dbo.EXCEL_FOR_KVK_16`: `IX_EXCEL_FOR_KVK_16_GovID` and `IX_EXCEL_FOR_KVK_16_KVK_NO`. The producer's output rebuild/deferred-index lifecycle was not represented end to end in the old strict contract. | Narrow compatibility with coherent lifecycle proof is deployed. Do not restore the obsolete proposal to run maintenance/create indexes merely to satisfy the old guard, broaden the allowance to other objects, or replay E2. |
| Observer versus reader/publisher contention | Bot `4bf9730d`, mirror PR540/private PR745, introduced Exclusive/Session/zero-wait `K98:maintenance-schema:v1` ownership across the full catalogue/lifecycle read. This conflicts with existing Shared readers and publishers. Earlier qualification proved guard refusal and real worker completion separately, not simultaneous coexistence. | **Still an in-scope P02 design/acceptance gap.** Initial admission settlement prevents one known verification overlap; it does not stop background workers contending after admission. Faster reads reduce exposure, not the incompatibility. |
| Catalogue cost at production scope | Manual diagnostics under the application principal reproduced three-second `HYT00` refusals in FK details, FK identity and key-constraint reads. Columns were also near the bound. Four candidate queries materialize scope; column results matched the original ordered bytes, and the combined candidate passed the reviewed baseline comparison. | Merged; used successfully by standalone verification. Application columns took 2.125 seconds execute time in the accepted run. One successful observation is not a headroom benchmark or concurrent-load qualification. Retain the three-second statement bound; do not substitute timeout increases/retries for design. |
| Cleanup coupled to observation budget | Offline tests exposed a path where an exhausted observation budget could prevent mandatory schema-lock release. | Dedicated bounded cleanup and connection custody handling are merged and exercised in the corrected verifier. This is a confirmed defect; it is not proof that this path caused the opaque production `OperationalError`. |
| Delayed verification after rotation | The initial verifier assumed the saved offset remained usable in active `log.txt`. Rotation invalidated that assumption while the bot continued running. | Corrected tool binds the retained startup interval across generations and checks it again. Ordinary appends need not invalidate the saved interval. No restart or whole mutable-log equality is required to prove the original startup. |
| Native fidelity and diagnostic mistakes | Earlier fake/native gaps included transaction-state handling and a caller bypassing the shared UUID/digest canonicalizer. A later manual diagnostic wrongly required `XACT_STATE()=0` despite the actual supported session state. | Preserve those failed checks and subsequent corrections. Test real SQL types/session semantics through actual callers; do not repair transactions or normalize evidence ad hoc to pass a diagnostic. |
| Concurrent confirmation allegation | The original flaky test required both simultaneous responses to be resolved although one action still owned execution. | Delivered correction tests truthful in-progress versus settled responses deterministically and one business transition. It did not make the execution guard wait; the earlier claim that this necessarily required a waiting implementation was unsupported. |
| Status and handoff ambiguity | Merged, installed, standalone-verified and business-accepted states were blurred; older pending checkpoints and allowance balances remained prominent. | This reconciliation separates the ledgers. Historical text is preserved but not current action authority. |

The exact historical lock holder and exact statement behind the original opaque verifier failure remain unproved. Later reproducible timeout/cleanup mechanisms must not be presented as a reconstructed production trace. Scheduled restart, failed deployment, subsequent runtime startup and later verification attempts are separate observations.

## Required P02 contention decision before another business attempt

Current Bot and authoritative SQL source still show this actor matrix. Test **both arrival orders**, keeping requester, actual holder, resource, phase and outcome distinct:

| Other actor | Ownership | When it precedes the Exclusive observer | When it arrives during observation |
| --- | --- | --- | --- |
| Passive recovery snapshot | Shared / Transaction | Observer refuses | Reader reports busy |
| `dbo.sp_ExcelOutput_ByKVK` | Shared / Transaction | Observer refuses | Publisher refuses with 51966 before its main write body |
| `dbo.usp_S11ValidateStatsReportStage` | Shared / Transaction | Observer refuses | Reporting remains held with 51966 |
| `dbo.usp_RunMaintenance` | Exclusive / Session | Observer refuses | Maintenance cannot acquire its guard |
| Another runtime/producer/catalogue observer | Exclusive / Session | Later observer refuses | Later observer refuses |

Zero wait prevents waiting, but can still create refusals and incidents. Legitimate maintenance/publication exclusion must remain safe; the acceptance requirement is useful progress with bounded cost and truthful deferred outcomes, not merely demonstrating that one participant fails safely. The existing ten-case model is evidence of the mechanism, not native concurrent qualification.

The next design must compare these options across startup, runtime writer admission, producer validation, passive recovery, maintenance, updater and standalone verification:

| Option | Value | Decision evidence required |
| --- | --- | --- |
| Explicit observation/admission sequencing with one owned coherent result | Can avoid duplicate startup verification competing with already admitted work. | Define freshness/invalidation, exact identity/version binding, worker admission handoff and all later runtime callers. Startup-only sequencing cannot close the general conflict. |
| Smaller protected observation interval | Can reduce unnecessary catalogue work while holding the lock. | Separate stable facts from changing output/lifecycle facts without weakening the full comparator; measure duration, total cost and both-order progress. Shorter duration alone is insufficient. |
| Coherently versioned observation | Could allow greater reader/publisher coexistence. | Define a SQL-backed consistency/invalidation contract across every relevant publisher and maintenance path; qualify changes during observation and bounded failure. This is broader Bot/SQL work. |

Start with the least complex design that meets the full matrix; do not preselect a new protocol without the evidence. Simply changing Exclusive to Shared would admit concurrent Shared publishers while their output/catalogue/lifecycle changes. Reusing stale metadata, raising deadlines, adding blind retries or waiting for a manually quiet host does not close this gate.

## D7 criteria and E1–E5 execution sequence

| D7 criterion | Current disposition | Evidence needed to finish |
| --- | --- | --- |
| D7-I: installed contracts | Accepted within its recorded observation scope; later running-release verification is additive. | Retain accepted D6 and later correction evidence; check only relevant action-time drift before the next approved action. |
| D7-R: original retained workflow | Incomplete. E1 accepted; E2 not applied; downstream configuration/cache/export unfinished. | Exact durable continuation/disposition preserving completed original stages and captures. |
| D7-P: required provider receipt | Incomplete. Input-read stream closure is not output delivery. | Bound job/attempt/stream/request/result/pacing/terminal/closure/publication and destination evidence. |
| D7-N: fresh normal whole flow | Incomplete. Startup cache/configuration is not this run. | E5: one latest genuine stats file through normal Discord input, import/report/config/cache/maintenance/export/notifications and standard outputs. |

| Execution step | Current status | Safe continuation condition |
| --- | --- | --- |
| E1: cancel exact old rolled-back configuration | Accepted and closed. | Preserve the original action/receipt; never cancel it again. |
| E2: configuration-for-export continuation | Failed/not_applied; successful input reads and cancelled uncommitted child retained. | After the P02 design/release gates, obtain current exact eligibility, approved configuration content/registration, ownership/fence/token and prior durable outcome. A newly approved decision is distinct from replaying the failed action. |
| E3: complete retained pipeline handoff | Not completed by this detour. | Review the new E2 result and capture-specific approval; bind its verified configuration stage, continue target cache, admit exactly one export, hand siblings to the same JobID. Preserve committed stages. |
| E4: review that export's delivery/closure | Not completed. | Observe that job's provider receipts, standard output and applicable maintenance. Do not resend to repair bookkeeping. E1–E4 success would take D7 to 3/4. |
| E5: fresh normal run | Not started for this acceptance. | After actual P03 blockers and essential demonstrated P04 corrections, Chris supplies the latest genuine file; bind exact input/effects and approve one normal run. This supplies the fourth D7 criterion. |

The retained D7 crosswalk remains **32 F + 16 C + 14 A + 6 D = 68 traceability records**, with **73 action-policy pairs** tracked separately. These are not 68 or 73 exercised production tests. Reconcile matching evidence against each original obligation; do not replace the original crosswalk with this summary.

## Actual P03/P04 dependencies versus historical records

| Item | Offline finding | Owner / required next evidence |
| --- | --- | --- |
| Original pipeline `86b597c1-0088-4b87-b668-7d8030299e0c` | Original scan 1245 / LastRunCounter 1093 and completed import, player cache, name cache and maintenance remain preserved. Unfinished configuration/target-cache/export linkage is the retained business dependency. | P03: action-specific current eligibility and durable stage binding, not another upload of the old input. |
| E2 action `836d2ef7-b56e-4775-b90a-cebb81a1d2d1` | Input read completed; seven read-only provider requests / 21 events / 29 evidence files formed a verified closed child stream. No atomic configuration checkpoint; child writer was reconciled cancelled. The shared SQL execution session being open did not invalidate the child stream closure. | P03: preserve old action, first failure, child and journal. A future new decision must use the supported `pipeline_export_v1` / `continue_configuration_export` path and current predicates. Do not substitute legacy-unknown, SQL-only retry or keep-prior routes. |
| Continuation code | Existing service/DAL support a uniquely linked cancelled child and truthful fresh-decision eligibility. Relevant continuation/pipeline files did not change between running `3a2694f7` and reviewed private `d3ca554c`. | No new P03 code defect is established by incident count alone. Current business eligibility still needs a later bounded read; this offline review does not manufacture it. |
| Retained capture siblings | Existing stats/player captures are retained for one export handoff. Five linked pipeline incidents do not imply five independent live jobs. | P03: exact preparation identities, immutable spool/registration, effective ownership and one resulting JobID; no independent enqueue or abandon. |
| F28 cancelled sibling and overview | Retained cancellation is historical; overview is an aggregate, not a producer. No current ownership blocker is established merely by these rows remaining visible. | P04: compare projection to durable outcomes when needed. No recancel, cosmetic clear, broad Recheck or group repair. `RecoveryService.refresh` may reconcile/write and is not a passive status read. |
| Historical failures, uncertain attempts and containment | Seven failed jobs/five uncertain attempts are historical inventory, not proof of a present hold. Request 177 / P03a.1 settlement stays closed. Historical containment presence alone is neither an active blocker nor an exemption. | P03/P04: determine actual effective fence, claim, containment and admission from exact current identities before action. Do not expire unknown outcomes by age. |
| Notifications | Historical run `c6a8f23c-c5f4-4ca0-964d-a0478f0a65f6` is closed/version 13 with Sheets failed; three acknowledgements and two skips remain evidence. | P04/D7: no resend, reopen or prune. Fresh normal run needs truthful admission/capacity/delivery results. No additional P04 implementation is justified unless a concrete blocker is demonstrated. |
| Monitoring and unrelated records | Retained Q04 cadence/freshness mismatch remains; partial-report totals are not global health or incident-generation rates. Missing historical board/empty event cache is not a demonstrated D7 blocker. | Keep existing owners and natural limits. Do not require zero incidents or repair unrelated domains to begin eligible work. |

The 19 November verifier checked the exact release session lineage and 63 retained preparations; it did not refresh all recovery-action predicates. Historical ownership readings are not authorization for today's continuation. P03a.2 whole-flow acceptance, wider P04 convergence, P05 independent combined acceptance, P01.4/P01.5 natural checks, SQL 3961 qualification limits and the historical Linux drain cause retain their original owners.

## Mandatory lessons carried into remaining scope

These are required acceptance gates for affected remaining work, not optional cleanup deferred to P05 merely to close P02:

| Gate | Owner | Required proof |
| --- | --- | --- |
| L1 producer post-state through next consumer | P02 Bot/SQL | Actual publication with zero/one/two allowed deferred indexes through the real contract guard, immutable capture, next writer and startup; changed/unrelated objects still refused. Reuse accepted native evidence and fill only the missing integration cases. |
| L2 observer coexistence and cost | P02 | Five actor roles above, both arrival orders, ordinary background workers present; exact lock mode/owner, protected duration, total observation/producer cost, useful progress, bounded busy/refusal behavior and no induced incident churn. Separate model, real SQL and actual-worker evidence. |
| L3 deadline-independent cleanup | P02 operational tooling | Exhausted observation/statement budget still permits bounded mandatory cleanup; failed/unknown acknowledgement retains custody. No release of another owner's lock, blind retry or acceptance before cleanup settles. |
| L4 native caller fidelity | P02/P03 | Actual SQL transaction states and native return types, UUID/digest serialization through the consuming helper/caller, sealed dependency completeness, deterministic concurrency events and truthful in-progress responses. |
| L5 attributable failure evidence | P02/P04 | Phase, statement digest, redacted SQLSTATE/native code and first failure; distinguish original cause from cleanup result and requester from proven holder. Unknown remains explicit; ordinary busy polling must not manufacture new incidents. |
| L6 delayed verification | P02 release tooling | Rotation/append/truncation/generation changes, bounded immutable interval, late identity/evidence check and separate historical acceptance. Keep original failed receipts. |
| L7 exact installed-tool release path | P02 release owner | Offline rehearsal of the actual installed preparer/registry/dependencies, exact running predecessor and candidate target, protected bundle inventory, LF/CRLF source representations, custody and startup policy. No target-supplied transition trust. |
| L8 business continuity | P03/P04/D7 | Completed stages never replayed; new decisions bind exact previous outcome and current eligibility; one job per intended export; required provider and notification receipts; first failures survive current-state convergence. |
| L9 truthful programme ledger | Release/D7 reviewer | Merged, installed, standalone-used, point-in-time verified and business-accepted recorded separately; original denominators, limits and budget charges preserved. |

L7 is a concrete release dependency: the predecessor preparer reads its **own installed** transition registry and recognizes up to 93 entries, whereas current source recognizes 95 including running-verification and catalogue-cleanup transitions. Unknown protected transitions are refused. A target pull does not upgrade that policy automatically. The exact installed bundle must be reconciled and any required tool upgrade qualified before a future release; this is an offline readiness finding, not a newly observed host failure.

## Preserved evidence and allowances

Do not sum overlapping cohorts or recast earlier failures as passes. Preserve D5 128/128, release groups 12/12, regressions 996/996, D6 8/8, receipt chain 20/20, stage receipts 5/5, package 526/526 and copied inventory 549, post-state 52/52, source 853/853, SQL definitions 26/26, startup 3/3 and updater 13/13 under their original scopes. Later native N01–N09 acceptance retains its lab-lineage limitation and the explicit **separate guard-control / real-worker** proof boundary. It did not prove simultaneous observer/worker coexistence or provider delivery.

The current controlling allowance record is `Qualification-Completion-v1/adjudication-01.json` referenced by the 18 November admission handoff, not older 774-second/49-second checkpoints:

| Ledger | Carried forward unchanged |
| --- | --- |
| Setup | 400 seconds remaining |
| Native | 563 seconds remaining; grouped subset 389 |
| Windows faults | 42 seconds remaining; grouped subset 13 |
| Control | 0 remaining; 32 is a **prior reservation**, not an additional usable balance |
| Control insertion intents | 7 observed |
| Generated fixture accounting | 91,244 reserved; 908,756 remaining, within the existing scoped fixture authorization |
| Historical inputs / rows | 21 inputs / 95 rows consumed; no reset or refund |

Grouped subsets are not additive budgets. Existing database/backup/row restrictions remain; no new allocation is granted. Production diagnostic elapsed times stay in their separate observations. This offline document review consumes none of the native/Windows/setup/control allowances. The closeout summary's abbreviated `reserve: 32` means the prior reservation above.

## Ordered next work and closure ownership

1. **P02 design owner — next offline step:** settle the observer/admission/coherence design against L1–L7 and the actual Bot/SQL callers. Define exact acceptance cases, maximum cost and any SQL/updater changes before seeking implementation approval. Do not use another production verification attempt as the experiment.
2. **Implementation/release owner — after that scope is approved:** implement only necessary corrections, reuse accepted evidence, fill the demonstrated qualification gaps within the recorded allowances, and manage mirror-first then identical private review/merge. Preserve formal Changes review and all applicable gates; no routine whole-codebase scan.
3. **Release owner/operator — separately approved future rollout:** prepare one coherent private candidate including required shared runtime fixes and installed-tool compatibility, with exact predecessor/target and fresh custody/resource checks. Later standalone verifier success is not runtime deployment authority. Do not replay either failed release.
4. **P03 owner/operator — then action-time review:** collect the smallest bounded current eligibility evidence, review configuration contents/registrations and exact retained outcome, and prepare a new E2 decision for explicit approval. E1 remains closed. Historical blanket approval is not a fresh E2 token.
5. **P03/D7 reviewer — E3/E4:** inspect new E2 receipts, apply the existing capture-specific approval boundary, complete exactly the remaining stages and review one job's required delivery/closure. Do not replay completed input/import/cache stages or provider requests.
6. **D7 reviewer/operator — E5:** after actual P03 blockers and essential demonstrated P04 corrections, approve one new genuine normal input and its standard effects. Reconcile D7-R/P/N and all applicable original crosswalk obligations. Close D7 only on the required evidence; leave wider P04/P05/natural obligations explicitly owned.

No host command is needed now. The immediate deliverable is the offline design decision in step 1, not a latest-version update or an E2 retry.

## Evidence provenance and validation

This review reconciles the original D7 `acceptance-register.json`, `D7-register-and-execution-packet.md`, E1–E4 packet (including E5), failed E2 review and corrected business/schema adjudications; the admission handoff and qualification-completion ledger; the retained contention-origin audit; current Bot/SQL Git source; remote main identities; and operator-supplied closeout outputs. Host facts are reported observations, not an independent fresh connection made by this review.

Local preservation inventory and validation outputs are retained under `.codex_artifacts/p02-d7-reconciliation-20261119/`. The inventory pins the original sources and the sealed catalogue-verification packet. Historical pending text inside that sealed delivery packet is not edited; this checkpoint supplies the later acceptance disposition. The original complete D7 crosswalk and private exact-identity evidence remain authoritative for detail.

Related tracked records: [programme principles](Startup%20Import%20Export%20Reliability%20-%20Programme%20Principles%20-%202026-11-06.md), [D5 final source/D6 gate](Startup%20Import%20Export%20Reliability%20-%20P02%20D5%20Final%20Source%20Delivery%20and%20D6%20Gate%20-%202026-11-15.md), [running-release verification](P02%20-%20Running%20Release%20Verification%20-%202026-11-18.md), [rotation correction](P02%20-%20Rotated%20Startup%20Verification%20-%202026-11-19.md), and [catalogue/cleanup correction](P02%20-%20Verification%20Catalog%20and%20Cleanup%20-%202026-11-19.md).

Changed surface is documentation only: this task pack plus current-checkpoint overlays in Developer Quickstart, the reference index and Promotion Guide. Validate architecture, deferred-item structure, security routing, explicit-path test selection, introduced local links and whitespace. Runtime pytest, smoke imports, command-registration execution and native/host tests are intentionally skipped: no executable source, command registration, schema or configuration is changed. Security routing is a documented documentation-only skip; this review does not alter enforcement or execute the proposed design. Implementation will require its own SQL validation, risk-based tests and Changes review. No commit, PR, merge or deployment is performed by this documentation review.

Review validation: architecture passed with zero changed Python files; deferred structure passed for all four Markdown files after correcting one vague phrase (the original failed validator output is retained); security routing passed with zero errors/warnings; explicit-path selector completed. Its release/schema test recommendations, smoke imports and registration checks are skipped for the documentation-only reason above. Eight introduced local links resolve, whitespace checks pass, all 31 inventoried evidence files are unchanged, and all 17 sealed artifact hashes match the preserved manifest (18 packet files including that manifest). Full pre-commit is deferred to an actual publication step; this review used the applicable scoped documentation gates. Detailed results and skip reasons are in the local validation record.
