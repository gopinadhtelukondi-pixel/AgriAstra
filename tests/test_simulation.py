from engine.simulation_engine import simulate


def test_simulation_is_explicitly_hypothetical_and_does_not_predict_crop_outcome():
    result = simulate(20, 30, 50, 35, rainfall_baseline_mm=10, temperature_baseline_c=25)
    assert result["rainfall_change_mm"] == 30
    assert result["temperature_change_c"] == 5
    assert result["simulated"]["label"] == "hypothetical"
    assert result["crop_outcome"] is None
    assert result["rainfall_baseline_comparison"]["forecast"]["value"] == 100
    assert result["rainfall_baseline_comparison"]["hypothetical"]["value"] == 400
    assert result["temperature_baseline_difference_c"] == {"forecast": 5, "hypothetical": 10}


def test_small_rainfall_baseline_uses_absolute_amounts():
    result = simulate(0.5, 20, 2, 22, rainfall_baseline_mm=0.5)
    assert result["rainfall_baseline_comparison"]["forecast"] == {"kind": "absolute", "value": 0}
    assert result["rainfall_baseline_comparison"]["hypothetical"] == {"kind": "absolute", "value": 1.5}

