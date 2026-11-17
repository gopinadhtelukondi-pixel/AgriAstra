from engine.climate_analyzer import analyze_climate, compare_nasa_power


def test_comparable_calendar_baseline_and_anomalies():
    weather = {
        "source": "forecast", "fetched_at": "now", "stale": False,
        "daily": {
            "time": ["2024-01-01", "2024-01-02"],
            "precipitation_sum": [4, 4],
            "temperature_2m_max": [12, 14],
            "temperature_2m_min": [8, 10],
        },
    }
    climate = {
        "source": "ERA5", "period": "2020-2023", "fetched_at": "then", "stale": False,
        "daily": {
            "time": ["2020-01-01", "2021-01-01", "2020-01-02", "2021-01-02"],
            "precipitation_sum": [1, 3, 2, 4],
            "temperature_2m_max": [9, 11, 10, 12],
            "temperature_2m_min": [1, 3, 2, 4],
        },
    }
    result = analyze_climate(weather, climate)
    assert result["forecast_rain"] == 8
    assert result["baseline_rain"] == 5
    assert result["rain_anomaly_percent"] == 60
    assert result["forecast_temp"] == 11
    assert result["historical_temp"] == 6.5
    assert result["temp_difference_c"] == 4.5
    assert result["coverage"] == 1


def test_zero_rainfall_baseline_uses_absolute_difference():
    weather = {"daily": {"time": ["2024-01-01"], "precipitation_sum": [5], "temperature_2m_max": [20], "temperature_2m_min": [10]}}
    climate = {"daily": {"time": ["2023-01-01"], "precipitation_sum": [0], "temperature_2m_max": [15], "temperature_2m_min": [5]}}
    result = analyze_climate(weather, climate)
    assert result["rain_anomaly_percent"] is None
    assert result["rain_text"] == "+5.0 mm"


def test_incomplete_calendar_baseline_is_unavailable():
    weather = {"daily": {"time": ["2024-01-01", "2024-01-02"], "precipitation_sum": [2, 2], "temperature_2m_max": [20, 20], "temperature_2m_min": [10, 10]}}
    climate = {"daily": {"time": ["2023-01-01"], "precipitation_sum": [1], "temperature_2m_max": [15], "temperature_2m_min": [5]}}
    result = analyze_climate(weather, climate)
    assert result["baseline_rain"] is None
    assert result["rain_text"] == "Baseline unavailable"
    assert result["coverage"] == 0.5


def test_nasa_cross_check_is_separate_and_reports_coverage():
    nasa = {
        "dates": ["20200101", "20210101"], "precipitation_mm": [1, 3],
        "temperature_max_c": [10, 12], "temperature_min_c": [0, 2],
        "source": "NASA POWER", "period": "2020-2021", "fetched_at": "now",
    }
    result = compare_nasa_power(nasa, ["2024-01-01"])
    assert result["rainfall_baseline_mm"] == 2
    assert result["temperature_baseline_c"] == 6
    assert result["coverage"] == 1

