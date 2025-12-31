import pytest

from vertex_benchmark.dashboard import TRANSLATIONS


def test_translations_have_required_keys_and_languages():
    required_keys = {"title", "select_region", "batch_date", "generate_pdf"}
    # Ensure all required keys exist
    assert required_keys.issubset(TRANSLATIONS.keys())
    for key in required_keys:
        entry = TRANSLATIONS[key]
        # Both languages present and non-empty
        assert "sk" in entry and entry["sk"].strip()
        assert "en" in entry and entry["en"].strip()


def test_translations_have_no_underscores():
    offending = []
    for key, entry in TRANSLATIONS.items():
        for lang, text in entry.items():
            if "_" in text:
                offending.append((key, lang, text))
    assert offending == []
