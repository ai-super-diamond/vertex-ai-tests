import math
import statistics


def percentile(sorted_vals: list[float], p: float) -> float:
    """Linear interpolation percentile on a pre-sorted list (0-100)."""
    if not sorted_vals:
        raise ValueError("percentile called with empty list")
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    k = (p / 100.0) * (len(sorted_vals) - 1)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_vals[int(k)]
    d0 = sorted_vals[f] * (c - k)
    d1 = sorted_vals[c] * (k - f)
    return d0 + d1


def compute_stats(values: list[float | None]):
    """Compute mean, stdev (if n>=2), and p10/p50/p90 for numeric values.

    None values are ignored. Returns None if no valid numbers.
    """
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    vals.sort()
    mean_val = statistics.mean(vals)
    stdev_val = statistics.stdev(vals) if len(vals) >= 2 else None
    p10 = percentile(vals, 10)
    p50 = percentile(vals, 50)
    p90 = percentile(vals, 90)
    return {
        "mean": mean_val,
        "stdev": stdev_val,
        "p10": p10,
        "p50": p50,
        "p90": p90,
    }
