from utils.i18n import tr


def test_crop_profile_copy_and_choices_follow_selected_language():
    labels = {
        "हिन्दी": {"Paddy": "धान", "Cotton": "कपास", "Maize": "मक्का"},
        "తెలుగు": {"Paddy": "వరి", "Cotton": "పత్తి", "Maize": "మొక్కజొన్న"},
    }
    help_text = "Growth stages update with the selected crop. Custom crops receive no inferred crop-specific thresholds."
    hero_label = "Climate intelligence for smarter farming"

    for language, examples in labels.items():
        assert tr(help_text, language) != help_text
        assert tr(hero_label, language) != hero_label
        for english, translated in examples.items():
            assert tr(english, language) == translated
