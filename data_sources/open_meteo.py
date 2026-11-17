"""Open-Meteo geocoding, forecast, and historical archive clients."""
import hashlib
import json
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests

CACHE = Path(__file__).resolve().parents[1] / "data" / "cache"
CACHE.mkdir(parents=True, exist_ok=True)
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "AgriAstra/1.0 (climate decision support)"})
TTL_SECONDS = {"forecast": 1800, "history": 86400, "geocoding": 86400}


def _cached_get(url, params, key, ttl):
    path = CACHE / f"{key}.json"
    now = time.time()
    if path.exists():
        cached = json.loads(path.read_text(encoding="utf-8"))
        age = now - cached["saved_epoch"]
        if age <= ttl:
            return cached["data"], {
                "stale": False, "cached": True, "fetched_at": cached["fetched_at"], "age_seconds": age,
            }
    fetched_at = datetime.now(timezone.utc).isoformat()
    try:
        response = SESSION.get(url, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
        path.write_text(json.dumps({"saved_epoch": time.time(), "fetched_at": fetched_at, "data": data}), encoding="utf-8")
        return data, {"stale": False, "cached": False, "fetched_at": fetched_at}
    except (requests.RequestException, ValueError) as exc:
        if path.exists():
            cached = json.loads(path.read_text(encoding="utf-8"))
            age = time.time() - cached["saved_epoch"]
            # Permit stale display for up to 24 cache periods; always label it stale.
            if age <= ttl * 24:
                return cached["data"], {"stale": True, "cached": True, "fetched_at": cached["fetched_at"], "age_seconds": age}
        raise RuntimeError(f"Open-Meteo request failed and no usable cached response exists: {exc}") from exc


def geocode(query, country_code="IN", language="en"):
    params = {"name": query, "count": 10, "language": language, "format": "json"}
    if country_code:
        params["countryCode"] = country_code.upper()
    cache_scope = f"{query.casefold()}|{country_code or 'all'}|{language}"
    digest = hashlib.sha256(cache_scope.encode()).hexdigest()[:16]
    data, freshness = _cached_get("https://geocoding-api.open-meteo.com/v1/search", params, f"geo_{digest}", TTL_SECONDS["geocoding"])
    results = []
    for item in data.get("results", []):
        region = ", ".join(str(value) for value in (item.get("admin1"), item.get("admin2"), item.get("country")) if value)
        results.append({
            "name": item.get("name"),
            "label": f"{item.get('name')}, {region}" if region else str(item.get("name")),
            "latitude": float(item["latitude"]),
            "longitude": float(item["longitude"]),
            "timezone": item.get("timezone") or "auto",
            "country_code": item.get("country_code"),
            "geocoding_stale": freshness["stale"],
        })
    return results


def get_weather(location):
    params = {
        "latitude": location["latitude"], "longitude": location["longitude"],
        "timezone": location.get("timezone") or "auto", "forecast_days": 7,
        "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,weather_code",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,wind_speed_10m_max,weather_code",
    }
    key = f"forecast_{location['latitude']:.3f}_{location['longitude']:.3f}"
    payload, freshness = _cached_get("https://api.open-meteo.com/v1/forecast", params, key, TTL_SECONDS["forecast"])
    daily = payload.get("daily") or {}
    if not daily.get("time"):
        raise RuntimeError("Forecast response did not contain daily values.")
    return {
        "daily": daily, "fetched_at": freshness["fetched_at"],
        "current": payload.get("current", {}), "current_units": payload.get("current_units", {}),
        "daily_units": payload.get("daily_units", {}),
        "stale": freshness["stale"], "cache_age_seconds": freshness.get("age_seconds"),
        "freshness": "stale cached data" if freshness["stale"] else ("recent cache" if freshness.get("cached") else "live"),
        "timezone": payload.get("timezone", location.get("timezone", "auto")),
        "source": "Open-Meteo Forecast API",
    }


def fetch_climate(location, forecast_dates, years=5):
    if not forecast_dates:
        raise ValueError("Forecast dates are required for a comparable historical period.")
    first_day = date.fromisoformat(forecast_dates[0])
    target_month_days = {(date.fromisoformat(raw).month, date.fromisoformat(raw).day) for raw in forecast_dates}
    last_year = first_day.year - 1
    # Match each forecast calendar day over the same number of complete prior years.
    start = date(last_year - years + 1, 1, 1)
    end = date(last_year, 12, 31)
    params = {
        "latitude": location["latitude"], "longitude": location["longitude"],
        "start_date": start.isoformat(), "end_date": end.isoformat(),
        "timezone": location.get("timezone") or "auto", "models": "era5",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
    }
    key = f"history_era5_{location['latitude']:.3f}_{location['longitude']:.3f}_{start}_{end}"
    payload, freshness = _cached_get("https://archive-api.open-meteo.com/v1/archive", params, key, TTL_SECONDS["history"])
    daily = payload.get("daily") or {}
    if not daily.get("time"):
        return {"daily": {}, "period": f"{start} to {end}", "target_month_days": sorted(target_month_days),
                "stale": freshness["stale"], "fetched_at": freshness["fetched_at"], "source": "Open-Meteo Historical Archive API (ERA5)"}
    return {
        "daily": daily, "period": f"{start} to {end}", "target_month_days": sorted(target_month_days),
        "stale": freshness["stale"], "fetched_at": freshness["fetched_at"],
        "cached": freshness.get("cached", False),
        "source": "Open-Meteo Historical Archive API (ERA5)",
    }

