# matchEngine/actions/pass_action_stripped.py

import math
from typing import Optional, Tuple

XYZ = Tuple[float, float, float]

def do_action(match, passer_id: str, subtype: Optional[str], location: XYZ, target: XYZ) -> bool:
    ball = match.ball
    if not ball.is_held():
        return False

    speed = 10 #simple for feeds

    # Mark status so the FSM can react
    ball.set_action("hook")
    ball.release()

    # Force x to 0 for both current location and target
    _, y, z = location
    _, ty, tz = target
    x = 0.0
    tx = 0.0

    # Constant pace: time = distance / speed (use yz-plane distance)
    dist = math.hypot(ty - y, tz - z)
    T = dist / speed if speed > 0 else 0.0

    # Use a "flat" trajectory (no arc) and constant timing.
    # Reuse the same API to keep it compatible with the rest of the engine.
    ball.start_parabola_to((tx, ty, 0), T=T, H=0.0, gamma=1.0)
    return True



