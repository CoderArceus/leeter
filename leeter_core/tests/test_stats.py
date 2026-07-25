import math
from leeter_core.stats import calculate_stats

def test_calculate_stats():
    times = [100, 200, 300, 400, 500]
    stats = calculate_stats(times)
    assert stats["mean_ns"] == 300.0
    assert stats["median_ns"] == 300
    assert stats["p95_ns"] == 500
    assert stats["p99_ns"] == 500
    assert math.isclose(stats["stddev_ns"], 141.4213562373095)
