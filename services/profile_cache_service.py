"""One owned profile refresh with short reader locks and atomic publication."""

from concurrent.futures import Future
from copy import deepcopy
from dataclasses import replace
from datetime import UTC, datetime
import json
import math
from pathlib import Path
from threading import Lock
import time

from services.cache_outcomes import PROCESS_ID, CacheOutcome


def validate_players(players):
    if not isinstance(players, dict):
        raise ValueError("profile_players_invalid")
    for key, row in players.items():
        if not isinstance(key, str) or not key.isdecimal() or not isinstance(row, dict):
            raise ValueError("profile_row_invalid")
        # KVK-only enrichment rows are part of the existing source contract.
        if "GovernorID" in row and str(row["GovernorID"]) != key:
            raise ValueError("profile_identity_mismatch")


class ProfileCacheService:
    def __init__(self):
        self._state = Lock()
        self._commit = Lock()
        self._flight = None
        self._closed = False
        self._revision = 0
        self._generation = 0
        self._players = {}
        self._loaded_at = 0.0
        self._snapshot_persistence = "not_applicable"
        self._snapshot_omitted = ()
        self._outcome = CacheOutcome("profile", "initial")

    def stats(self):
        with self._state:
            stamp, count = self._loaded_at, len(self._players)
            outcome = self._outcome
        try:
            loaded_iso = datetime.fromtimestamp(stamp, UTC).isoformat() if stamp else None
        except (OverflowError, OSError, ValueError):
            loaded_iso = None
        return {
            "count": count,
            "loaded_at_epoch": stamp,
            "loaded_at_iso": loaded_iso,
            "outcome": outcome.report(),
        }

    def snapshot(self):
        with self._state:
            players = self._players
        return deepcopy(players)

    def name_entries(self):
        """Copy only search fields from one coherent published snapshot."""
        with self._state:
            players = self._players
        # Publication/invalidation replace the dictionary; readers can project
        # this retained snapshot outside the lock without copying KVK payloads.
        return tuple(
            deepcopy((row.get("GovernorName"), row.get("GovernorID"))) for row in players.values()
        )

    def profile(self, governor_id):
        with self._state:
            value = self._players.get(str(governor_id))
        return deepcopy(value)

    def close(self):
        with self._state:
            self._closed = True

    def invalidate(self, governor_id):
        # Sync callers serialize with publication; async callers use invalidate_async.
        with self._commit:
            with self._state:
                self._revision += 1
                self._generation += 1
                self._players = {k: v for k, v in self._players.items() if k != str(governor_id)}
                self._snapshot_persistence = "unconfirmed"
                self._outcome = replace(
                    self._outcome,
                    generation=self._generation,
                    count=len(self._players),
                    availability="loaded_populated" if self._players else "unavailable",
                    verification="superseded",
                    persistence="unconfirmed",
                )

    def refresh(
        self, *, path, ttl, parse_time, build, save, force=False, fresh=False, origin="legacy"
    ):
        # An explicit post-update request waits for the entered worker, then owns
        # its own build. It never certifies a pre-update candidate as fresh.
        if fresh:
            with self._commit:
                with self._state:
                    if self._closed:
                        raise RuntimeError("profile_refresh_admission_closed")
                    self._revision += 1
        while True:
            with self._state:
                if self._closed:
                    raise RuntimeError("profile_refresh_admission_closed")
                flight = self._flight
                if flight is None:
                    flight = self._flight = Future()
                    revision = self._revision
                    previous = self._players
                    loaded_at = self._loaded_at
                    generation = self._generation
                    prior_persistence = self._snapshot_persistence
                    prior_omitted = self._snapshot_omitted
                    outcome = CacheOutcome(
                        "profile",
                        origin,
                        execution="running",
                        availability="loaded_populated" if previous else "unavailable",
                        count=len(previous),
                        source_time=loaded_at,
                        generation=generation,
                    )
                    self._outcome = outcome
                    break
            result = flight.result()
            if not fresh:
                return result
        started = time.monotonic()
        timings = []
        try:
            players, stamp, source = previous, loaded_at, "memory_reused"
            persistence, diagnostic, omitted = prior_persistence, None, prior_omitted
            execution = "succeeded"
            disk = None
            if fresh or force or not previous or time.time() - loaded_at >= ttl:
                if not fresh:
                    try:
                        disk = json.loads(Path(path).read_text(encoding="utf-8"))
                        validate_players(disk["players"])
                        stamp = parse_time(disk.get("generated_at"))
                        if not math.isfinite(stamp):
                            raise ValueError("profile_timestamp_nonfinite")
                        datetime.fromtimestamp(stamp, UTC)
                    except (OSError, OverflowError, ValueError, KeyError, TypeError):
                        disk = None
                if disk and disk["players"] and stamp and time.time() - stamp < ttl:
                    players, source = disk["players"], "disk_loaded"
                    persistence, omitted = "unchanged", ()
                else:
                    try:
                        stage = time.monotonic()
                        players, omitted = build()
                        timings.append(("build", time.monotonic() - stage))
                        stage = time.monotonic()
                        validate_players(players)
                        timings.append(("validate", time.monotonic() - stage))
                        stamp, source = time.time(), "refreshed"
                    except Exception as exc:
                        execution, diagnostic = "failed", type(exc).__name__
                        players, stamp = previous, loaded_at
                        if disk and disk["players"]:
                            players, stamp = disk["players"], parse_time(disk.get("generated_at"))
                            persistence, omitted = "unchanged", ()
                        source = "retained_last_known_good" if players else "unavailable"
            with self._commit:
                with self._state:
                    eligible = revision == self._revision
                if eligible:
                    if source == "refreshed":
                        stage = time.monotonic()
                        try:
                            save(
                                path,
                                {
                                    "generated_at": datetime.fromtimestamp(stamp, UTC).isoformat(),
                                    "players": players,
                                },
                            )
                            persistence = "saved"
                        except Exception as exc:
                            persistence, diagnostic = "failed_preserved", type(exc).__name__
                        timings.append(("persist", time.monotonic() - stage))
                    with self._state:
                        if source != "memory_reused":
                            self._generation += 1
                            self._players, self._loaded_at = players, stamp
                            self._snapshot_persistence = persistence
                            self._snapshot_omitted = tuple(omitted)
                        generation = self._generation
                else:
                    with self._state:
                        players, stamp = self._players, self._loaded_at
                        persistence, omitted = self._snapshot_persistence, self._snapshot_omitted
                    source = "retained_last_known_good" if players else "unavailable"
                outcome = replace(
                    outcome,
                    execution=execution,
                    availability=(
                        "loaded_populated"
                        if players
                        else (
                            "loaded_empty"
                            if eligible and execution == "succeeded"
                            else "unavailable"
                        )
                    ),
                    source=source,
                    persistence=persistence,
                    generation=generation,
                    verification="original_result" if eligible else "superseded",
                    count=len(players),
                    source_time=stamp,
                    diagnostic=diagnostic,
                    enrichment_omitted=tuple(omitted),
                    duration_seconds=time.monotonic() - started,
                    timings=tuple(timings),
                )
                with self._state:
                    self._outcome = outcome
            flight.set_result(outcome)
            return outcome
        except BaseException as exc:
            flight.set_exception(exc)
            raise
        finally:
            with self._state:
                self._flight = None

    def verify(self, outcome):
        with self._state:
            if (
                outcome.process_id != PROCESS_ID
                or outcome.generation != self._generation
                or outcome.verification != "original_result"
            ):
                raise ValueError("profile_result_superseded")
        if outcome.execution != "succeeded":
            raise ValueError("profile_refresh_failed")
        return outcome.report()
