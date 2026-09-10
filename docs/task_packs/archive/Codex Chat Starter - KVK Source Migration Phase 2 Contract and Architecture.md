# Codex Chat Starter — KVK Source Migration Phase 2 Contract and Architecture

**Archived completed record - 2026-09-09.** Audit/architecture preparation completed; G2 approved. Retained as evidence, not a new execution instruction.

Prepared 2026-09-09. Paste the prompt below to authorize the bounded Phase 2A design task.
Creating this starter does not execute it. No implementation is authorized.

---

Start **Phase 2A only: contract and architecture design** for KVK Source Migration. Complete the
bounded documentation pass and stop for my architecture review. Do not implement anything or
prepare executable implementation packs before that approval.

Working copies: bot `C:\discord_file_downloader` (`cwatts6/K98-bot-mirror`), SQL
`C:\K98-bot-SQL-Server` (`cwatts6/K98-bot-SQL-Server`). Verify current branches, HEADs, remotes and
working-tree changes. Preserve all existing work; no pull, checkout/reset, merge, push or PR.
Distinguish local source from actual deployed evidence.

Read current repository instructions/core references and the canonical task template, then:

1. `docs/task_packs/KVK Source Migration - Programme Pack.md`, including latest updates.
2. `docs/task_packs/Codex Task Pack - KVK Source Migration Phase 2 Contract and Architecture.md`.
3. `docs/reference/kvk_source_migration/decision_and_evidence_register.md` and all five Phase-1 outputs.

The latest follow-ups supersede earlier missing-B0/open-period statements. B0 is designated:
`C:\Users\cwatt\Downloads\KVK_16_Baseline.xlsx`, SHA-256
`d28d58b3505eac2cfaffc144130ce8816f270496dee439842c49fc06064fe147`.
It contains 5,806 eligible governors across 36 kingdoms; 5,410 have both earlier sample endpoints.
Other original evidence is under `%LOCALAPPDATA%\K98\kvk-source-migration\evidence`; read its
`README_EVIDENCE.md` first, remembering it predates B0. Do not publish private workbooks or player rows.

Settled decisions — do not reopen:

- New source separate; preserve legacy and reuse compatible reporting interfaces.
- B0 fixes eligibility, all 36 kingdoms retained; later-only players excluded. Each player gain
  requires the correct start/end observations; no zero baseline or substitution from another period.
- Player DKP uses total-deaths differences and one WeightDeadsZ. Kingdom/camp values and DKP are
  authoritative; no provider formula/split request, no player rollup replacement, no camp sum replacement.
- Separate per-fight aggregate reports, with successive live revisions superseding the displayed
  values for that same fight until its final report. Never add revisions together.
- A separate final overall KVK report is authoritative overall; do not replace it with summed fights.
  Running-total reports are possible but not the chosen normal fight workflow.
- Filename times mean UTC scan start. Do not substitute local time, upload time or file timestamps.
  B0 scan start is operator-confirmed as **2026-08-26 04:07 UTC**. Filenames are ours to design,
  not a fixed provider convention; propose a simple naming/metadata workflow.
- KVK Windows and Camp Map sheet structures remain unchanged.

Use Phase 1 to focus current-code/SQL drift checks. Define precise observation/report/revision and
logical scan identities, metadata, live/final/correction rules, field precision/availability, roster
and player calculation rules, source-specific storage, atomic publication, shared consumer
contracts, cache invalidation, legacy compatibility and realistic rollback. Keep daily SCANORDER
and independent kingdom-only systems separate. Resolve engineering choices with concrete
recommendations rather than passing a long list of technical questions back to me.

Only Pass 4 has occurred. Three player-scan files are available in `C:\Users\cwatt\Downloads`:

- `auto_pass_lvl4_before_2026-09-05_1526 (1).xlsx`: start, **2026-09-05 15:26 UTC**.
- `pass_4_scan2_2026-09-06_1304.xlsx`: middle, **2026-09-06 13:04 UTC**.
- `end_of_zone_5_2026-09-07_0721 (1).xlsx`: end, **2026-09-07 07:21 UTC**.

Their validated hashes/coverage are in the latest audit follow-up. These are player observations,
not three kingdom/camp report revisions. Start/end have the same cell values as prior P1/P2 but
different byte hashes: design for re-export deduplication as well as true corrections. Use the
middle scan for live-player scenarios; do not require it for a valid start/end gain. Aggregate
revision samples remain optional; use synthetic cases. Do not request a later fight that has not
occurred or wait for the final overall report.

The operator confirms the local SQL/config repo is synced with production and offers production
RDP access if needed. Local definitions are sufficient to start design. Record operator-attested
parity separately from independently queried live rows/jobs; no RDP session is needed for this
design task. Use only authorized, available read-only access if a specific check becomes necessary,
otherwise retain that bounded readiness gap without searching for credentials.

Produce the three outputs named in the pack: contract/architecture, synthetic acceptance scenarios,
and evidence/validation log. Update programme/register/indexes additively. Include a draft slice
sequence, but leave exact implementation packs to Phase 2B after G2 approval. Apply separate bot
docs-only and SQL no-change security skips; no standard/deep scan. Run safe document checks and
report actual results and remaining limitations using the canonical delivery shape.

**Stop at G2 for my review. No self-approval, Phase 2B execution, code/test edits, SQL changes,
migrations, imports, processing, exports, Discord actions, restarts, PRs or deployment.**
