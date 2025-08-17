# matchEngine/actions/kick.py
from typing import Optional, Tuple

XYZ = Tuple[float, float, float]

def do_action(match, kicker_id: str, subtype: Optional[str], location: XYZ, target: XYZ) -> bool:
    """
    Kicks DO change ball.status -> 'kicked'.
    Choose flight params by subtype.
    """
    ball = match.ball
    if not ball.is_held():
        return False

    # status first so status/last_status capture pre-flight location+holder
    ball.set_action("kicked")
    ball.release()

    if subtype in ("bomb", "contestable"):
        ball.start_parabola_to(target, T=2.2, H=10.0, gamma=1.1)
    elif subtype in ("grubber", "dribble"):
        # low travel, quick ground contact → short arc then skid
        ball.start_parabola_to((target[0], target[1], 0.0), T=0.6, H=0.4, gamma=1.0)
    elif subtype in ("exit", "long"):
        ball.start_parabola_to(target, T=2.0, H=8.0, gamma=1.0)
    else:
        # default punt
        ball.start_parabola_to(target, T=1.8, H=8.0, gamma=1.0)

    return True
