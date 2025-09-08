import math


def _clamp01(val: float) -> float:
    return max(0.0, min(1.0, float(val)))


def pass_speed(passing: float, technique: float) -> float:
    """Base pass speed in meters per second."""
    return 10.0 + 7.0 * _clamp01(passing) * _clamp01(technique)


def pass_range(passing: float, technique: float) -> float:
    """Maximum effective passing range in meters."""
    return 10.0 + 45.0 * _clamp01(passing) * _clamp01(technique)


def pass_scope(technique: float) -> float:
    """Total passing scope in radians based on technique."""
    t = _clamp01(technique)
    return math.pi + (2 * math.pi - math.pi) * t


def pass_success(distance: float, range_: float, passing: float) -> float:
    """Probability of a successful pass over `distance` meters."""
    if range_ <= 0:
        base = 0.0
    else:
        base = 1.0 - (distance / range_)
    prob = 0.1 + 0.9 * max(0.0, base) * _clamp01(passing)
    return max(0.0, min(1.0, prob))