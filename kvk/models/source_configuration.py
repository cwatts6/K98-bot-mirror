"""Configuration meaning, independent of import timestamps and decimal spelling."""

from decimal import Decimal

from kvk.models.new_source_reporting import fits_decimal


def weight_values(tokens):
    if len(tokens) != 3:
        raise ValueError("Exactly three player DKP weights are required.")
    values = tuple(Decimal(str(token)) for token in tokens)
    if any(not fits_decimal(value, 12) for value in values):
        raise ValueError("Player DKP weights must be exact finite decimals.")
    return values


def configuration_meaning(snapshot):
    if snapshot is None:
        return None
    return {
        "mapping": snapshot["mapping"],
        "weights": weight_values(snapshot["weights"]),
        "windows": snapshot["windows"],
    }


def weight_digest_tokens(tokens):
    # Fixed point avoids ambient Decimal context rounding and equivalent spellings.
    return [format(value, ".12f") for value in weight_values(tokens)]
