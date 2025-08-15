from math import cos, sin, radians

from constants import (
    KICK_BASE_V0, KICK_PRESETS, LATERAL_DRIFT_MAX,
    DEADBALL_LINE_A_X, DEADBALL_LINE_B_X,
    TOUCHLINE_BOTTOM_Y, TOUCHLINE_TOP_Y,
)

GRAVITY = 9.81


def _clamp(val: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, val))


def _clamp_xy(x: float, y: float) -> tuple[float, float]:
    x = _clamp(x, DEADBALL_LINE_A_X, DEADBALL_LINE_B_X)
    y = _clamp(y, TOUCHLINE_BOTTOM_Y, TOUCHLINE_TOP_Y)
    return x, y


def _attack_dir_from_team(match, team):
    # +1 or -1 depending on team attacking direction along x
    # Fallback to +1 if not defined
    try:
        return 1 if getattr(team, "attack_dir", 1) >= 0 else -1
    except Exception:
        return 1


def compute_kick_velocity(match, kicker, kick_type: str, v0_hint: float, lateral_hint: float) -> dict:
    """
    Returns:
      {
        "vx": float, "vy": float, "vz": float,
        "type": kick_type,
        "hang_bonus": float,
        "spin": float,
        "landing_pred": (x,y,t)  # rough predicted landing
      }
    """
    preset = KICK_PRESETS.get(kick_type)
    if preset is None:
        raise ValueError(f"Unknown kick_type: {kick_type}")

    v0 = KICK_BASE_V0 * preset["v0"] * _clamp(v0_hint, 0.5, 1.4)
    elev = radians(preset["elev_deg"])
    attack_dir = _attack_dir_from_team(match, getattr(kicker, "team", None) or match.get_team(kicker))

    vx = v0 * cos(elev) * attack_dir

    # lateral drift, clamp |vy|/v0
    vy = v0 * (preset.get("drift", 0.0) + lateral_hint)
    max_vy = LATERAL_DRIFT_MAX * max(v0, 1e-6)
    if vy > max_vy:
        vy = max_vy
    elif vy < -max_vy:
        vy = -max_vy

    vz = v0 * sin(elev)

    # naive landing projection (no air)
    t_fall = (2.0 * vz) / GRAVITY if vz > 0 else 0.0
    x0, y0, _ = getattr(match.ball, "location", (0.0, 0.0, 1.5))
    x_land = x0 + vx * t_fall
    y_land = y0 + vy * t_fall

    # Clamp landing inside the field: prefer Pitch.clamp_position, else constants
    try:
        px, py, _ = match.pitch.clamp_position((x_land, y_land, 0.0))
        x_land, y_land = px, py
    except Exception:
        x_land, y_land = _clamp_xy(x_land, y_land)

    return {
        "vx": vx,
        "vy": vy,
        "vz": vz,
        "type": kick_type,
        "hang_bonus": float(preset.get("hang_bonus", 0.0)),
        "spin": float(preset.get("spin", 0.0)),
        "landing_pred": (x_land, y_land, t_fall),
    }
