# engine/matchEngine/choice/scrum/set.py
from typing import List
from .common import DoCall, team_possession, ScrumScore, compute_stage_3, outcome_from_score

def plan(match, state_tuple) -> List[DoCall]:
    """
    Stage 3: Set
    - Accumulate score += rule 3 (stub) and maybe lock_out (50%).
    - If lock_out: push ball to 8's feet and finish immediately -> will go to 'stable' then 'out'.
    - If score breaches +/-1, mark penalty side (for referee layer to consume).
    """
    calls: List[DoCall] = []
    atk = team_possession(match)
    s = getattr(match, "_scrum_score", None) or ScrumScore()

    compute_stage_3(match, atk, s)
    match._scrum_score = s

    outcome = outcome_from_score(s.value)
    if outcome:
        match._scrum_outcome = outcome
        return calls

   
    return calls
