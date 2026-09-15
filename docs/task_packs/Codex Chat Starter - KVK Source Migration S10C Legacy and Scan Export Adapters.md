# S10C starter — Legacy and Scan Export Adapters

Continuation checkpoint (2026-09-14): the operator has approved expanded Bot implementation
and the separate eight-path SQL authoring/offline-validation patch. See the task pack's approved
implementation checkpoint for current files and validation. The initial starter below is historical;
do not re-ask settled scope or SQL authoring approval. Publication, execution, deployment and
activation remain excluded. Separate Changes/Deep-off reviews are still required.

Please begin **S10C Legacy and Scan Export Adapters, initial review/scope only**, using
[the task pack](Codex%20Task%20Pack%20-%20KVK%20Source%20Migration%20S10C%20Legacy%20and%20Scan%20Export%20Adapters.md)
and [the S10B closeout and exact documentation manifest](../reference/kvk_source_migration/s10b_closeout_and_s10c_handoff.md).
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
