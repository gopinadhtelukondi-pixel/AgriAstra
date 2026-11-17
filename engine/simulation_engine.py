"""Scenario calculations kept separate from live forecast data."""


def _rain_comparison(value, baseline):
    if value is None or baseline is None:
        return None
    difference = float(value) - float(baseline)
    if float(baseline) >= 1.0:
        return {"kind": "percent", "value": difference / float(baseline) * 100}
    return {"kind": "absolute", "value": difference}


def simulate(base_rain_mm, base_temp_c, hypothetical_rain_mm, hypothetical_temp_c,
             rainfall_baseline_mm=None, temperature_baseline_c=None):
    original_rain = _rain_comparison(base_rain_mm, rainfall_baseline_mm)
    simulated_rain = _rain_comparison(hypothetical_rain_mm, rainfall_baseline_mm)
    original_temp = (
        float(base_temp_c) - float(temperature_baseline_c)
        if base_temp_c is not None and temperature_baseline_c is not None else None
    )
    simulated_temp = (
        float(hypothetical_temp_c) - float(temperature_baseline_c)
        if hypothetical_temp_c is not None and temperature_baseline_c is not None else None
    )
    return {
        "original": {"rainfall_mm": float(base_rain_mm), "temperature_c": float(base_temp_c), "label": "forecast"},
        "simulated": {"rainfall_mm": float(hypothetical_rain_mm), "temperature_c": float(hypothetical_temp_c), "label": "hypothetical"},
        "rainfall_change_mm": float(hypothetical_rain_mm) - float(base_rain_mm),
        "temperature_change_c": float(hypothetical_temp_c) - float(base_temp_c),
        "rainfall_baseline_comparison": {"forecast": original_rain, "hypothetical": simulated_rain},
        "temperature_baseline_difference_c": {"forecast": original_temp, "hypothetical": simulated_temp},
        "crop_outcome": None,
    }

