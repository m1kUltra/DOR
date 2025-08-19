# states/scoring.py — flags + thin helper

from typing import Tuple
import event
from constants import TRYLINE_A_X, TRYLINE_B_X
from states.nudge import CONVERSION
from utils.scoring import award_try  # ⬅️ use your existing utils

# kept exactly as in ActionMatrix
CHECK_TRY = "score.check_try"

SCORING_TAGS = {
    CHECK_TRY,
}

def _attack_dir_for_team(match, team_code: str) -> float:
    team = match.team_a if team_code == "a" else match.team_b
    return float((getattr(team, "tactics", {}) or {}).get("attack_dir", +1.0))

def _is_over_correct_tryline(x: float, attack_dir: float) -> bool:
    if attack_dir > 0:
        return x >= float(TRYLINE_B_X)
    return x <= float(TRYLINE_A_X)

def checktry(match) -> bool:
    """
    Thin wrapper:
      - Determine if grounding was over the correct tryline.
      - If yes, award via utils.scoring.award_try(...).
      - Schedule 'nudge.conversion' for next tick.
      - Return True on award, else False.
    """
    ball = match.ball
    holder_id = getattr(ball, "holder", None)
    if not holder_id:
        return False

    holder = match.get_player_by_code(holder_id)
    if holder is None:
        return False

    # Use ball position if available; fall back to holder
    bx, by, _ = getattr(ball, "location", holder.location)
    team_code = holder.team_code
    atk_dir   = _attack_dir_for_team(match, team_code)

    if not _is_over_correct_tryline(float(bx), atk_dir):
        return False

    # Delegate bookkeeping (+5, conversion context, restart info) to utils
    payload = award_try(match, team_code, (float(bx), float(by)))

    # Optional: remember for restarts if your flow uses this
    try:
        match.last_restart_to = payload.get("next_restart_to", None)
    except Exception:
        pass

    # Prime FSM for the conversion phase (same pattern as kickoff_now)
    event.set_event(CONVERSION, (float(bx), float(by)), team_code)
    return True
