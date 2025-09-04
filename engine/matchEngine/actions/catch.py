# matchEngine/actions/catch.py
from typing import Optional, Tuple
from utils.laws import advantage as adv_law
XYZ = Tuple[float, float, float]


def do_action(match, catcher_id: str, subtype: Optional[str], location: XYZ, target: XYZ) -> bool:
    """
    subtype may hint failure: e.g. "fail", "drop"
    """
    ball = match.ball

    # failure path (keep simple: use subtype signal)
    if subtype in ("fail", "drop", "dropped", "miss"):
        ball.release()                 # ensure unheld
        ball.set_action("dropped")
             # FSM sees loose-ball
        return False

    # success path
    ball.holder = catcher_id
    ball.set_action("caught")
    x, y, _ = ball.location
    other = "b" if catcher_id.endswith("a") else "a"
    match.advantage = adv_law.start(
        match.advantage,
        type_="knock_on",
        to=other,
        start_x=x,
        start_y=y,
        start_t=match.match_time,
        reason="forced_knock_on",
    )
    return True
