# tests/test_no_prints_in_cache_modules.py
# Static check to ensure cache modules don't write to stdout via print(...) calls.
# This helps prevent accidental large stdout outputs when these modules are run in a child process.

import inspect

import player_stats_cache
import target_utils
import targets_sql_cache


def module_has_print_calls(module) -> bool:
    src = inspect.getsource(module)
    return "print(" in src


def test_player_stats_cache_has_no_print():
    assert not module_has_print_calls(
        player_stats_cache
    ), "player_stats_cache still contains print()"


def test_targets_sql_cache_has_no_print():
    assert not module_has_print_calls(targets_sql_cache), "targets_sql_cache still contains print()"


def test_target_utils_has_no_print():
    assert not module_has_print_calls(target_utils), "target_utils still contains print()"
