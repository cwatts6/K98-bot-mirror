# S11 direct permission snapshot ordering

The direct application permission verifier checks exact row sets and then hashes
the complete observation. Its grants, memberships, application-grants and
token-grants queries previously had no final ORDER BY. An unchanged permission
set could therefore produce different observation bytes when SQL chose a
different row order.

The four existing queries now order by every returned identity/state field.
Their UNION projections already use Latin1_General_100_BIN2 for names, so the
final ORDER BY uses the projected aliases without adding expressions that SQL
Server rejects in a UNION order clause. No grant, role, principal, source manifest,
data query, credential configuration or permission acceptance rule changes.

Validation performed locally:

- Existing direct permission and runtime composition tests: 380 passed.
- All four actual metadata queries compiled against the local SQL Server using
  session NOEXEC; no production connection or persistent SQL write occurred.
- Three constant JSON input permutations per category returned identical ordered
  rows using the same projected sort keys and binary collation.

For rollout, retain prior observations and seals. Assemble the direct permission
contract in the newly specified query order only after independently reviewing
its existing source/permission contents. The source correction must pass review
and normal mirror/private promotion before production deployment. Static runtime
installation, actual process binding, enrollment and activation remain separate
operational steps. The SQL repository needs no migration for this correction.
