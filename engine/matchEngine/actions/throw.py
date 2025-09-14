
"""Throw action for lineouts or restarts."""

from typing import Optional, Tuple
import math

XYZ = Tuple[float, float, float]



def do_action(
    match,
    passer_id: str,
    subtype: Optional[str],
    location: XYZ,
    target: XYZ,
) -> bool:
    ball = match.ball
    if not ball.is_held():
        return False
    if getattr(ball, "holder", None) != passer_id:
        return False
    if target is None:
        return False

   
    
    x, y, z = location
    tx, ty, tz = target

    dist = math.hypot(tx - x, ty - y)
   


    speed = 26
    hang = dist / speed if speed > 0 else 0.0

    # mark status so the FSM can pick it up via ActionMatrix ("in_a_tackle" -> "offloaded")
    # mark status and release the ball
    ball.set_action("thrown")
    ball.release()

    # ensure starting point is correct and clear holder
    ball.location = (x, y, 1)

    # launch a simple arc toward the target
    ball.start_parabola_to((tx, ty, tz), T=hang, H=1.0, gamma=1.0)
    return True


 