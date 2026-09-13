import pytest

from kvk.models.new_source_reporting import PeriodKind
from kvk.services.new_source_config_service import request_endpoint_update, validate_endpoint_order
from tests.kvk_source_fixtures import calculation_config


def test_pair_confirmation_requires_endpoint_authority_and_never_guesses_counterpart():
    from types import SimpleNamespace
    from unittest.mock import Mock

    from kvk.services.new_source_config_service import confirm_endpoint_pair

    service = Mock()
    context = SimpleNamespace(request_id=None)
    with pytest.raises(PermissionError):
        confirm_endpoint_pair(service, context, authorized=True)
    service.create.assert_not_called()
    context.request_id = "request"
    service.create.return_value = {"UpdateID": "update", "Version": 1}
    assert confirm_endpoint_pair(service, context, authorized=True) == service.create.return_value
    service.associate.assert_not_called()


@pytest.mark.parametrize("end", [1, 9])
def test_combat_endpoint_cannot_be_lower_than_start(end):
    with pytest.raises(ValueError, match="greater"):
        validate_endpoint_order(calculation_config(end_scan_id=end))


def test_pending_and_no_fight_endpoints_preserved():
    for end in (None, 10, 11, 13, 14):
        validate_endpoint_order(calculation_config(end_scan_id=end))
    validate_endpoint_order(
        calculation_config(
            end_scan_id=10, period_kind=PeriodKind.NO_FIGHT, period_key="no_fight:baseline"
        )
    )
    with pytest.raises(PermissionError):
        request_endpoint_update(None, authorized=False)
