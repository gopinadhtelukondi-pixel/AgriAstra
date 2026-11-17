"""Numerical, transparent comparisons between forecast and historical data."""
from datetime import date, datetime
import math


def _valid(values):
    return [number for value in values if value is not None for number in [float(value)] if math.isfinite(number)]


def analyze_climate(weather, climate):
    daily = weather.get("daily") or {}
    forecast_dates = daily.get("time") or []
    raw_rain = daily.get("precipitation_sum") or []
    raw_max = daily.get("temperature_2m_max") or []
    raw_min = daily.get("temperature_2m_min") or []
    rain_values = _valid(raw_rain)
    paired_temps = [
        (float(high) + float(low)) / 2
        for high, low in zip(raw_max, raw_min)
        if high is not None and low is not None and math.isfinite(float(high)) and math.isfinite(float(low))
    ]
    complete_days = len(forecast_dates) > 0 and len(rain_values) == len(forecast_dates)
    forecast_rain = sum(rain_values) if complete_days else None
    forecast_temp = sum(paired_temps) / len(paired_temps) if len(paired_temps) == len(forecast_dates) and forecast_dates else None

    historical = (climate or {}).get("daily") or {}
    hist_dates = historical.get("time") or []
    hist_rain = historical.get("precipitation_sum") or []
    hist_max = historical.get("temperature_2m_max") or []
    hist_min = historical.get("temperature_2m_min") or []
    target_days = {(date.fromisoformat(raw).month, date.fromisoformat(raw).day) for raw in forecast_dates}
    rain_by_day = {day: [] for day in target_days}
    temp_by_day = {day: [] for day in target_days}
    for index, raw in enumerate(hist_dates):
        day = date.fromisoformat(raw)
        key = (day.month, day.day)
        if key not in target_days:
            continue
        if index < len(hist_rain) and hist_rain[index] is not None and math.isfinite(float(hist_rain[index])):
            rain_by_day[key].append(float(hist_rain[index]))
        if (index < len(hist_max) and index < len(hist_min) and hist_max[index] is not None
                and hist_min[index] is not None and math.isfinite(float(hist_max[index]))
                and math.isfinite(float(hist_min[index]))):
            temp_by_day[key].append((float(hist_max[index]) + float(hist_min[index])) / 2)

    rain_daily_baselines = [sum(values) / len(values) for values in rain_by_day.values() if values]
    temp_daily_baselines = [sum(values) / len(values) for values in temp_by_day.values() if values]
    baseline_rain = sum(rain_daily_baselines) if len(rain_daily_baselines) == len(target_days) and target_days else None
    baseline_temp = sum(temp_daily_baselines) / len(temp_daily_baselines) if len(temp_daily_baselines) == len(target_days) and target_days else None

    if forecast_rain is None:
        rain_text = "Unavailable"
        rain_difference_mm = None
        rain_anomaly_percent = None
    elif baseline_rain is None:
        rain_text = "Baseline unavailable"
        rain_difference_mm = None
        rain_anomaly_percent = None
    else:
        rain_difference_mm = forecast_rain - baseline_rain
        rain_anomaly_percent = ((forecast_rain - baseline_rain) / baseline_rain * 100) if baseline_rain >= 1 else None
        rain_text = f"{rain_anomaly_percent:+.0f}%" if rain_anomaly_percent is not None else f"{rain_difference_mm:+.1f} mm"

    temp_difference = forecast_temp - baseline_temp if forecast_temp is not None and baseline_temp is not None else None
    temp_text = f"{temp_difference:+.1f} °C" if temp_difference is not None else "Baseline unavailable"
    observed_day_count = len(rain_daily_baselines)
    coverage = observed_day_count / len(target_days) if target_days else 0
    caveat = (
        "Historical baseline is ERA5 reanalysis, not a ground-station measurement. "
        f"Comparable calendar-day coverage: {observed_day_count}/{len(target_days)} days. "
        "Forecast and reanalysis use different model products."
    )
    return {
        "forecast_rain": forecast_rain,
        "forecast_temp": forecast_temp,
        "baseline_rain": baseline_rain,
        "rain_difference_mm": rain_difference_mm,
        "rain_anomaly_percent": rain_anomaly_percent,
        "rain_text": rain_text,
        "baseline_text": f"ERA5 comparable-period baseline: {baseline_rain:.1f} mm" if baseline_rain is not None else "No complete comparable baseline",
        "historical_temp": baseline_temp,
        "temp_difference_c": temp_difference,
        "temp_text": temp_text,
        "coverage": coverage,
        "caveat": caveat,
        "forecast_days_available": len(rain_values),
        "historical_days_available": observed_day_count,
        "forecast_source": weather.get("source"),
        "history_source": (climate or {}).get("source"),
        "history_period": (climate or {}).get("period"),
        "weather_fetched_at": weather.get("fetched_at"),
        "history_fetched_at": (climate or {}).get("fetched_at"),
        "forecast_stale": weather.get("stale", False),
        "history_stale": (climate or {}).get("stale", False),
    }


def compare_nasa_power(nasa, forecast_dates):
    """Return a separate comparable baseline; never merges NASA and ERA5 values."""
    wanted = {(date.fromisoformat(raw).month, date.fromisoformat(raw).day) for raw in forecast_dates}
    rain = {}
    temp = {}
    for i, raw in enumerate(nasa.get("dates", [])):
        day = datetime.strptime(raw, "%Y%m%d").date()
        key = (day.month, day.day)
        if key not in wanted:
            continue
        r = nasa["precipitation_mm"][i]
        hi, lo = nasa["temperature_max_c"][i], nasa["temperature_min_c"][i]
        if r is not None and float(r) > -900:
            rain.setdefault(key, []).append(float(r))
        if hi is not None and lo is not None and float(hi) > -900 and float(lo) > -900:
            temp.setdefault(key, []).append((float(hi) + float(lo)) / 2)
    rain_days = [sum(values) / len(values) for values in rain.values() if values]
    temp_days = [sum(values) / len(values) for values in temp.values() if values]
    complete = len(rain_days) == len(wanted) and len(temp_days) == len(wanted) and bool(wanted)
    return {
        "rainfall_baseline_mm": sum(rain_days) if len(rain_days) == len(wanted) and wanted else None,
        "temperature_baseline_c": sum(temp_days) / len(temp_days) if len(temp_days) == len(wanted) and wanted else None,
        "coverage": len(rain_days) / len(wanted) if wanted else 0,
        "complete": complete,
        "source": nasa.get("source"),
        "period": nasa.get("period"),
        "fetched_at": nasa.get("fetched_at"),
        "stale": nasa.get("stale", False),
    }

