"""Admission checks for permanently isolated physical provider destinations.

Queue exclusion leaves inputs and tickets intact for guided replacement. The
locked admission check closes the race between candidate discovery and a target
being isolated by another account. Provider dispatch independently checks SQL's
permanent fence, including for old processes that predate these queue checks.
"""

from kvk.dal.new_source_import_dal import rows

# Fixed SQL fragments only; no identifier is supplied by a caller or Discord.
ISOLATED_JOB_TARGETS_SQL = (
    "EXISTS (SELECT 1 FROM dbo.ExportJobResource retired_membership "
    "JOIN dbo.ExportContainedTarget retired_target "
    "ON retired_membership.ResourceKey='destination:'+retired_target.FileID "
    "WHERE retired_membership.JobID=dbo.ExportJob.JobID)"
)
AVAILABLE_JOB_TARGETS_SQL = " AND NOT " + ISOLATED_JOB_TARGETS_SQL + " "


def contained_resources(cursor, resource_keys):
    """Call after acquiring the sorted resource mutexes, before claiming them."""
    targets = tuple(
        k.removeprefix("destination:") for k in resource_keys if k.startswith("destination:")
    )
    if not targets:
        return []
    cursor.execute(
        "SELECT FileID,ContainmentID FROM dbo.ExportContainedTarget WHERE FileID IN ("
        + ",".join("?" for _ in targets)
        + ") ORDER BY FileID",
        *targets,
    )
    return rows(cursor)
