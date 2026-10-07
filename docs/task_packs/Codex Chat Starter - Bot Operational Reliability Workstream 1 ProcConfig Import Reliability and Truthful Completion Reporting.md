# Chat starter — Bot Operational Reliability Workstream 1

Continue ProcConfig Import Reliability and Truthful Completion Reporting, formerly embed Phase 2L.
Read [the programme](Bot%20Operational%20Reliability%20-%20Programme%20Pack.md), [task pack](Codex%20Task%20Pack%20-%20Bot%20Operational%20Reliability%20Workstream%201%20ProcConfig%20Import%20Reliability%20and%20Truthful%20Completion%20Reporting.md) and
[completed design/manifests](Bot%20Operational%20Reliability%20Workstream%201%20-%20Design%20and%20Manifests.md), then current AGENTS.md/core references.

The audit/design is already complete. Programme boundary and documentation are approved;
runtime/test/SQL implementation is not. Read the completed
[backlog assessment](Backlog%20Priority%20Assessment%20-%202026-09-09.md): the operator selects
KVK Source Migration first, private inventory second, WS1 third. A proved KVK implementation
dependency may justify a separately approved exception. Do not infer implementation
selection from WS1 numbering or from historical Phase 2L instructions. Check for new operator
decisions first; revalidate source drift and exact manifests if resuming later.

Final Phase 2K closeout, 2026-09-09: mirror #262 merged at 12:06:38 UTC and production
#569 at 12:07:06 UTC. Verified mirror main: `1a3a5de3d2e9f349c276725f6271ef19a7517c4f`;
production main: `1e72949dc69f1a1e5a529dbf1951039fe0ba74a6`. Operator supplied the same
production bot HEAD and empty `git status --short`. Associated restart invoked 12:08:56.672,
ready 12:09:10.755, full startup complete 12:09:15.539, new child PID 4800. This closes the
final deployment evidence gap; candidate smoke/test revisions below remain historical evidence.


Preserve Phase 2J removal, H/I sessions/defaults, Phase 2K receipt/claim semantics, SQL transaction
ownership and no automatic replay. The proposed complete fix covers SQL result/resource lifetime,
confirmed versus unknown commits, worker/native/envelope parsing, dry-run argument forwarding,
reports/manifests, telemetry, downstream effects, cleanup and cancellation/timeout across all
participating direct/admin/startup/pipeline paths. At most one backend execution per invocation
after submission; no recovery/replay protocol. Proposed SQL mutation manifest is empty.

If implementation is explicitly selected and approved, follow the exact accepted manifests and
meaningful risk tests, source-of-truth SQL validation, Changes-only/Deep-off reviews, natural smoke
and bounded rollback. Otherwise stop after the requested assessment or design revision. No live
SQL/calendar/state mutation or forced import is authorized by this starter.

Natural Pre-KVK/off-season and Phase 2F public-save evidence remain independent follow-ups.
Broader executors, lifecycle, DM/JSON, durable dispatch and cross-invocation admission belong to
separate programme workstreams; do not add them to WS1.
