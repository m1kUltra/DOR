from typing import Any


def _norm_attr(player: Any, key: str) -> float:
    """Return normalized attribute in 0..1 range."""
    try:
        return float(getattr(player, "norm_attributes", {}).get(key, 0.0))
    except Exception:
        return 0.0


def standing_jump(player: Any) -> float:
    """Standing jump height in meters."""
    return 0.20 + 0.40 * _norm_attr(player, "jumping_reach")


def running_jump(player: Any) -> float:
    """Running jump height in meters."""
    return standing_jump(player) + 0.12 * _norm_attr(player, "acceleration")


def lifted_jump(lifter: Any, jumper: Any) -> float:
    """Lifted jump height in meters."""
    lh = float(getattr(lifter, "height", 0.0))
    jh = float(getattr(jumper, "height", 0.0))
    return (lh / 2.0) + (jh * 1.375)


def total_vertical_reach(player: Any, jump_height: float) -> float:
    """Combine player height and jump height for total reach."""
    return float(getattr(player, "height", 0.0)) + float(jump_height)


def lateral_catch_radius(player: Any) -> float:
    """Lateral radius within which a player can attempt a catch."""
    h = float(getattr(player, "height", 0.0))
    return 1.0 + h / 0.375