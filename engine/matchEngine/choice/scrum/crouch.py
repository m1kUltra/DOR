# engine/matchEngine/choice/scrum/crouch.py
from typing import List, Tuple, Optional
from .common import DoCall, team_possession,  ScrumScore, compute_stage_1
from utils.positioning.mental.formations import get_scrum_formation
def plan(match, state_tuple) -> List[DoCall]:
    """
    Stage 1: Crouch
    - Position packs and 9.
    - Accumulate score per rule 1 (stub).
    - No penalties yet (just staging).
    """
    calls: List[DoCall] = []
    atk = team_possession(match)

    # Ensure formation
    # Ensure formation using canonical scrum template
    bx, by, _ = getattr(match.ball, "location", (0.0, 0.0, 0.0))
    formation = get_scrum_formation((bx, by), atk, match)
    for player, tgt in formation.items():
        pid = getattr(player, "pid", None) or getattr(player, "id", None) or getattr(player, "code", None)
        if pid:
            calls.append((pid, ("move", None), tgt, tgt))
    # Score stage 1
    s = getattr(match, "_scrum_score", None) or ScrumScore()
    compute_stage_1(match, atk, s)
    match._scrum_score = s

    return calls
