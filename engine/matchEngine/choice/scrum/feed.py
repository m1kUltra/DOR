# engine/matchEngine/choice/scrum/feed.py
from typing import List
from .common import DoCall, team_possession

def plan(match, state_tuple) -> List[DoCall]:
    """
    Stage 4: Feed
    - Ball is put to tunnel; your set_pieces/scrum.py already orients the ball at the tunnel.
    - No score math here; tactic choice happens in 'drive' loop after each push tick.
    """
    calls: List[DoCall] = []
    atk = team_possession(match)

    # Scrum-half simple 'feed' action for flavor (no op coords)
    pid9 = None
    for p in match.players:
        if p.team_code == atk and getattr(p, "jersey", 0) == 9:
            pid9 = getattr(p, "pid", None) or getattr(p, "id", None)
            break
    if pid9:
        calls.append((pid9, ("feed", None), (0.0,0.0,0.0), (0.0,0.0,0.0)))

    return calls
