from unittest.mock import patch

import pytest

from data_sources.open_meteo import get_weather


def test_forecast_uses_api_values_and_marks_freshness():
    payload = {"timezone": "Asia/Kolkata", "daily": {"time": ["2026-11-17"], "precipitation_sum": [7.5], "temperature_2m_max": [31], "temperature_2m_min": [21]}}
    with patch("data_sources.open_meteo._cached_get", return_value=(payload, {"stale": False, "fetched_at": "2026-11-17T00:00:00Z"})):
        result = get_weather({"latitude": 17.9, "longitude": 79.1, "timezone": "Asia/Kolkata"})
    assert result["daily"]["precipitation_sum"] == [7.5]
    assert result["source"] == "Open-Meteo Forecast API"
    assert result["stale"] is False


def test_forecast_missing_values_are_not_fabricated():
    with patch("data_sources.open_meteo._cached_get", return_value=({"daily": {}}, {"stale": False, "fetched_at": "now"})):
        with pytest.raises(RuntimeError, match="did not contain daily values"):
            get_weather({"latitude": 0, "longitude": 0, "timezone": "UTC"})

