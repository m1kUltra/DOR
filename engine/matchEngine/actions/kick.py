from typing import Optional, Tuple
from math import hypot, isfinite, cos, sin, tau
import random

XYZ = Tuple[float, float, float]

def _profile_for(subtype: Optional[str]) -> Tuple[float, float, float]:
    # (T, H, gamma)
    """Return (speed, apex height, gamma) profile for the kick subtype."""
    if subtype in ("bomb", "contestable"):
        
        return 23.0, 10.0, 1.1
    if subtype in ("grubber", "dribble"):
        
        return 15.0, 0.4, 1.0
    if subtype in ("exit", "long"):
        
        return 30.0, 8.0, 1.0
    if subtype in ("place_kick", "conversion"):
      
    
        return 30.0, 6.0, 1.0
    return 26.0, 8.0, 1.0  # default punt


def calculate_kick_success(kicker, subtype: Optional[str], location: XYZ, target: XYZ) -> Tuple[float, float, float]:
    """Compute kick success probability and distances."""
    norms = getattr(kicker, "norm_attributes", {}) or {}
    power = float(norms.get("kicking_power", 0.0))

    dx = float(target[0] - location[0])
    dy = float(target[1] - location[1])
    distance_m = hypot(dx, dy)

    subtype = subtype or ""
    if subtype in ("conversion", "place_kick"):
        range_m = 25.0 + 50.0 * power
        modifier = float(norms.get("goal_kicking", 0.0))
    elif subtype == "drop_goal":
        range_m = 15.0 + 45.0 * power
        modifier = float(norms.get("goal_kicking", 0.0))
    else:
        range_m = 28.0 + 44.0 * power
        modifier = float(norms.get("kicking", 0.0))

    if range_m <= 0:
        success = 0.0
    else:
        ratio = distance_m / range_m
        success = 0.1 + 0.9 * ((1 - ratio ** 2) * (1 + modifier))

    success = max(0.0, min(1.0, success))
    return success, range_m, distance_m


def do_action(match, kicker_id: str, subtype: Optional[str], location: XYZ, target: XYZ) -> bool:
    """
    If target.z > 0: force the trajectory to pass through (tx,ty,tz) using z(s) = 4*H*s*(1-s)
    and land further along the same line. If target.z <= 0 (or omitted), keep previous behavior:
    land at (tx, ty, 0).
    """
    ball = match.ball
    if not ball.is_held():
        return False

    kicker = match.get_player_by_code(kicker_id)
    success, range_m, distance_m = calculate_kick_success(kicker, subtype, location, target)
    ball.kick_success = success
    ball.kick_range_m = range_m
    ball.kick_distance_m = distance_m

    if subtype == "conversion":
        ball.set_action("conversion")
    # mark and release
    else :  ball.set_action("kicked")
    
    
    ball.release()

    # safety nudge to avoid instant self-catch
    try:
        sx, sy, sz = ball.location
    except Exception:
        sx, sy, sz = location
    ux = 1.0 if (target[0] - sx) >= 0 else -1.0
    ball.location = (sx + 0.30 * ux, sy, max(sz, 0.20))
    sx, sy, sz = ball.location

    # profile params
    T, H, gamma = _profile_for(subtype)
    speed, H, gamma = _profile_for(subtype)
    tx = float(target[0])
    ty = float(target[1])
    tz = float(target[2] if len(target) > 2 else 0.0)

    dist_xy = hypot(tx - sx, ty - sy)
    T = dist_xy / max(speed, 1e-6)

    # Grubber/dribble: force to ground quickly, ignore z-constraint
    if subtype in ("grubber", "dribble"):
        ball.start_parabola_to((target[0], target[1], 0.0), T=T, H=H, gamma=gamma)
        ball.start_parabola_to((tx, ty, 0.0), T=T, H=H, gamma=gamma)
        return True

    tx = float(target[0])
    ty = float(target[1])
    tz = float(target[2] if len(target) > 2 else 0.0)
     # compute kick success and potential deviation
    kicker = match.get_player_by_code(kicker_id)
    kicking = float(getattr(kicker, "norm_attributes", {}).get("kicking", 0.0)) if kicker else 0.0
    power = float(getattr(kicker, "norm_attributes", {}).get("kicking_power", 0.0)) if kicker else 0.0
    x0, y0, _ = location
    distance_m = hypot(tx - x0, ty - y0)
    range_m = 28.0 + 44.0 * power
    kick_success = 0.1 + 0.9 * ((1.0 - (distance_m / max(range_m, 1e-6)) ** 2) * (1.0 + kicking))
    kick_success = max(0.0, min(1.0, kick_success))
    rnd = random.random()
    if rnd > kick_success:
        error = rnd - kick_success
        if random.random() < 0.5:
            error = -error
        misplaced = error * distance_m
        if abs(error) < 0.2:
            ty += misplaced
        elif abs(error) <= 0.75:
            tx += misplaced
            ty += misplaced
        
    # --- Case 1: old behavior for z<=0 ---
    if tz <= 0.0:
        ball.start_parabola_to((tx, ty, 0.0), T=T, H=H, gamma=gamma)
        return True

    # --- Case 2: intersect (tx,ty,tz) then continue to landing ---
    # Direction and distance start -> target in XY
    vx, vy = tx - sx, ty - sy
    at = hypot(vx, vy)
    if at < 1e-6:
        # degenerate: define any direction forward
        vx, vy, at = ux, 0.0, 1.0
    dirx, diry = vx / at, vy / at

    # Choose H and s* so that z(s*) == tz on z(s)=4*H*s*(1-s)
    if tz > H:
        # raise apex to match the required height and set target at apex
        H = tz
        s_star = 0.5
    else:
        # ascending branch solution: s = (1 - sqrt(1 - tz/H)) / 2
        root = 1.0 - tz / max(H, 1e-9)
        root = max(0.0, min(1.0, root))
        s_star = (1.0 - root**0.5) / 2.0
        s_star = max(0.05, min(0.95, s_star))  # numeric guardrails

    denom = max(s_star, 1e-9)
    total_xy = at / denom            # |S->L| so that |S->T|/|S->L| = s*
    extra = max(0.0, total_xy - at)  # distance beyond the target along the same line

    land_x = tx + dirx * extra
    land_y = ty + diry * extra

    # final safety: bad numerics fallback
    if not all(map(isfinite, (land_x, land_y))):
        land_x, land_y = tx + dirx, ty + diry  # minimal 1m fallback

    total_xy = hypot(land_x - sx, land_y - sy)
    T = total_xy / max(speed, 1e-6)

    ball.start_parabola_to((land_x, land_y, 0.0), T=T, H=H, gamma=gamma)
    return True
def slice_kick(location: XYZ, range_m: float) -> tuple[XYZ, float]:
    """Return a random target within ``range_m/3`` and a high-arc gamma."""
    sx, sy, _ = location
    radius = max(range_m, 0.0) / 3.0
    ang = random.random() * tau
    dist = random.random() * radius
    x = sx + cos(ang) * dist
    y = sy + sin(ang) * dist
    # gamma > 85° -> use a large curvature factor
    return (x, y, 0.0), 1.7