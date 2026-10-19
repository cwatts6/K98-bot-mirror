"""Read-only calculation preview; a ratio correction cannot silently alter other metrics."""

import json

from kvk.dal.new_source_import_dal import SourceConflict
from kvk.dal.new_source_publication_dal import result_digest, result_values
from kvk.services.new_source_calculation import calculate_period
from kvk.services.new_source_window_resolver import resolve_window


def preview(data, original):
    calculation = calculate_period(resolve_window(data["config"], data["observations"]), data["b0"])
    proposed = [result_values(player) for player in calculation.players]
    before = {r["GovernorID"]: r for r in original}
    if set(before) != {r["GovernorID"] for r in proposed}:
        raise SourceConflict("Calculation refresh changed the selected player cohort.")
    values_changed = states_changed = available_before = available_after = 0
    for new in proposed:
        old = before[new["GovernorID"]]
        old_states, new_states = json.loads(old["FieldStatusJson"]), json.loads(
            new["FieldStatusJson"]
        )
        if any(
            old[k] != new[k]
            for k in new
            if k != "FieldStatusJson" and not k.startswith("dkp_power_ratio")
        ) or {k: v for k, v in old_states.items() if k != "dkp_power_ratio"} != {
            k: v for k, v in new_states.items() if k != "dkp_power_ratio"
        }:
            raise SourceConflict(
                "Calculation refresh changes more than DKP/power ratios; separate review required."
            )
        values_changed += old["dkp_power_ratio"] != new["dkp_power_ratio"]
        states_changed += old_states["dkp_power_ratio"] != new_states["dkp_power_ratio"]
        available_before += old_states["dkp_power_ratio"] == "available"
        available_after += new_states["dkp_power_ratio"] == "available"
    return dict(
        calculation_version=calculation.calculation_version,
        eligible_players=len(proposed),
        ratio_values_changed=values_changed,
        ratio_states_changed=states_changed,
        ratios_available_before=available_before,
        ratios_available_after=available_after,
        other_metrics_unchanged=True,
        result_hash=result_digest(proposed).hex(),
    )
