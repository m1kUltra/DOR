# matchEngine/actions/catch.py
from typing import Optional, Tuple

XYZ = Tuple[float, float, float]


def do_action(match, receiver_id: str, subtype: Optional[str], location: XYZ, target: XYZ) -> bool:
    """
    subtype may hint failure: e.g. "fail", "drop"
    """
    ball = match.ball



    # success path
    ball.holder = receiver_id
    ball.set_action("picked")
    return True
