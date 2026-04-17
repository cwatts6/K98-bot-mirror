from __future__ import annotations

from ui.views.mge_signup_view import MGESignupView


class MGESimplifiedSignupView(MGESignupView):
    """Simplified public-facing MGE signup view for player/data channel use."""

    def __init__(self, event_id: int, admin_deps, timeout: float | None = None):
        super().__init__(event_id=event_id, admin_deps=admin_deps, timeout=timeout)
        for item in list(self.children):
            if getattr(item, "custom_id", "") in {
                "mge_switch_open",
                "mge_switch_fixed",
                "mge_edit_rules",
                "mge_refresh_embed",
                "mge_open_leadership_board",
                "mge_admin_completion_controls",
            }:
                self.remove_item(item)

        edit_button = next(
            (child for child in self.children if getattr(child, "custom_id", "") == "mge_edit"),
            None,
        )
        if edit_button is not None:
            edit_button.label = "Edit Sign Up"
