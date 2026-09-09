from __future__ import annotations


def test_rehydrate_module_imports():
    import rehydrate_views as r

    assert hasattr(r, "rehydrate_tracked_views")
    assert callable(r.rehydrate_tracked_views)


def test_ark_scheduler_import_regression():
    # ensure no cross-subsystem breakage
    import ark.ark_scheduler as s

    assert hasattr(s, "schedule_ark_lifecycle")
