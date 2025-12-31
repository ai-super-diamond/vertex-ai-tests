from vertex_benchmark.config import REGION_TO_CITY


def test_region_labels_have_no_underscores():
    offending = [value for value in REGION_TO_CITY.values() if "_" in value]
    assert offending == []
