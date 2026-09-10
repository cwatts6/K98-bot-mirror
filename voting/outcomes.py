from __future__ import annotations

from voting.models import VoteOutcome, VoteSnapshot
from voting.vote_modes import is_multi_select


def _pct(count: int, total: int) -> str:
    if total <= 0:
        return "0%"
    value = (count / total) * 100
    return f"{value:.1f}".rstrip("0").rstrip(".") + "%"


def vote_outcome(snapshot: VoteSnapshot) -> VoteOutcome:
    total = int(snapshot.total_votes or 0)
    if total <= 0:
        return VoteOutcome(kind="no_votes", summary="No votes were cast.")

    top = max((int(option.vote_count or 0) for option in snapshot.options), default=0)
    winners = tuple(option for option in snapshot.options if int(option.vote_count or 0) == top)
    winner_ids = tuple(int(option.option_id) for option in winners)

    if len(winners) == 1:
        winner = winners[0]
        if is_multi_select(snapshot.vote_mode):
            return VoteOutcome(
                kind="top_selection",
                summary=(
                    f"Top selection: {winner.label} selected by {top:,} voter"
                    f"{'' if top == 1 else 's'} ({_pct(top, total)})."
                ),
                winning_option_ids=winner_ids,
                top_vote_count=top,
            )
        return VoteOutcome(
            kind="winner",
            summary=(
                f"Winner: {winner.label} with {top:,} vote"
                f"{'' if top == 1 else 's'} ({_pct(top, total)})."
            ),
            winning_option_ids=winner_ids,
            top_vote_count=top,
        )

    names = ", ".join(option.label for option in winners)
    if is_multi_select(snapshot.vote_mode):
        return VoteOutcome(
            kind="top_selection_tie",
            summary=(
                f"Top selections: {names} selected by {top:,} voter"
                f"{'' if top == 1 else 's'} each ({_pct(top, total)})."
            ),
            winning_option_ids=winner_ids,
            top_vote_count=top,
        )
    return VoteOutcome(
        kind="tie",
        summary=(
            f"Tie: {names} with {top:,} vote"
            f"{'' if top == 1 else 's'} each ({_pct(top, total)})."
        ),
        winning_option_ids=winner_ids,
        top_vote_count=top,
    )
