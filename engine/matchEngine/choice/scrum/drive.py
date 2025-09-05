# engine/matchEngine/choice/scrum/drive.py
from typing import List
from .common import (
    DoCall, team_possession, ScrumScore, compute_drive_increment,
    outcome_from_score, tactic_decision, counter_shove_check
)

def plan(match, state_tuple) -> List[DoCall]:
    """
    Stage 5: Drive
    - After each drive 'instance', we:
        * increment score with drive rule (stub)
        * check penalty thresholds
        * consult tactic to decide 'take_out' vs 'scrum_on' (only feeding team can end)
        * allow one counter-shove check while in stable (handled in stable.py)
    """
    calls: List[DoCall] = []
    atk = team_possession(match)
    s = getattr(match, "_scrum_score", None) or ScrumScore()

    # +drive increment (second rows etc.)
    s.value += compute_drive_increment(match, atk)
    match._scrum_score = s

    # Penalty gate
    outcome = outcome_from_score(s.value)
    if outcome:
        match._scrum_outcome = outcome
        return calls

    # Tactic (read from match or default)
    tactic = getattr(match, "scrum_tactic", "mixed")  # "channel1", "mixed", "leave_in"
    decision = tactic_decision(match, atk, s, tactic)

    if decision == "take_out":
        match.ball.set_action("scrum_stable")  # progress to stable to finalize exit
    else:
        # keep scrumming -> push animation hint for both packs
        for p in match.players:
            if getattr(p, "phase_role", "") == "scrum":
                calls.append((getattr(p, "pid", None) or getattr(p, "id", None),
                              ("push", None), (0.0,0.0,0.0), (0.0,0.0,0.0)))

    return calls
