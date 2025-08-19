# matchEngine/actions/kick.py
from typing import Optional, Tuple
from math import hypot, isfinite

XYZ = Tuple[float, float, float]

def _profile_for(subtype: Optional[str]) -> Tuple[float, float, float]:
    # (T, H, gamma)
    if subtype in ("bomb", "contestable"):
        return 2.2, 10.0, 1.1
    if subtype in ("grubber", "dribble"):
        return 0.6, 0.4, 1.0
    if subtype in ("exit", "long"):
        return 2.0, 8.0, 1.0
    if subtype in ("place_kick", "conversion"):
        return 1.15, 6.0, 1.0
    return 1.8, 8.0, 1.0  # default punt

def do_action(match, kicker_id: str, subtype: Optional[str], location: XYZ, target: XYZ) -> bool:
    """
    If target.z > 0: force the trajectory to pass through (tx,ty,tz) using z(s) = 4*H*s*(1-s)
    and land further along the same line. If target.z <= 0 (or omitted), keep previous behavior:
    land at (tx, ty, 0).
    """
    ball = match.ball
    if not ball.is_held():
        return False


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

    # Grubber/dribble: force to ground quickly, ignore z-constraint
    if subtype in ("grubber", "dribble"):
        ball.start_parabola_to((target[0], target[1], 0.0), T=T, H=H, gamma=gamma)
        return True

    tx = float(target[0])
    ty = float(target[1])
    tz = float(target[2] if len(target) > 2 else 0.0)

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

    ball.start_parabola_to((land_x, land_y, 0.0), T=T, H=H, gamma=gamma)
    return True
