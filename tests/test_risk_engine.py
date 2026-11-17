from engine.climate_analyzer import analyze_climate


def test_climate_analysis_does_not_invent_risk_score():
    weather = {"daily": {"time": ["2024-01-01"], "precipitation_sum": [2], "temperature_2m_max": [20], "temperature_2m_min": [10]}}
    history = {"daily": {"time": ["2023-01-01"], "precipitation_sum": [1], "temperature_2m_max": [18], "temperature_2m_min": [8]}}
    result = analyze_climate(weather, history)
    assert "risk_score" not in result
    assert result["rain_anomaly_percent"] == 100

