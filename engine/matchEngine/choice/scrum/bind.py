# engine/matchEngine/choice/scrum/bind.py
from typing import List
from .common import DoCall, team_possession, ScrumScore, compute_stage_2

def plan(match, state_tuple) -> List[DoCall]:
    """
    Stage 2: Bind
    - Maintain formation.
    - Accumulate score += rule 2 (stub).
    """
    calls: List[DoCall] = []
    atk = team_possession(match)

    # keep formation steady (no extra moves necessary by default)
    s = getattr(match, "_scrum_score", None) or ScrumScore()
    compute_stage_2(match, atk, s)
    match._scrum_score = s

    return calls
