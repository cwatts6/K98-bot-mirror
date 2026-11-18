"""Offline benchmark of the real signup callback with explicitly simulated IO.

No SQL or Discord requests. Run the same harness against two source roots.
Timing describes this fixture, not production latency or a SQL query plan.
"""

import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time
from types import SimpleNamespace


async def measure(samples, delay):
    from mge import mge_signup_service
    from ui.views.mge_signup_modal import MgeSignupModalPayload
    from ui.views.mge_simplified_signup_form_view import MgeSimplifiedSignupFormView

    observations = []
    for sample in range(samples):
        started = time.perf_counter()
        calls = {"mutations": 0, "replies": 0, "refreshes": 0}
        acknowledgement = None
        done = False
        lag = []

        async def heartbeat():
            while not done:
                before = time.perf_counter()
                await asyncio.sleep(0.001)
                lag.append(max(0, time.perf_counter() - before - 0.001))

        class Response:
            acknowledged = False

            def is_done(self):
                return self.acknowledged

            async def defer(self, **kwargs):
                nonlocal acknowledgement
                acknowledgement = time.perf_counter() - started
                self.acknowledged = True

            async def send_message(self, *args, **kwargs):
                nonlocal acknowledgement
                acknowledgement = time.perf_counter() - started
                self.acknowledged = True
                calls["replies"] += 1

        async def followup(*args, **kwargs):
            calls["replies"] += 1

        def mutate(**kwargs):
            calls["mutations"] += 1
            time.sleep(delay)
            return mge_signup_service.ServiceResult(True, "Signup created.", signup_id=123)

        def refresh(event_id):
            calls["refreshes"] += 1

        mge_signup_service.create_signup = mutate
        payload = MgeSignupModalPayload(
            42, 100, "Fixture", set(), set(), on_success_refresh=refresh
        )
        view = MgeSimplifiedSignupFormView(payload=payload, commander_options={1: "Fixture"})
        view.selected_priority_rank_value = "high_1_5"
        view.selected_commander_id = 1
        interaction = SimpleNamespace(
            id=sample + 1,
            user=SimpleNamespace(id=1, roles=[]),
            guild=None,
            response=Response(),
            followup=SimpleNamespace(send=followup),
        )
        monitor = asyncio.create_task(heartbeat())
        await asyncio.sleep(0)
        started = time.perf_counter()
        await view.submit_btn.callback(interaction)
        elapsed = time.perf_counter() - started
        done = True
        await monitor
        observations.append(
            {
                "ack_ms": acknowledgement * 1000 if acknowledgement is not None else None,
                "total_ms": elapsed * 1000,
                "max_loop_lag_ms": max(lag, default=0) * 1000,
                **calls,
            }
        )
        view.stop()
    return {
        "fixture": "real simplified signup callback; simulated blocking service",
        "samples": samples,
        "simulated_service_ms": delay * 1000,
        "median": {
            key: statistics.median(row[key] for row in observations) for key in observations[0]
        },
        "p95": {
            key: sorted(row[key] for row in observations)[max(0, int(samples * 0.95) - 1)]
            for key in observations[0]
        },
        "observations": observations,
    }


async def measure_refresh(samples, delay):
    from datetime import UTC, datetime, timedelta

    import discord

    from mge import mge_embed_manager as manager, mge_simplified_flow_service

    counts = {"event_reads": 0, "roster_reads": 0, "edits": 0, "id_writes": 0}

    def event(event_id):
        counts["event_reads"] += 1
        time.sleep(delay / 4)
        return dict(
            EventId=event_id,
            SignupEmbedMessageId=10,
            Status="signup_open",
            EventMode="controlled",
            SignupCloseUtc=datetime.now(UTC) + timedelta(hours=1),
        )

    def roster(event_id):
        counts["roster_reads"] += 1
        time.sleep(delay / 4)
        return []

    def save(**kwargs):
        counts["id_writes"] += 1
        return True

    async def edit(**kwargs):
        await asyncio.sleep(delay / 2)
        counts["edits"] += 1

    class Channel(discord.abc.Messageable):
        id = 20

        async def _get_channel(self):
            return self

        async def fetch_message(self, message_id):
            return SimpleNamespace(id=message_id, edit=edit)

    channel = Channel()
    bot = SimpleNamespace(get_channel=lambda channel_id: channel)
    manager.fetch_event_for_embed = event
    manager.fetch_public_signup_names = roster
    mge_simplified_flow_service.get_public_signup_rows = roster
    manager.update_event_embed_ids = save
    manager.build_mge_signup_embed = lambda *a, **k: None
    manager._build_signup_view = lambda **k: None
    started = time.perf_counter()
    if hasattr(manager, "request_signup_refresh"):
        tasks = [
            manager.request_signup_refresh(bot=bot, event_id=42, signup_channel_id=20)
            for _ in range(samples)
        ]
    else:
        # The baseline callback dispatches one sync per request after a fixed 0.5s delay.
        # Exclude that artificial delay; exercise the exact sync implementation here.
        tasks = [
            asyncio.create_task(
                manager.sync_event_signup_embed(
                    bot=bot, event_id=42, signup_channel_id=20, is_rehydrate=True
                )
            )
            for _ in range(samples)
        ]
    results = await asyncio.gather(*tasks)
    assert all(results)
    return {
        "fixture": "real board sync; simulated SQL and Discord; same-turn burst",
        "requests": samples,
        "simulated_pass_io_ms": delay * 1000,
        "elapsed_ms": (time.perf_counter() - started) * 1000,
        **counts,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=20)
    parser.add_argument("--delay-ms", type=float, default=50)
    parser.add_argument("--mode", choices=("signup", "refresh"), default="signup")
    args = parser.parse_args()
    sys.path.insert(0, str(args.source_root.resolve()))
    for key, value in {
        "K98_TEST_MODE": "1",
        "PYTEST_RUNNING": "1",
        "OUR_KINGDOM": "98",
        "DISCORD_BOT_TOKEN": "test-token",
        "SQL_SERVER": "test-sql-server",
        "SQL_DATABASE": "test-db",
    }.items():
        os.environ[key] = value
    if args.samples < 1 or args.delay_ms < 0:
        parser.error("samples must be positive and delay nonnegative")
    measure_function = measure if args.mode == "signup" else measure_refresh
    result = asyncio.run(measure_function(args.samples, args.delay_ms / 1000))
    result["source_revision"] = subprocess.check_output(
        ["git", "-C", str(args.source_root.resolve()), "rev-parse", "HEAD"], text=True
    ).strip()
    result["source_hashes"] = {
        name: hashlib.sha256((args.source_root / name).read_bytes()).hexdigest()
        for name in ("ui/views/mge_simplified_signup_form_view.py", "mge/mge_embed_manager.py")
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
