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
    dt = dt * GameSpeed  # is the pace the user wants to watch game at
    accel = float(getattr(p, "accel_mps2", 4.0))
    max_speed = float(getattr(p, "max_speed_mps", 5.5))
    p.current_speed = min(
        max_speed, getattr(p, "current_speed", 0.0) + accel * dt
    )

    x, y, z = p.location
    xt, yt, zt = target
    dx, dy, dz = (xt - x), (yt - y), (zt - z)
    d2 = dx*dx + dy*dy + dz*dz
    vx, vy = dx, dy
    if vx or vy:
        # assume you've already computed/loaded normalized attributes on the player:
        agility_norm = float(getattr(p, "agility_norm", 0.5))          # 0..1
        acceleration_norm = float(getattr(p, "acceleration_norm", 0.5))# 0..1

        # compute max turn allowed this tick from speed + attrs
        max_turn_deg = max_turn_deg_per_tick_from_attrs(
            speed_mps=p.current_speed,
            dt=dt,
            agility_norm=agility_norm,
            acceleration_norm=acceleration_norm,
        )

        p.orientation_deg = compute_orientation(
            (x, y),
            (xt, yt),     # face toward the target firs                # face the direction we will move this tick
            attacking_dir=None,
            current_deg=p.orientation_deg,
            max_turn_deg_per_tick=max_turn_deg,
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
            max_turn_deg_per_tick=None,  # snap for the first set
        )

    step = p.current_speed * dt

    new_pos = (x, y, z)
    if vx or vy:
        # only move once we are facing (within a tiny tolerance)
        heading_to_target = math.degrees(math.atan2(vy, vx))
        diff = (heading_to_target - p.orientation_deg + 180.0) % 360.0 - 180.0
        if abs(diff) < 1e-3:
            if d2 <= max(step * step, (getattr(p, "arrive_radius", 0.5))**2):
                new_pos = (xt, yt, zt)
                p.current_action = "idle"
            else:
                k = step / math.sqrt(d2)
                new_pos = (x + dx * k, y + dy * k, z + dz * k)
                p.current_action = "run"
        else:
            p.current_action = "idle"
    else:
        p.current_action = "idle"

    new_pos = match.pitch.clamp_position(new_pos)
    p.update_location(new_pos)
    return True



def max_turn_deg_per_tick_from_attrs(
    speed_mps: float,
    dt: float,
    agility_norm: float,       # 0..1
    acceleration_norm: float   # 0..1
) -> float:
    # 1) Agility -> lateral acceleration (3..8 m/s^2)
    a_lat_max = 3.0 + (8.0 - 3.0) * agility_norm

    # 2) Soft floor for low-speed turning (v0 shrinks with acceleration)
    v0_min, v0_max = 0.3, 2.0
    v0 = v0_max - (v0_max - v0_min) * acceleration_norm
    v_eff = math.sqrt(speed_mps * speed_mps + v0 * v0)

    # 3) Physical limit (rad/s)
    omega_phys = a_lat_max / v_eff

    # 4) Low-speed pivot spin and smooth blend
    omega_pivot_min, omega_pivot_max = 3.0, 6.0  # rad/s
    omega_pivot = omega_pivot_min + (omega_pivot_max - omega_pivot_min) * acceleration_norm

    v_c = 2.0  # m/s, blend scale
    s = speed_mps / (speed_mps + v_c)  # 0 at rest -> ~1 at speed
    omega = (1.0 - s) * omega_pivot + s * omega_phys

    # 5) Convert to degrees per tick (and keep a safety cap)
    omega_cap = 6.0  # rad/s (~343 deg/s)
    omega = min(omega, omega_cap)

    max_turn_deg_per_tick = omega * dt * (180.0 / math.pi)
    return max_turn_deg_per_tick