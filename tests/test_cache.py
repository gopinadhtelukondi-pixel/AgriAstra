import json
from unittest.mock import Mock, patch

import requests

from data_sources.open_meteo import _cached_get


def test_fresh_cache_is_used_without_calling_the_network(tmp_path, monkeypatch):
    import data_sources.open_meteo as client
    monkeypatch.setattr(client, "CACHE", tmp_path)
    path = tmp_path / "fresh.json"
    path.write_text(json.dumps({"saved_epoch": 1000.0, "fetched_at": "origin", "data": {"ok": True}}))
    with patch.object(client.time, "time", return_value=1100.0), patch.object(client.SESSION, "get") as get:
        payload, freshness = _cached_get("https://example.invalid", {}, "fresh", ttl=200)
    get.assert_not_called()
    assert payload == {"ok": True}
    assert freshness["cached"] is True
    assert freshness["stale"] is False


def test_stale_cache_is_explicit_after_api_timeout(tmp_path, monkeypatch):
    import data_sources.open_meteo as client
    monkeypatch.setattr(client, "CACHE", tmp_path)
    path = tmp_path / "stale.json"
    path.write_text(json.dumps({"saved_epoch": 1000.0, "fetched_at": "origin", "data": {"ok": True}}))
    with patch.object(client.time, "time", return_value=1200.0), patch.object(client.SESSION, "get", side_effect=requests.Timeout("offline")):
        payload, freshness = _cached_get("https://example.invalid", {}, "stale", ttl=10)
    assert payload == {"ok": True}
    assert freshness["stale"] is True

