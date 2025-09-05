# engine/matchEngine/choice/scrum/start.py
from typing import List
from .common import DoCall, team_possession, move_pack_and_9_calls

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
    calls += move_pack_and_9_calls(match, atk)

    # Kick off crouch phase
    match.ball.holder = None
    bx, by, _ = getattr(match.ball, "location", (0.0, 0.0, 0.0))
    match.ball.location = (bx, by, 0.0)
    match.ball.set_action("scrum_crouch")

    return calls