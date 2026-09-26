# S10C starter — Legacy and Scan Export Adapters

## Current status — S10E merged; S11 review/scope next, 2026-09-15

S10E Bot [mirror #280](https://github.com/cwatts6/K98-bot-mirror/pull/280),
[production #587](https://github.com/cwatts6/k98-bot/pull/587) and
[SQL #88](https://github.com/cwatts6/K98-bot-SQL-Server/pull/88) are merged and locally pulled.
Bot main/origin main `721ad7e0cd6b160ddddad328c2338a98bdfb6e0a`; production/main `3dbe63e7a47175df85ed17814ea06f9dd3d130b7`; SQL main/origin main `2352a898881d4b74d6eec153bb3cb381d6162041`.
**No changes have been pulled to the bot machine.** Repository delivery is complete;
SQL installation, real provider/Discord execution, runtime acceptance and activation remain unproven.

Next: **S11 Controlled Release and Acceptance, initial review/scope only**:
[task pack](../Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S11%20Controlled%20Release%20and%20Acceptance.md) and [starter](../Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S11%20Controlled%20Release%20and%20Acceptance.md).
Read the [S10E closeout and exact next-PR manifest](../../reference/kvk_source_migration/s10e_closeout_and_s11_handoff.md).
S11 starts from S7's eight-document release proposal plus mandatory carry-forward docs;
reconcile real composition/installation/operational gaps before proposing any runtime scope.
Its eventual authorized Bot PR MUST include every listed pending document, both S10E archive
move identities, this closeout and S11 pack/starter. Verify filename AND previous_filename,
exact content and absent-at-base proof; counts are insufficient. No standalone docs PR,
mixed repositories or manufactured implementation. Pending SQL closeout edits belong only
in the next genuine authorized SQL implementation PR; otherwise carry them forward.

Preserve all recovered documentation evidence, S6-OPS01/PERF01/CAP01, both uncertain publications
and retained data. S8A six scripts, S8B 50 cases/actual restore versus offline history, and S8C
seven local checks remain distinct. S10C/D/E static authoring is not installation/provider proof.
No predecessor rerun, SQL/provider/Discord operation, bot-machine pull/restart/deployment,
activation, new task creation or Git publication is authorized by this documentation closeout.
Earlier dated pending/next-slice instructions are historical and do not reopen accepted work.

## Historical S10D closeout — 2026-09-15

SQL #87 is merged and locally pulled at `80353a6280e523f30c27e724f71e7b47dadadd16`.
Bot main/origin main remains `bf3eccf964601e2975dd86eefe96f7b0153be3bb`; production/main remains
`aa1821adbde9ccda47797caa83b5d5a9958bfce9`. **No changes have been pulled to the bot machine.**
S10D authoring, offline checks and Changes security review are complete; SQL installation and
provider/Discord execution are not established. S10C remains source/static SQL evidence too.
See [S10D closeout and exact carry-forward manifests](../../reference/kvk_source_migration/s10d_closeout_and_s10e_handoff.md).

Next: **S10E Export Operator UX and Rollover, initial review/scope only**:
[task pack](Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S10E%20Export%20Operator%20UX%20and%20Rollover.md) and [starter](Codex%20Chat%20Starter%20-%20KVK%20Source%20Migration%20S10E%20Export%20Operator%20UX%20and%20Rollover.md).
The eventual authorized S10E Bot implementation PR MUST include every pending Bot document in
that closeout, this pack/starter and all required archive identities. Verify filename AND
previous_filename, or exact merged/content and absent-at-base proof. No standalone docs PR,
repository mixing, manufactured implementation or renewed predecessor/grouping approval.
Both SQL documents were delivered in #87; their new closeout edits stay in SQL for the next
actual authorized SQL implementation PR. S10E scope must assess any genuine SQL delta separately.

Preserve S6-OPS01/PERF01/CAP01, both uncertain publications and every retained database/file.
S8A six scripts, S8B 50 cases/actual restore versus offline history, and S8C seven local checks
remain distinct; none is new live Discord or deployment evidence. Shutdown stops admission and
drains owned delivery; uncertainty retains claims. No lease-age/job-state release.
This documentation closeout authorizes no implementation, Git publication, SQL/provider/Discord
execution, real import/export, bot-machine action, deployment, activation, predecessor rerun or
new task. Earlier dated checkpoints are historical; the current closeout controls the next step.

Historical S10C instructions and implementation evidence follow. The merged closeout above controls current status.

Continuation checkpoint (2026-09-14): the operator has approved expanded Bot implementation
and the separate eight-path SQL authoring/offline-validation patch. See the task pack's approved
implementation checkpoint for current files and validation. The initial starter below is historical;
do not re-ask settled scope or SQL authoring approval. Publication, execution, deployment and
activation remain excluded. Separate Changes/Deep-off reviews are still required.

Please begin **S10C Legacy and Scan Export Adapters, initial review/scope only**, using
[the task pack](Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S10C%20Legacy%20and%20Scan%20Export%20Adapters.md)
and [the S10B closeout and exact documentation manifest](../../reference/kvk_source_migration/s10b_closeout_and_s10c_handoff.md).
Read current AGENTS/core references, approved S7 contract/manifests, authoritative SQL,
architecture/EndScanID amendment and retained S6/S8 evidence. S10B review is complete, mirror #278
and production #585 merged and locally pulled. Bot main/origin main is
`8ae66da6e12b53781c5df0d46a8ee79314cecead`; production/main is
`40c2e48111ebbe44d58d71269dea63a6dd9388b7`; SQL #85 remains accepted at
`3776dfa6b0892a8800d236fdf111c4d2f93c3813`. **No bot-machine pull occurred.**

Recheck both repositories and preserve all pending work. Scope the exact S7 26-path S10C boundary
plus every pending Bot document in the closeout, this pack/starter and both S10B archive move sides.
The eventual S10C implementation PR must include them all. Verify filename AND previous_filename
coverage or exact merged/absent-at-base proof; counts alone are insufficient. SQL delivery-log and
migration-README changes stay separate for the next authorized SQL PR. No standalone docs PR or
repository mixing. Do not re-ask settled grouping or predecessor acceptance.

Route automatic/manual legacy and scan exporters through common admission and request pacing.
Capture immutable complete outputs/config/header/provenance under shared writer/snapshot admission;
pass the owner token to nested helpers, avoid self-deadlock, preserve UPDATE_ALL2 transaction ownership,
and never hold a SQL transaction over provider requests or waits. Do not reread mutable tables per tab,
infer recompute completion from ScanID, or label advanced output as an earlier committed generation.
Retain durable spool digest/length/owner, pending capture evidence and explicit unavailable outcomes.

Preserve running A when B arrives, eligible pending-only coalescing, daily SCANORDER/history,
account fairness, resolved destination-ID conflicts, deterministic owner/fence/version CAS, attempts/
parts and scoped receipt identity. Pace both gspread HTTP and google-api execute requests with
server-UTC reservations, completion checkpoints and common bounded cooldown; uncertainty and late
threads retain claims until authoritative reconciliation. Job state and lease age cannot free resources.
Retain S10B registration-aware intent lifecycle and one-period-at-a-time compaction.

Preserve fixed season source, independent stats/targets/publication/roster/history/daily consumers,
supplied overall/B0 and authoritative aggregates/DKP, UTC starts, unused scans, movable within-season
windows, exact endpoint chain, sealed inputs/CAS, matched UpdateID and explicit counterpart attestation.
No mixed sources, summed-fight overall, silent legacy fallback or SourceRouting.Enabled-only activation.

Return scope, risks, tests and an implementation plan for approval. No implementation, Git publication,
SQL/provider/Discord execution, real imports/exports, bot-machine pull/restart/deployment, activation,
predecessor rerun or automatic new task. No new top-level command or S10D/E/S11 implementation.
After implementation approval use security routing then Changes, Deep off, on the exact Bot target;
assess any SQL delta independently. Preserve all S6 open gates, both uncertain publications and all
retained databases/files. Keep S8A six scripts, S8B 50 cases/actual restore and offline history, and
S8C seven local checks distinct; none is new live Discord or deployment evidence.
