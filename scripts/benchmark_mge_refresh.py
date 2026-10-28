"""Offline A1a comparison: real callbacks/render preparation; simulated SQL/Discord.

Run this same harness against baseline and candidate source roots. All SQL entry
is denied except fixture adapters. No source tree or operational logs are written.
Reported connections are simulated query connections, not a native SQL benchmark.
"""

import argparse
import asyncio
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import UTC, datetime, timedelta
import hashlib
import json
import logging
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time
from types import SimpleNamespace
from unittest.mock import patch


class StageCapture(logging.Handler):
    def __init__(self):
        super().__init__()
        self.rows = []

    def emit(self, record):
        stage = getattr(record, "operation_stage", None)
        if stage:
            self.rows.append(dict(stage))


def summarize(rows):
    result = {"samples": len(rows), "median": {}, "p95": {}}
    for key in rows[0]:
        values = sorted(row[key] for row in rows)
        result["median"][key] = statistics.median(values)
        if len(values) >= 20:
            result["p95"][key] = values[max(0, (95 * len(values) + 99) // 100 - 1)]
    result["observations"] = rows
    return result


async def measure(args):
    import discord
    import pyodbc

    from mge import mge_embed_manager as boards, mge_simplified_leadership_service as leadership
    from mge.dal import mge_review_dal as review, mge_roster_dal as roster
    from mge.mge_roster_service import RosterResult
    from ui.views import mge_simplified_leadership_view as views

    capture = StageCapture()
    logging.getLogger().addHandler(capture)
    logging.getLogger().setLevel(logging.INFO)
    result = {}
    delay = args.delay_ms / 1000

    def deny(*_, **__):
        raise AssertionError("Live SQL is forbidden in this benchmark")

    # Imports above only define code. No real services/writes run below.
    with patch.object(pyodbc, "connect", deny):
        for mode, size in [("payload", n) for n in (0, 4, 15, 30)] + [
            ("rank_select", 4),
            ("rank_submit", 4),
            ("overlap", 4),
        ]:
            observations = []
            all_stages = defaultdict(list)
            for _ in range(args.samples):
                calls = Counter(
                    review_reads=0,
                    award_reads=0,
                    event_reads=0,
                    state_reads=0,
                    id_writes=0,
                    fetches=0,
                    edits=0,
                    replies=0,
                    mutations=0,
                    simulated_read_connections=0,
                )
                review_rows = [
                    dict(
                        EventId=77,
                        SignupId=i,
                        GovernorId=100 + i,
                        GovernorNameSnapshot=f"Fixture {i}",
                        RequestedCommanderId=1,
                        RequestPriority="High",
                        PreferredRankBand="1-5",
                        SignupCreatedUtc=datetime(2026, 1, 1, tzinfo=UTC),
                    )
                    for i in range(1, size + 1)
                ]
                awards = [
                    dict(
                        EventId=77,
                        SignupId=i,
                        AwardId=1000 + i,
                        GovernorId=100 + i,
                        AwardStatus="awarded" if i <= 15 else "waitlist",
                        AwardedRank=i if i <= 15 else None,
                        WaitlistOrder=None if i <= 15 else i - 15,
                        TargetScore=8000000,
                    )
                    for i in range(1, size + 1)
                ]

                def read(kind, rows):
                    calls[kind] += 1
                    calls["simulated_read_connections"] += 1
                    time.sleep(delay)
                    return deepcopy(rows)

                def identity(**_):
                    calls["id_writes"] += 1
                    time.sleep(delay)
                    return True

                event = dict(
                    EventId=77,
                    EventName="Fixture",
                    VariantName="Infantry",
                    EventMode="controlled",
                    Status="signup_open",
                    RulesText="Fixture",
                    SignupCloseUtc=datetime.now(UTC) + timedelta(days=1),
                    SignupEmbedMessageId=10,
                    SignupEmbedChannelId=1,
                )

                class Channel(discord.abc.Messageable):
                    id = 1

                    async def _get_channel(self):
                        return self

                    async def fetch_message(self, message_id):
                        calls["fetches"] += 1
                        await asyncio.sleep(delay * 3)
                        return SimpleNamespace(id=message_id, edit=self.edit)

                    async def edit(self, **_):
                        calls["edits"] += 1
                        await asyncio.sleep(delay * 3)

                channel = Channel()
                bot = SimpleNamespace(get_channel=lambda _: channel)
                started = time.perf_counter()
                ack = None
                done = False
                lag = []

                class Interaction:
                    def __init__(self):
                        self.user = SimpleNamespace(id=1, roles=[])
                        self.guild = None
                        self.client = bot
                        self.created_at = datetime.now(UTC)
                        self.acked = False
                        self.response = SimpleNamespace(
                            is_done=lambda: self.acked, defer=self.defer
                        )
                        self.followup = SimpleNamespace(send=self.send)

                    async def defer(self, **_):
                        nonlocal ack
                        await asyncio.sleep(delay)
                        self.acked = True
                        ack = time.perf_counter() - started

                    async def send(self, *_, **__):
                        calls["replies"] += 1
                        await asyncio.sleep(delay)

                def mutation(**_):
                    calls["mutations"] += 1
                    time.sleep(delay)
                    return RosterResult(True, "Rank saved")

                async def heartbeat():
                    while not done:
                        before = time.perf_counter()
                        await asyncio.sleep(0.001)
                        lag.append(max(0, time.perf_counter() - before - 0.001))

                with (
                    patch.object(review, "run_query", lambda *_: read("review_reads", review_rows)),
                    patch.object(roster, "run_query", lambda *_: read("award_reads", awards)),
                    patch.object(roster, "insert_award", deny),
                    patch.object(
                        boards, "fetch_event_for_embed", lambda _: read("event_reads", event)
                    ),
                    patch.object(
                        boards,
                        "fetch_leadership_embed_state",
                        lambda _: read("state_reads", {"message_id": 11}),
                    ),
                    patch.object(boards, "update_event_embed_ids", identity),
                    patch.object(boards, "update_leadership_embed_state", identity),
                    patch.object(
                        boards, "resolve_public_signup_channel_id", lambda: (1, 1, "fixture")
                    ),
                    patch.object(boards, "MGE_LEADERSHIP_CHANNEL_ID", 1),
                    patch.object(boards, "MGE_SIMPLIFIED_FLOW_ENABLED", True),
                    patch.object(boards, "_build_signup_view", lambda **_: None),
                    patch.object(boards, "_build_leadership_view", lambda **_: None),
                    patch.object(views, "is_admin_or_leadership_interaction", lambda _: True),
                    patch.object(views.mge_roster_service, "set_rank", mutation),
                ):
                    capture.rows.clear()
                    monitor = asyncio.create_task(heartbeat())
                    await asyncio.sleep(0)
                    started = time.perf_counter()
                    try:
                        if mode == "payload":
                            await asyncio.to_thread(leadership.get_leadership_board_payload, 77)
                        elif mode == "rank_select":
                            view = views.MGESimplifiedLeadershipView(event_id=77)
                            await view.adjust_rank.callback(Interaction())
                            view.stop()
                        else:
                            modal = views._AdjustRankModal(event_id=77, award_id=1001)
                            modal.rank_value = SimpleNamespace(value="2")
                            if mode == "overlap":
                                await asyncio.gather(
                                    modal.callback(Interaction()),
                                    boards.sync_event_leadership_embed(bot=bot, event_id=77),
                                )
                            else:
                                await modal.callback(Interaction())
                    finally:
                        elapsed = time.perf_counter() - started
                        done = True
                        await monitor
                observations.append(
                    dict(
                        total_ms=elapsed * 1000,
                        ack_ms=(ack or 0) * 1000,
                        max_loop_lag_ms=max(lag, default=0) * 1000,
                        **calls,
                    )
                )
                for row in capture.rows:
                    all_stages[row["stage"]].append(row["elapsed_ms"])
            result[f"{mode}_{size}"] = summarize(observations)
            result[f"{mode}_{size}"]["inclusive_stage_ms"] = {
                key: {
                    "count": len(values),
                    "median": statistics.median(values),
                    "p95": (
                        sorted(values)[(95 * len(values) + 99) // 100 - 1]
                        if len(values) >= 20
                        else None
                    ),
                }
                for key, values in all_stages.items()
            }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=30)
    parser.add_argument("--delay-ms", type=float, default=1)
    args = parser.parse_args()
    if args.samples < 1 or args.delay_ms < 0:
        parser.error("samples must be positive and delay nonnegative")
    sys.path.insert(0, str(args.source_root.resolve()))
    for key, value in {
        "K98_TEST_MODE": "1",
        "PYTEST_RUNNING": "1",
        "PYTHON_DOTENV_DISABLED": "1",
        "OUR_KINGDOM": "98",
        "DISCORD_BOT_TOKEN": "fixture-token",
        "SQL_SERVER": "fixture-invalid",
        "SQL_DATABASE": "fixture-invalid",
        "PREKVK_IMPORT_HISTORY_DISABLED": "1",
    }.items():
        os.environ[key] = value
    result = {
        "kind": "offline simulated IO; no production latency or native SQL claims",
        "harness_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "simulated_io_ms": args.delay_ms,
        "cases": asyncio.run(measure(args)),
    }
    result["source_revision"] = subprocess.check_output(
        ["git", "-C", str(args.source_root), "rev-parse", "HEAD"], text=True
    ).strip()
    result["source_hashes"] = {
        str(path.relative_to(args.source_root))
        .replace("\\", "/"): hashlib.sha256(path.read_bytes())
        .hexdigest()
        for directory in ("core", "mge", "ui/views")
        for path in sorted((args.source_root / directory).rglob("*.py"))
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
