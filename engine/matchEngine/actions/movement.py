# matchEngine/actions/movement.py
from typing import Optional, Tuple
import math
from constants import GameSpeed
from utils.positioning.movement.orientation import compute_orientation  # ⬅️ NEW

XYZ = Tuple[float, float, float]

def _get_player(match, player_id: str):
    return match.get_player_by_code(player_id)



def do_action(match, player_id: str, subtype: Optional[str], location: XYZ, target: Optional[XYZ]) -> bool:
    p = _get_player(match, player_id)
    if not p:
        return False

    if target is None:
        target = p.target
        if target is None:
            return False

    p.target = tuple(target)

    dt = float(getattr(match, "tick_rate", 0.05))
    dt = dt*GameSpeed #is the pace the user wants to watch game at 
    accel = getattr(p, "accel_mps2", 4.0)
    max_speed = getattr(p, "max_speed_mps", 5.5)
    p.current_speed = min(max_speed, getattr(p, "current_speed", 0.0) + accel * dt)

    x, y, z = p.location
    xt, yt, zt = target
    dx, dy, dz = (xt - x), (yt - y), (zt - z)
    d2 = dx*dx + dy*dy + dz*dz
  
    step = p.current_speed * dt

    if d2 <= max(step * step, (getattr(p, "arrive_radius", 0.5))**2):
        new_pos = (xt, yt, zt)
        p.current_action = "idle"
    else:
        k = step / math.sqrt(d2)
        new_pos = (x + dx * k, y + dy * k, z + dz * k)
        p.current_action = "run"

    # ⬇️ FACE WHERE WE'RE ACTUALLY MOVING THIS TICK
    vx, vy = (new_pos[0] - x), (new_pos[1] - y)
    if vx or vy:
        # use the immediate next point as the "target" for orientation
        p.orientation_deg = compute_orientation(
            (x, y),
            (x + vx, y + vy),
            attacking_dir=None,                  # not needed when we have a movement vector
            current_deg=p.orientation_deg,
            max_turn_deg_per_tick=None,          # snap; set to e.g. 30.0 for smooth turning
        )
    elif p.orientation_deg is None:
        # initialize idle facing once based on team attack direction
        team = match.team_a if p.team_code == "a" else match.team_b
        atk = float((getattr(team, "tactics", {}) or {}).get("attack_dir", +1.0))
        attacking_dir = "right" if atk > 0 else "left"
        p.orientation_deg = compute_orientation(
            (x, y),
            None,
            attacking_dir=attacking_dir,
            current_deg=None,
            max_turn_deg_per_tick=None,
        )

    new_pos = match.pitch.clamp_position(new_pos)
    p.update_location(new_pos)
    return True
