# matchEngine/actions/catch.py
from typing import Optional, Tuple

XYZ = Tuple[float, float, float]

def do_action(match, catcher_id: str, subtype: Optional[str], location: XYZ, target: XYZ) -> bool:
    """
    Catch sets holder and ball.status -> 'caught'.
    """
    ball = match.ball

    # set holder (your holder id format like '10a')
    ball.holder = catcher_id
    ball.set_action("caught")
    # held → Ball.update() will snap to player and clear transit
    return True
