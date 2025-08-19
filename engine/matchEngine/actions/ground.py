# engine/matchEngine/actions/ground.py
from typing import Optional, Tuple

XYZ = Tuple[float, float, float]

def do_action(match, player_id: str, subtype: Optional[str], location: XYZ, target: Optional[XYZ]) -> bool:
    
    ball = match.ball

   
    # primary flag
    ball.set_action("grounded")

    # publish new snapshot for the FSM
    
     
    

    return True
