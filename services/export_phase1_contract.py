"""Fixed Phase 1 source amendment; never inferred from observed SQL state."""

from kvk.dal.new_source_import_dal import SourceConflict

MIGRATION_ID = "20261109_001_p02_phase1_sql_exports"
PROFILE_SHA256 = "520b58c1b25d80bd28f32324d99b5fede0d6191ddab93ac93469ed5c1f6e4041"
LEGACY_SOURCE_SHA256 = "85866ff40b43d392d1dfc8c07033135e0995cf90d3aaae4852d9c37efba7cda8"
APPLICATION_SOURCE_SHA256 = "6b118abe34bf49f26e2d000b312652c7f0a237ce63ad340f18650574ef94d317"
ACTIVATION_SCOPE_SHA256 = "e815147d0cea676248de87b50b39ced161151b86d10bd094993ae224ab58e816"


def phase1_contract(approved):
    """Return whether the protected contract selects this exact amendment."""
    if not isinstance(approved, dict) or "phase1_installation" not in approved:
        return False
    if approved["phase1_installation"] != MIGRATION_ID:
        raise SourceConflict("Exact reviewed Phase 1 installation required.")
    return True
