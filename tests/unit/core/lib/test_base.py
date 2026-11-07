import json
from unittest.mock import patch

import pytest

from nettacker.core.lib.base import BaseEngine


def make_row(conditions_results):
    return json.dumps({"response": {"conditions_results": conditions_results}})


@pytest.fixture
def engine():
    return BaseEngine()


@patch("nettacker.core.lib.base.find_temp_events")
def test_get_dependent_results_string_form_does_not_filter_port(mock_find, engine):
    mock_find.return_value = make_row({"content": ["1"]})

    result = engine.get_dependent_results_from_database("t", "m", "s", "a", "8080")

    assert result == [{"content": ["1"]}]
    mock_find.assert_called_once_with("t", "m", "s", "a", None)


@patch("nettacker.core.lib.base.find_temp_events")
def test_get_dependent_results_match_port_filters_by_port(mock_find, engine):
    mock_find.return_value = make_row({"content": ["1"]})

    engine.get_dependent_results_from_database(
        "t", "m", "s", {"name": "a", "match_port": True}, "8080"
    )

    mock_find.assert_called_once_with("t", "m", "s", "a", "8080")


@patch("nettacker.core.lib.base.find_temp_events")
def test_get_dependent_results_keeps_declared_order(mock_find, engine):
    rows = {"a": make_row({"id": "a"}), "b": make_row({"id": "b"})}
    mock_find.side_effect = lambda target, module, scan, name, port: rows[name]

    result = engine.get_dependent_results_from_database(
        "t", "m", "s", [{"name": "b", "match_port": True}, {"name": "a"}], "8080"
    )

    assert result == [{"id": "b"}, {"id": "a"}]
    assert [c.args[3:] for c in mock_find.call_args_list] == [("b", "8080"), ("a", None)]


@patch("nettacker.core.lib.base.time.sleep")
@patch("nettacker.core.lib.base.find_temp_events")
def test_get_dependent_results_polls_until_event_exists(mock_find, mock_sleep, engine):
    mock_find.side_effect = [[], [], make_row({"content": ["1"]})]

    result = engine.get_dependent_results_from_database("t", "m", "s", "a")

    assert result == [{"content": ["1"]}]
    assert mock_find.call_count == 3
    assert mock_sleep.call_count == 2


@patch("nettacker.core.lib.base.find_temp_events")
def test_get_dependent_results_rejects_empty_names(mock_find, engine):
    with pytest.raises(ValueError):
        engine.get_dependent_results_from_database("t", "m", "s", "a,,b")
    mock_find.assert_not_called()
