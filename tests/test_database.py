from datetime import date

import database


def fixture_records():
    location = {"label": "Example, Region", "latitude": 1.0, "longitude": 2.0}
    profile = {"crop": "Paddy", "stage": "Flowering", "language": "English"}
    weather = {"source": "Open-Meteo", "fetched_at": "now", "stale": False, "daily": {
        "time": ["2026-01-01"], "precipitation_sum": [1], "temperature_2m_min": [10], "temperature_2m_max": [20],
    }}
    analysis = {"forecast_rain": 1, "forecast_temp": 15, "rain_text": "Unavailable", "temp_text": "Unavailable", "baseline_text": "No baseline"}
    return location, profile, weather, analysis


def test_assessment_advisory_and_simulation_history(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB", tmp_path / "test.sqlite")
    database.init_db()
    location, profile, weather, analysis = fixture_records()
    database.register_user("user-a", "a@example.test", "Farmer A")
    database.save_assessment("user-a", location, profile, weather, analysis)
    database.save_crop_profile("user-a", "Paddy profile", {**profile, "sowing": date(2026, 6, 1)})
    saved = database.saved_crop_profiles("user-a")[0]
    loaded = database.get_crop_profile("user-a", saved["profile_id"])
    assert loaded["sowing"] == date(2026, 6, 1)
    database.save_advisory("user-a", location, profile, "question", "answer", ["source"])
    database.save_simulation("user-a", location, profile, 1, 15, 5, 20)
    result = database.history_frame("user-a")
    assert len(result) == 3
    assert set(result["type"]) == {"Assessment", "AI advisory", "Simulation (hypothetical)"}
    assert "question" in result.columns


def test_records_and_saved_profiles_are_isolated_by_authenticated_subject(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB", tmp_path / "isolation.sqlite")
    database.init_db()
    location, profile, weather, analysis = fixture_records()

    for user_id in ("user-a", "user-b"):
        database.save_assessment(user_id, location, profile, weather, analysis)
        database.save_crop_profile(user_id, f"{user_id} crop", profile)
        database.save_advisory(user_id, location, profile, "q", f"answer for {user_id}", [])
        database.save_simulation(user_id, location, profile, 1, 15, 2, 16)

    assert [row["profile_name"] for row in database.saved_crop_profiles("user-a")] == ["user-a crop"]
    foreign_profile = database.saved_crop_profiles("user-b")[0]
    assert database.get_crop_profile("user-a", foreign_profile["profile_id"]) is None
    history_a = database.history_frame("user-a")
    assert len(history_a) == 3
    assert set(history_a["response"].dropna()) == {"answer for user-a"}
    assert "answer for user-b" not in set(history_a["response"].dropna())
