# P02 D5b closeout — 2026-11-11

Status: **D5b complete within the approved isolated qualification scope.**
The six actual maintenance children and the remaining report checks have passed.
This closes correctness qualification on the single disposable copy; D5c-f,
D6 promotion and production acceptance remain outstanding.

## Accepted evidence

| Obligation | Result |
| --- | --- |
| 42 detailed report states | Native candidate captures reconciled against authenticated retained source data and historical captures. The supplementary comparison verified 391,184 additional exact cells. No rank tolerance was needed. |
| 14 exports | All 49,468 rows and 827,683 cells preserve their values through the current bot formatter. All 14 prework exports match accepted historical exports; 13 candidate exports remain identical. The summary export's rolling-window changes are independently explained. |
| Source-data oracle | 486,842 source rows; 415 affected governors; 19,920 endpoint cells, 9,960 raw window cells, 6,640 latest/rank cells and 144 aggregate cells independently checked. All 768 changed ordinary final window cells are source-explained; zero source rows fall within the uncertain clock boundary. |
| Names | 58,659 current display-name checks against 2,449 independently derived latest names; historical alias output retains its distinct contract. |
| Rollback and cleanup | All 57 captured objects, including the additional alliance synchronization state, exactly match their prework row multisets after rollback. All 171 capture files passed hash/size/row checks. Physical SQL session closure verified. |
| Six maintenance children | import, configuration, player_report, kvk_output, final_stats and post_import qualified with actual physical work and owned completed claims. The first five completed rows remain unchanged; the approved one post_import retry is consumed. Backup demand remains visible; no backup job was dispatched. |
| Q05 receipt controls | Existing 146 passed / one deselected offline result retained, including 49 receipt-contract controls. Current relevant runtime and test bytes match that validated candidate. The 20 retained-payload compatibility tests also passed during this closeout. |
| Original queued bytes | Original 17,516,820-byte payload remains SHA-256 `24e9f15dc71d0e3ef2b0d2e08383f9c623bb37328521126336504b896775264c`. |
| Q06 boundary | D5b source classification retained: managed readers require schema exclusion; arbitrary raw readers/ad-hoc DDL are outside the safety claim. Original SQL 3961 evidence remains open for the two native arrival orders in D5c. This is not a native Q06 pass. |

The numerical check counts overlap where state and export expose the same values;
they are evidence coverage counts, not a claim of that many unique business cells.
Original NULL, integer/decimal precision, negative, overflow, halfway-rounding and
retained payload contracts remain covered by the accepted offline controls.

## Receipt custody

Private evidence remains under `C:\discord_file_downloader\.codex_artifacts\p025`.
The append-only closeout `d5b-closeout-acceptance.json` maps all 64 original cases
to their current evidence/disposition without rewriting the original case manifest.
Its SHA-256 is `bd477a1ea4c09c1aba655c87463b2fe335d651f8c9aa1724d9f6e70f5ea96888`.

| Evidence | SHA-256 |
| --- | --- |
| `d5b-reports-v2-result-0863e498862c48bcaf4a1be9d1ec7237.json` | `4e3e0fdfe2cd0408f48868336ee8b642cb11ff8cf52b697ad59dc323949a6458` |
| `d5b-reports-v2-result-0863e498862c48bcaf4a1be9d1ec7237-adjudication.json` | `6cc8fbd02705319701e8d7d3ecefab978dfefada51823bdf2c27bfb0da287b43` |
| `d5b-continuation-result-715c675f474c4d2aae0517dbfacf4f10.json` | `dbfc23fb7687ed4cd5952a1d9fd31ac4e5b6382710fdeb96bf5348cf8ac7601b` |

The closeout also binds the detailed-history adjudication, offline correction
validation, current source hashes, payload test XML and host adjudication scripts.
The native report run took 24.7341248 seconds, used 41 client commands and returned
141 metadata rows. Its report clock interval was 20:23:13.827–20:23:19.617 UTC.
The receipt acknowledges rollback; host comparison independently establishes
restoration. No SQL or VM operation was performed during host adjudication.

## Preserved failures and limits

The first maintenance error 15247, the row-cap and recovery-session refusals,
the report V1 remoted-list comparison refusal, their scripts, intent markers and
receipts remain immutable. Successful continuation does not erase those events.
The report V1 refusal preceded all report workload; V2 corrected only comparison
of remoted lists while retaining state checks. The approved copy-only ownership
alignment remains recorded separately from unchanged permission grants.

The original database, production files/guards and evidence remain preserved.
No import replay, new input, provider delivery or permission grant occurred.
The **21-input allowance remains consumed**, with zero additional inputs.
The carried rehearsal budget now has **1,480 seconds remaining**; all statement,
row, receipt, resource and isolation limits remain unchanged. The approved storage
exception and ownership alignment do not authorize additional resource or access
changes. Retain the VM, disposable copy, qualification disk and evidence as-is;
this closeout requests no cleanup, reset or rerun.

## Validation and next boundary

The report V2 source packet completed Changes review
`3b2a4c34-0586-4040-9501-7063f9fd9935` with zero reportable findings; its source
bytes remain pinned. Existing Q05 review and offline validation remain applicable.
This closeout adds host-only evidence adjudication and documentation, without
changing runtime code, SQL, permissions or the executed packets. A new security
scan is therefore skipped for this closeout delta; it would not supply additional
native correctness evidence. Full-suite, smoke and command-registration runs are
skipped because this delta changes no bot runtime or command registration. The
focused payload checks passed 20 tests; their one unknown `asyncio_mode` warning
comes from intentionally disabled plugin loading in the bounded offline runner.

Closeout gates: architecture validation passed with zero applicable Python files;
deferred-item validation passed; security-routing validation passed with zero
errors/warnings. The test selector ran; its broader release/schema/permission
recommendations are skipped for this documentation-only repository delta because
no release identity, schema, permission code or application contract changed.
Local Markdown links and whitespace were checked separately. No new deferred
optimisation item is introduced; the existing D5c-f obligations remain active.

Next is a **source-only D5c review and concrete execution plan** covering managed
reader/schema-exclusion arrival orders and the remaining concurrency boundaries.
Bring that plan back before additional native execution. D5b does not establish
contention, fault/restart, balanced cost, full-flow or production acceptance.
The original D5c-f and D6/D7/P03/P04/P05 obligations retain their owners and limits.

Related: [report execution packet](Startup%20Import%20Export%20Reliability%20-%20P02%20D5b%20Report%20Execution%20Packet%20-%202026-11-11.md),
[obligation reconciliation](Startup%20Import%20Export%20Reliability%20-%20P02%20D5%20Obligation%20Reconciliation%20-%202026-11-11.md),
[preparation scope and Q06 boundary](Startup%20Import%20Export%20Reliability%20-%20P02%20D5b%20Preparation%20Review%20and%20Execution%20Plan%20-%202026-11-11.md).
