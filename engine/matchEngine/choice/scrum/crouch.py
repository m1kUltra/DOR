# engine/matchEngine/choice/scrum/crouch.py
from typing import List, Tuple, Optional
from .common import DoCall, team_possession, move_pack_and_9_calls, ScrumScore, compute_stage_1

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
    calls += move_pack_and_9_calls(match, atk)

    # Score stage 1
    s = getattr(match, "_scrum_score", None) or ScrumScore()
    compute_stage_1(match, atk, s)
    match._scrum_score = s

    return calls
