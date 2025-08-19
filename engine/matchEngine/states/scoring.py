# states/scoring.py  (thin wrapper around your utils)
from typing import Tuple
import event
from constants import TRYLINE_A_X, TRYLINE_B_X, PITCH_WIDTH
from states.nudge import CONVERSION
from utils.actions.scoring_check import check_try

CHECK_TRY = "score.check_try"
SCORING_TAGS = { CHECK_TRY }

def try_now(match, to: str = "b") -> bool:
    if check_try:


    # emit conversion exactly once
       
        x, y, _ = match.ball.location
    # Team 'to' is the receiving team; pass it through as the event 'team' field
        event.set_event("nudge.conversion", (float(x), float(y)), to)        # reset per-try id
        return True

    else: return False