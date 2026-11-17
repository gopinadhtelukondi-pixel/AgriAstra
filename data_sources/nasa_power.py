"""Optional NASA POWER independent daily historical comparison."""
from datetime import date, datetime, timedelta, timezone

from data_sources.open_meteo import _cached_get, TTL_SECONDS


def fetch_nasa_power(location, forecast_dates, years=5):
    if not forecast_dates:
        raise ValueError("Forecast dates are required.")
    first = date.fromisoformat(forecast_dates[0])
    last_year = first.year - 1
    start = date(last_year - years + 1, 1, 1)
    end = date(last_year, 12, 31)
    params = {
        "parameters": "PRECTOTCORR,T2M_MAX,T2M_MIN",
        "community": "AG",
        "longitude": location["longitude"], "latitude": location["latitude"],
        "start": start.strftime("%Y%m%d"), "end": end.strftime("%Y%m%d"),
        "format": "JSON", "time-standard": "UTC",
    }
    key = f"nasa_power_{location['latitude']:.3f}_{location['longitude']:.3f}_{start}_{end}"
    payload, freshness = _cached_get(
        "https://power.larc.nasa.gov/api/temporal/daily/point",
        params, key, TTL_SECONDS["history"],
    )
    parameters = payload.get("properties", {}).get("parameter", {})
    if not parameters:
        raise RuntimeError("NASA POWER response did not contain requested daily parameters.")
    dates = sorted(parameters.get("PRECTOTCORR", {}).keys())
    return {
        "dates": dates,
        "precipitation_mm": [parameters.get("PRECTOTCORR", {}).get(day) for day in dates],
        "temperature_max_c": [parameters.get("T2M_MAX", {}).get(day) for day in dates],
        "temperature_min_c": [parameters.get("T2M_MIN", {}).get(day) for day in dates],
        "period": f"{start} to {end}",
        "fetched_at": freshness["fetched_at"],
        "stale": freshness["stale"],
        "cached": freshness.get("cached", False),
        "source": "NASA POWER Daily API · Agroclimatology community · UTC",
        "units": payload.get("parameters", {}),
    }

