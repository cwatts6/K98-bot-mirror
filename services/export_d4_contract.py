"""Fixed D4 successor over Phase 1; no observed state selects an amendment."""

from kvk.dal.new_source_import_dal import SourceConflict
from services.export_phase1_contract import phase1_contract

MIGRATION_ID = "20261111_001_p02_d4_combined"
PROFILE_SHA256 = "57944777e50b7dc9200220cfcc2ce767edb22a2e0972e02bc2cd6f04e23e8171"
LEGACY_SOURCE_SHA256 = "d25ed334edc4f2a71e0fa51d252a6d8ff7d65691f1ad909f0c65a24654eac4cf"
APPLICATION_SOURCE_SHA256 = "10d1598c1280039abe6c208b657815cf4a03efcfad397a6a6e67c3205723841f"
ACTIVATION_SCOPE_SHA256 = "7976d3dd9a54cb125e638f99b63fef871985617d45405910184e82d7ddce48b2"


def d4_contract(approved):
    """Require explicit D4 selection and its retained Phase 1 lineage."""
    if not isinstance(approved, dict) or "d4_installation" not in approved:
        return False
    if approved["d4_installation"] != MIGRATION_ID or not phase1_contract(approved):
        raise SourceConflict("Exact reviewed D4 successor over Phase 1 required.")
    return True
