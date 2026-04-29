# boot_safety.py
def apply_boot_safety() -> None:
    # Force non-interactive matplotlib
    try:
        import matplotlib

        matplotlib.use("Agg", force=True)
    except Exception:
        pass

    # Pillow: no-op ImageShow to avoid GUI popups
    try:
        from PIL import ImageShow

        class _NoopViewer(ImageShow.Viewer):
            def show_file(self, *a, **k):
                return 1

            def get_command(self, *a, **k):
                return ""

        ImageShow.register(_NoopViewer(), order=0)
    except Exception:
        pass
