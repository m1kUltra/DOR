# matchEngine/actions/movement.py
from typing import Optional, Tuple
import math
from constants import DEFAULT_PLAYER_SPEED

XYZ = Tuple[float, float, float]

def _get_player(match, player_id: str):
    return match.get_player_by_code(player_id)

def _resolve_speed(subtype: Optional[str], player) -> float:
    """If subtype is a number, use it as m/s; else fallback to defaults."""
    if subtype:
        try:
            return max(0.0, float(subtype))
        except ValueError:
            pass
    # simple fallback; you can later derive from player.attributes['pace']
    return float(DEFAULT_PLAYER_SPEED)

def do_action(match, player_id: str, subtype: Optional[str], location: XYZ, target: XYZ) -> bool:
    """
    Generic movement:
      - moves player from `location` toward `target` by at most `speed * dt`
      - clamps inside pitch
      - updates orientation to face movement direction
    """
    p = _get_player(match, player_id)
    if not p:
        return False

    dt = float(getattr(match, "tick_rate", 0.05))
    speed = _resolve_speed(subtype, p)

    x, y, z = location
    xt, yt, zt = target
    dx, dy, dz = (xt - x), (yt - y), (zt - z)
    d2 = dx*dx + dy*dy + dz*dz
    step = speed * dt

    if d2 <= step * step or d2 == 0.0:
        new_pos = (xt, yt, zt)
    else:
        k = step / math.sqrt(d2)
        new_pos = (x + dx * k, y + dy * k, z + dz * k)

    # face movement direction (if any)
    if dx != 0.0 or dy != 0.0:
        p.orientation_deg = (math.degrees(math.atan2(dy, dx)) + 360.0) % 360.0

    # stay within legal bounds (dead-ball box clamp)
    new_pos = match.pitch.clamp_position(new_pos)

    p.update_location(new_pos)
    return True
