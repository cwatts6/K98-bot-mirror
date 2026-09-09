# Codex Chat Starter — KVK Source Migration Phase 1 Audit and Validation

Paste the prompt below into Codex with access to both supplied local repositories.

---

Start **Phase 1 only** of the KVK Source Migration programme: validate the earlier findings and perform the current-code/SQL end-to-end audit. Do not implement the migration.

Working copies:

- Bot: `C:\discord_file_downloader` (`cwatts6/K98-bot-mirror`).
- SQL: `C:\K98-bot-SQL-Server` (`cwatts6/K98-bot-SQL-Server`).

I consider both copies synced with Git. Verify current branch, HEAD, remotes and working-tree changes; do not pull, checkout/reset, merge or discard work to make them match an assumed state. Distinguish local code from deployed-version evidence.

Read the current repo instructions and canonical template, then:

1. `docs/task_packs/KVK Source Migration - Programme Pack.md`
2. `docs/task_packs/Codex Task Pack - KVK Source Migration Phase 1 Audit and Validation.md`
3. `docs/reference/kvk_source_migration/decision_and_evidence_register.md`

Private evidence is at `%LOCALAPPDATA%\K98\kvk-source-migration\evidence` unless I give you another location. Read `README_EVIDENCE.md` first. It contains the four original workbooks and the earlier assessment/CSVs, which include superseded advice. The master-baseline workbook has not yet been supplied/designated in this bundle. Do not substitute the Pass-4 start file as the master roster. Do not commit private workbooks or identifiable player-level evidence.

**Confirmed requirements — do not ask these again:**

- Follow similar logic to the existing KVK import/reporting process where compatible; preserve the old path while assessing a separate new-source route.
- Retain all 36 kingdoms for this KVK; the 1198 filename prefix is not a filter.
- A designated master-baseline workbook fixes the eligible player roster. Governors absent from it remain ignored even when present in later scans.
- Player gains require the correct window starting and ending observations. No starting observation means no calculable gain, not a zero baseline. Master-roster eligibility and window endpoint availability are separate checks.
- Player DKP uses total-deaths differences and the existing single `WeightDeadsZ`. No extra T4/T5 death-weight columns in `KVK_DKPWeights`.
- Kingdom/camp totals and DKP are authoritative as imported. The provider uses an exact tier-death split that cannot be exported. Do not recalculate DKP, infer the split, or block the audit asking for the split/formula.
- Do not replace supplied kingdom/camp data with sums of eligible players, or supplied camps with sums of rounded kingdoms. Detail/summary DKP equality is not required.
- Filename timestamps always mean **UTC scan start**. Verify current importer compatibility; do not apply UK local-time conversion or substitute upload time.
- KVK Windows and Camp Map should remain structurally unchanged. Audit their actual data/identity contracts before proposing any exception.

Trace actual upload routes, parsers, raw/staging/output SQL, configuration import, scan/baseline/window rules, processing and refresh orchestration through every affected report, command, embed/card, cache and export. Work backwards from consumers as well as forwards from imports. Establish whether adjacent kingdom-only systems are linked or independent; do not assume all KVK-named commands share a source.

Validate the earlier sample findings from the original bytes. Treat earlier numeric results as diagnostic leads, not acceptance results for the not-yet-supplied master roster. Check the aggregate-period question against existing logic first: an end-scan association must not silently relabel fixed-baseline totals as a later individual fighting window. Identify any narrowly remaining source-period decision without reopening settled rules.

Compare storage reuse, new staging/raw with shared reporting, and isolated new-generation storage using actual DDL/consumer constraints. Cover historic compatibility, exact scan-ID namespaces, missing fields/precision, retries/corrections, source selection, final/live/no-fight windows, source-aware caches and realistic rollback limits. Recommend a design and next PR-sized slice, but do not approve it yourself.

Phase 1 permits read-only inspection, safe offline checks and the named documentation outputs. No runtime edits, SQL changes, migrations, real imports, processing-procedure execution, external exports, Discord changes, restarts, production PRs or deployment. Use authorised read-only DB access only where already permitted and safe; otherwise record the deployed-state gap. Apply the task's per-repo security documented skips and do not launch a standard/deep security scan.

Complete all independent work even if B0 or live SQL evidence is missing. Create the five required Phase-1 audit outputs, update the programme/register and relevant indexes additively, and report actual checks/results and precise blockers. Use the canonical delivery shape from the task, ending with the remaining operator decisions, recommended next task and explicit stop point.

**Stop after the audit for my review. No automatic Phase 2 or implementation.**
