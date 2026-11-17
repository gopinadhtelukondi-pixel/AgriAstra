from services import CROPS, STAGES


def test_initial_crop_catalogue_has_crop_specific_stages():
    assert {"Paddy", "Cotton", "Maize", "Chilli", "Turmeric", "Groundnut", "Soybean", "Red gram"} <= set(CROPS)
    assert STAGES["Paddy"] != STAGES["Cotton"]
    assert "Flowering" in STAGES["Cotton"]
    assert "Tasseling" in STAGES["Maize"]

