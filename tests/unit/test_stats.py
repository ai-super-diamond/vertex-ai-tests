import math

from vertex_benchmark.generate_report import compute_stats


def test_compute_stats_basic():
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    stats = compute_stats(values)
    assert stats is not None
    assert math.isclose(stats["mean"], 3.0, rel_tol=1e-9)
    # stdev of 1..5 is sqrt(2.5) ≈ 1.5811 (sample stdev)
    assert stats["stdev"] is not None
    assert math.isclose(stats["stdev"], 1.5811388301, rel_tol=1e-6)
    assert math.isclose(stats["p10"], 1.4, rel_tol=1e-9)
    assert math.isclose(stats["p50"], 3.0, rel_tol=1e-9)
    assert math.isclose(stats["p90"], 4.6, rel_tol=1e-9)


def test_compute_stats_single_value():
    values = [42.0]
    stats = compute_stats(values)
    assert stats is not None
    assert stats["mean"] == 42.0
    assert stats["stdev"] is None
    assert stats["p10"] == 42.0
    assert stats["p50"] == 42.0
    assert stats["p90"] == 42.0


def test_compute_stats_ignores_none_and_empty():
    stats_none = compute_stats([None, None])
    assert stats_none is None

    stats_some = compute_stats([None, 10.0, None, 20.0])
    assert stats_some is not None
    assert math.isclose(stats_some["mean"], 15.0, rel_tol=1e-9)
