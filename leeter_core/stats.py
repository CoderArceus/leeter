# leeter_core/stats.py
"""Pure statistical helpers – no CLI/renderer dependencies.

Moved from cli/bench.py so that both leeter_core and the thin CLI wrapper
can use them without circular imports.
"""

import math


def calculate_stats(times: list) -> dict:
    """Compute mean, median, p95, p99, and stddev from a list of
    nanosecond timing samples.

    Returns a dict with keys: mean_ns, median_ns, p95_ns, p99_ns, stddev_ns.
    The input list is sorted in-place as a side-effect (matches the original
    cli/bench.py behaviour).

    If *times* is empty, returns zeroed-out stats to avoid ZeroDivisionError.
    """
    if not times:
        return {
            "mean_ns": 0.0,
            "median_ns": 0,
            "p95_ns": 0,
            "p99_ns": 0,
            "stddev_ns": 0.0,
        }

    n = len(times)
    times.sort()
    mean = sum(times) / n
    median = times[n // 2]
    p95 = times[min(int(n * 0.95), n - 1)]
    p99 = times[min(int(n * 0.99), n - 1)]
    variance = sum((x - mean) ** 2 for x in times) / n
    stddev = math.sqrt(variance)
    return {
        "mean_ns": mean,
        "median_ns": median,
        "p95_ns": p95,
        "p99_ns": p99,
        "stddev_ns": stddev,
    }
