# Ark Command Update Briefing

Share after the Phase 4 Ark command grouping PR is merged and before the next Ark cycle.

## Discord Message

Ark commands have been tidied up under one `/ark` command group.

What changed:

- `/ark_create_match` is now `/ark create_match`
- `/ark_force_announce` is now `/ark force_announce`
- `/ark_amend_match` is now `/ark amend_match`
- `/ark_cancel_match` is now `/ark cancel_match`
- `/ark_reminder_prefs` is now `/ark reminder_prefs`
- `/ark_set_preference` is now `/ark set_preference`
- `/ark_clear_preference` is now `/ark clear_preference`
- `/ark_ban_add` is now `/ark ban_add`
- `/ark_ban_revoke` is now `/ark ban_revoke`
- `/ark_ban_list` is now `/ark ban_list`
- `/ark_set_result` is now `/ark set_result`
- `/ark_report_players` is now `/ark report_players`
- `/ark_generate_draft` is now `/ark generate_draft`
- `/create_ark_team` is now `/ark create_team`

Why this changed:

- Ark commands are easier to find because they all sit under `/ark`.
- Discord command autocomplete is cleaner.
- The bot now has more top-level command headroom, which helps avoid Discord's command limit as new features are added.
- Existing Ark behavior, permissions, reminder settings, reports, buttons, dropdowns, and views are unchanged.

When using Discord, type `/ark` and pick the action you need from the subcommand list.
