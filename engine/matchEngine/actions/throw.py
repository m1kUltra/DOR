# matchEngine/actions/offload.py
from typing import Optional, Tuple
import math

XYZ = Tuple[float, float, float]
MAX_OFFLOAD_RANGE = 10.0  # meters

def do_action(match, passer_id: str, subtype: Optional[str], location: XYZ, target: XYZ) -> bool:
    ball = match.ball
    if not ball.is_held():
        return False
    if getattr(ball, "holder", None) != passer_id:
        return False
    if target is None:
        return False

    # range gate: offloads must be short
    x, y, _  = location
    tx, ty, _ = target
    

    speed = 26 #constant for now introduce arc later

    # mark status so the FSM can pick it up via ActionMatrix ("in_a_tackle" -> "offloaded")
    ball.set_action("thrown")

    
def _speed_for(subtype: Optional[str]) -> float:
    # mirror your pass speeds; tweak if you like
    if subtype == None:
        return 16.0
    else:
        return 16.0
