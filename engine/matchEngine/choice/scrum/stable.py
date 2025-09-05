# engine/matchEngine/choice/scrum/stable.py
from typing import List
from .common import DoCall, team_possession, ScrumScore, counter_shove_check

def plan(match, state_tuple) -> List[DoCall]:
    """
    Stage 6: Stable
    - Ball is controllable at 8's feet; 9 can pass or 8 can pick.
    - Single counter-shove opportunity by opposition to try force 'scrum_on' again.
    - Only feeding team can end the scrum (transition will be done in out.py via pass/pick).
    """
    calls: List[DoCall] = []
   

    # Otherwise remain stable; 9/8 will decide next (handled in out.py)
    return calls
