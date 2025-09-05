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

    # Penalty detection gate (up to referee / advantage system)
    outcome = outcome_from_score(s.value)
    if outcome:
        match._scrum_outcome = outcome  # 'pen_feed' or 'pen_def'

    # Lock-out shortcut: ball goes quickly to 8 and we're effectively stable.
    if s.lock_out:
        match.ball.set_action("scrum_stable")  # your handler will pick it up
        # Optional: hint 8 to 'control_ball' at feet (no move, just an action suggestion)
        pid8 = None
        for p in match.players:
            if p.team_code == atk and getattr(p, "jersey", 0) == 8:
                pid8 = getattr(p, "pid", None) or getattr(p, "id", None)
                break
        if pid8:
            calls.append((pid8, ("set_behavior", "control_at_feet"), (0.0,0.0,0.0), (0.0,0.0,0.0)))

    return calls
