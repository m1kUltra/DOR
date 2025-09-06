# matchEngine/actions/feed.py

import math
from typing import Optional, Tuple

XYZ = Tuple[float, float, float]

def do_action(match, passer_id: str, subtype: Optional[str], location: XYZ, target: XYZ) -> bool:
    ball = match.ball
    bx, by, _ = ball.location
    hx, hy, _ = location
    if math.hypot(bx - hx, by - hy) > 0.75:
        return False

    speed = 10.0  # units per second

    # Mark status so the FSM can react
    ball.set_action("hook")
    ball.release()

    # Preserve x/y; lock z to 0 for start and end
    x0, y0, _ = location
    x1, y1, _ = target
    start = (x0, y0, 0.0)
    end   = (x1, y1, 0.0)

    # (Optional) snap the ball exactly to start if your engine needs it


    # Time from full XY distance to keep constant pace
    dx = x1 - x0
    dy = y1 - y0
    dist_xy = math.hypot(dx, dy)
    T = max(dist_xy / speed, 1e-3)  # avoid zero-duration issues

    # Flat path (H=0), linear timing (gamma=1.0), no vertical drift
    ball.start_parabola_to(end, T=T, H=0.0, gamma=1.0)
    return True
