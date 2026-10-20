"""Guided decisions for a configuration import refused before its read."""

from services.configuration_continuation import ConfigurationContinuation


class ConfigurationReadContinuation(ConfigurationContinuation):
    kind = "configuration_read_continuation"
    title = "Configuration import read not started"
    initial_explanation = (
        "This configuration import could not obtain read admission. Its exact unused ticket "
        "is withdrawn; no input collection or configuration publication started. Review "
        "the original/current sources and outputs, then choose a fresh publication or keep "
        "the prior configuration. Other operations keep their own recovery and verification."
    )
