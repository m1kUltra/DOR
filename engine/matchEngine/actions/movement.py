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

    # matchEngine/actions/movement.py
def do_action(match, player_id: str, subtype: Optional[str], location: XYZ, target: Optional[XYZ]) -> bool:
    p = _get_player(match, player_id)
    if not p:
        return False

    # if caller didn't pass a target, use the player's currently set intention
    if target is None:
        target = p.target
        if target is None:
            return False  # nowhere to go

    # remember intention so future ticks can keep moving without re-sending target
    p.target = tuple(target)

    dt = float(getattr(match, "tick_rate", 0.05))
    speed = _resolve_speed(subtype, p) if subtype else float(getattr(p, "speed_mps", DEFAULT_PLAYER_SPEED))

    x, y, z = p.location
    xt, yt, zt = target
    dx, dy, dz = (xt - x), (yt - y), (zt - z)
    d2 = dx*dx + dy*dy + dz*dz
    step = speed * dt

    if d2 <= max(step * step, (getattr(p, "arrive_radius", 0.5))**2):
        new_pos = (xt, yt, zt)
        p.current_action = "idle"
    else:
        k = step / math.sqrt(d2)
        new_pos = (x + dx * k, y + dy * k, z + dz * k)
        p.current_action = "run"

    if dx or dy:
        p.orientation_deg = (math.degrees(math.atan2(dy, dx)) + 360.0) % 360.0

    new_pos = match.pitch.clamp_position(new_pos)
    p.update_location(new_pos)
    return True

