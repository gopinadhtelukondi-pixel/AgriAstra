from unittest.mock import patch

from data_sources.open_meteo import geocode


def test_geocode_returns_all_matches_and_regions():
    payload = {"results": [
        {"name": "Springfield", "admin1": "Illinois", "country": "United States", "latitude": 39.8, "longitude": -89.6},
        {"name": "Springfield", "admin1": "Missouri", "country": "United States", "latitude": 37.2, "longitude": -93.3},
    ]}
    with patch("data_sources.open_meteo._cached_get", return_value=(payload, {"stale": False})):
        matches = geocode("Springfield")
    assert len(matches) == 2
    assert "Illinois" in matches[0]["label"]
    assert matches[0]["latitude"] != matches[1]["latitude"]


def test_geocode_can_scope_to_india_and_return_hindi_names():
    payload = {"results": [{
        "name": "वारंगल", "admin1": "तेलंगाना", "country": "भारत",
        "country_code": "IN", "latitude": 17.97, "longitude": 79.59,
    }]}
    with patch("data_sources.open_meteo._cached_get", return_value=(payload, {"stale": False})) as request:
        matches = geocode("Warangal", country_code="IN", language="hi")
    assert len(matches) == 1
    assert matches[0]["country_code"] == "IN"
    assert "भारत" in matches[0]["label"]
    assert request.call_args.args[1]["countryCode"] == "IN"
    assert request.call_args.args[1]["language"] == "hi"

