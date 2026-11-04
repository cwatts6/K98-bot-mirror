# Preparation request contention

The production ProcConfig failure occurs while creating its preparation request:
the account application lock returns timeout before provider collection or SQL
publication begins. Other preparation transitions already use the shared bounded
coordination retry; request creation did not.

Apply that existing retry policy to request creation. Retry only the attributed
timeout after rollback and connection close acknowledge, within the shared
one-second/eight-attempt budget. Keep the original request content and hash;
existing matching requests return their original identity. Unknown commits,
connection failures, cancellation and deadlock outcomes are not replayed.

No SQL migration, permission, provider, guided approval or held-resource rule
changes. Business execution is outside this transaction and outside the retry.
Disposable SQL tests cover a transient lock, permanent lock and lost commit reply.
Existing contention tests cover cancellation, rollback/close failure and deadlines.
Final Changes review is required for the exact mirror/private diffs; Deep is off.

This slice addresses short-lived request creation contention. Durable handling
of exhausted pre-request admission, monitor diagnostic clarity, configuration
membership mismatch and its linked queue, still-needed outputs and remaining
unknown-write/producer/rollover workflows remain mandatory P0b work. It does not
claim that existing held reservations are safe to release or certify import/export.
