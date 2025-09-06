# engine/matchEngine/choice/scrum/start.py
from typing import List
from .common import DoCall, team_possession, move_pack_and_9_calls
from utils.positioning.mental.formations import get_scrum_formation
def plan(match, state_tuple) -> List[DoCall]:
    """
    Scrum START:
    - Puts all forwards + 9 into correct scrum positions
    - Aligns backs 5m back
    - Kicks off the state machine by setting the ball to "scrum_crouch"
    """
    calls: List[DoCall] = []

    atk = team_possession(match)

    # Position both teams’ packs and 9s, plus backs
     # Position both teams using canonical scrum formation
    bx, by, _ = getattr(match.ball, "location", (0.0, 0.0, 0.0))
    formation = get_scrum_formation((bx, by), atk, match)
    for player, tgt in formation.items():
        pid =  getattr(player, "code", None)
        if pid:
             calls.append((pid, ("move", None), tgt, tgt))
    # Kick off crouch phase
    
   
    

    return calls