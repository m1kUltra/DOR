# matchEngine/actions/deliver.py
"""Guaranteed catch-and-pass combo action."""

import math
from typing import Optional, Tuple

XYZ = Tuple[float, float, float]


def do_action(match, passer_id: str, subtype: Optional[str], location: XYZ, target: XYZ) -> bool:
    """Catch the ball and immediately pass to ``target``.

    This action ignores player attributes and always succeeds. It is
    primarily for flow control where a player is known to securely catch
    the ball and deliver it to a pre-defined spot without emitting
    separate catch and pass actions.
    """
    ball = match.ball

    # Snap the ball to the passer to simulate the catch
    x, y, z = location
    ball.location = (x, y, z)
    ball.holder = passer_id

    # Mark as a successful pass and release the ball again
    ball.set_action("delivered")
    ball.release()

    # Constant speed pass toward the target with a gentle arc
    tx, ty, tz = target
    speed = 20.0  # m/s constant speed
    dist = math.hypot(tx - x, ty - y)
    hang = dist / speed if speed > 0 else 0.0
    ball.start_parabola_to((tx, ty, tz), T=hang, H=1.1, gamma=1.1)
    return True