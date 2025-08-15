# matchEngine/utils/orientation.py
from __future__ import annotations
from math import atan2, degrees, isfinite

def normalize_deg(a: float) -> float:
    """Wrap any angle to [0, 360)."""
    a = a % 360.0
    return a if a >= 0 else a + 360.0

def angle_diff_deg(a: float, b: float) -> float:
    """Signed smallest difference a->b in (-180, 180]."""
    d = (b - a + 180.0) % 360.0 - 180.0
    return 180.0 if d == -180.0 else d

def bearing_deg(from_xy: tuple[float, float], to_xy: tuple[float, float]) -> float | None:
    """
    Bearing in field coords (x:0..100, y:0..70).
    Convention: 0° along +x, 90° along +y.
    Returns None if points are identical.
    """
    fx, fy = from_xy
    tx, ty = to_xy
    dx, dy = tx - fx, ty - fy
    if dx == 0.0 and dy == 0.0:
        return None
    return normalize_deg(degrees(atan2(dy, dx)))

def default_facing_for_team(attacking_dir: str | None) -> float:
    """
    Per your spec:
      attacking right -> 90°
      attacking left  -> 270°
    (Adjust here if your field axes differ.)
    """
    if attacking_dir == "right":
        return 90.0
    if attacking_dir == "left":
        return 270.0
    return 90.0  # safe default

def compute_orientation(
    pos_xy: tuple[float, float],
    target_xy: tuple[float, float] | None,
    attacking_dir: str | None,
    *,
    current_deg: float | None = None,
    max_turn_deg_per_tick: float | None = None,  # None or 9999 => snap instantly
) -> float:
    """
    Decide orientation for this tick.

    Priority:
      1) If target exists and != pos -> face target bearing.
      2) Else -> face team default (90/270 by attacking_dir).

    If max_turn_deg_per_tick is set (e.g., 25.0), rotation is clamped per tick.
    """
    desired = bearing_deg(pos_xy, target_xy) if target_xy is not None else None
    if desired is None or not isfinite(desired):
        desired = default_facing_for_team(attacking_dir)

    if (
        max_turn_deg_per_tick is not None
        and current_deg is not None
        and max_turn_deg_per_tick < 9999
    ):
        delta = angle_diff_deg(current_deg, desired)
        if abs(delta) > max_turn_deg_per_tick:
            step = max_turn_deg_per_tick if delta > 0 else -max_turn_deg_per_tick
            return normalize_deg(current_deg + step)

    return normalize_deg(desired)
