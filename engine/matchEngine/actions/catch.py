# matchEngine/actions/catch.py
from typing import Optional, Tuple

XYZ = Tuple[float, float, float]


def do_action(match, catcher_id: str, subtype: Optional[str], location: XYZ, target: XYZ) -> bool:
    """
    subtype may hint failure: e.g. "fail", "drop"
    """
    ball = match.ball

    # failure path (keep simple: use subtype signal)
    if subtype in ("fail", "drop", "dropped", "miss"):
        ball.release()                 # ensure unheld
        ball.set_action("dropped")     # FSM sees loose-ball
        return False

    # success path
    ball.holder = catcher_id
    ball.set_action("caught")
    return True
