# MGE startup contract amendment

## Problem and bounded correction

The installed version-2 application SQL contract includes `dbo.MGE_Events`,
`dbo.MGE_Awards` and `dbo.MGE_Signups`. The generic combined runner correctly refuses
the MGE schema family because its three new triggers change that protected
metadata. A valid release descriptor alone therefore cannot prepare this release.

The installed preparation policy now admits one exact descriptor, SQL ancestor,
profile hash and predecessor application-contract fingerprint. It derives a new
application contract by changing only the reviewed metadata hash and review ID.
The predecessor remains immutable; permissions, scope, sources, dynamic objects,
identities and both other SQL contracts are retained. A different descriptor or
predecessor contract refuses before output. Only the three application-scope
parents receive this amendment; installation and legacy protections remain
independent, including protection of those same names through either other scope.
The generic `combined_payload` protected-object refusal remains unchanged.

Existing `p0a_release.adapt_candidate` rebinds the Bot template, seed plan, policy
and gate hashes. It does not select the historical P0 release or change its policy.
The unchanged live predecessor and successor comparators still verify actual SQL.
This code does not learn an expected hash from the deployment target or from a
post-deployment observation.

## Independent derivation

Retained historical disposable metadata has exactly the installed application's
metadata and permission hashes. Original evidence SHA256:
`b9ed05df3e6ea295aff160659488ad34ad08065c431c1eb9cbcd23995de811fd`.
The original server/database identity remains retained; it is not described as a
live production snapshot. For the offline comparator, target identity was an
explicit surrogate while the original metadata and permissions were unchanged.

Expected trigger definitions came from `Get-K98MgeTriggers` in reviewed SQL commit
`9344a37656b034dd43867435e7c039ed20ae1c5e`. The runner explicitly sets ANSI_NULLS and
QUOTED_IDENTIFIER on. Three expected enabled AFTER trigger rows were added to the
baseline's `triggers` category in its BIN2 name ordering. No other category or
permission changed. A read-only query of the already qualified disposable database
confirmed all three native trigger rows, including definitions and flags, exactly
equal those independently derived rows. No SQL write or native case replay ran.

| Binding | SHA256 / identity |
|---|---|
| Complete predecessor application contract | `814a7e6be4ac3865ee29b65e3c55ec7ad06d4a2ddeb0831f5cf1480d39d9f49f` |
| Predecessor metadata | `12b7d6f1178e66708210088f59296a885ed7b11f894273bdfae874460ba96b07` |
| Derived successor metadata | `103e92000529669ec7213a397f1062036a7965ef1d9be4ea7712dcb91e7feb5b` |
| Complete successor application contract | `c9fa1f180386198630cdb62bc259408286ad8956b1a2be38963cb4c2e8ba0b00` |
| Amendment review ID | `26a303f7-e8b6-4be6-9dce-43086c78d98e` |

## Validation and remaining boundary

Focused tests cover a complete synthetic package, gate/plan/template rebinding,
unchanged predecessor and permissions, independent legacy protection, every
contract-field drift and every descriptor-field substitution. The existing full
startup comparator accepted the independently derived expected metadata using the
labelled surrogate target. Real production preflight is still required; this is
neither fresh production acceptance nor an elevated combined rehearsal result.

Scope is the existing updater preparation layer, its tests and this evidence
record. Runtime DAL/commands, SQL schema/runner, activation flags and provider work
are unchanged. The per-repository security route is Changes, Deep off, over this
exact correction. The updater package must be rebuilt after this correction and
separately approved for installation. Protected Windows/full combined qualification
and production operational approvals remain outstanding.
