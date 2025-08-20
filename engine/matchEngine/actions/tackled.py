# actions/tackled.py
from typing import Optional, Tuple
XYZ = Tuple[float, float, float]

def do_action(match, player_id: str, subtype: Optional[str], location: XYZ, target: XYZ) -> bool:
    ball = match.ball
    # Only the current carrier can be “tackled”
    if getattr(ball, "holder", None) != player_id:
        return False

    # Put ball on ground at carrier location and mark the action
    x, y, _ = location
    ball.release()
    ball.location = (x, y, 0.0)
    ball.set_action("tackled")   # → ACTION_MATRIX will enter ruck.start
    return True
