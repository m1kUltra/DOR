# states/scoring.py
from typing import Tuple
import event
from states.nudge import CONVERSION
from utils.actions.scoring_check import check_try
from utils.core.scoreboard import score_update
from constants import TRYLINE_A_X, TRYLINE_B_X
CHECK_TRY = "score.check_try"
SCORING_TAGS = { CHECK_TRY }

"""todo have scoring check if ball is over line. 
if over opposition tryline of holder award try else give goaline drop out restart to the ball holders team
"""


def try_now(match, to: str = "b") -> bool:
    
    b = match.ball
        
    holder = getattr(b, "holder", None)
    b.set_action("try")
    # Prefer explicit side if provided; otherwise fall back to holder
    team = to if isinstance(to, str) and to in ("a", "b") else (holder or "b")
    score_update(match, team, "try")
    return True
    

    #return False 

def maybe_handle(match, tag, loc, ctx) -> bool:
    if tag in SCORING_TAGS:
        b = match.ball
        if tag == CHECK_TRY:
           
            if check_try(match):
                try_now(match, ctx if isinstance(ctx, str) else "b")
            else:
                x, y, _ = getattr(b, "location", (0.0, 0.0, 0.0))
                holder = getattr(b, "holder", None)
                team = holder[-1] if isinstance(holder, str) else (ctx if isinstance(ctx, str) else "b")
                if x <= TRYLINE_A_X or x >= TRYLINE_B_X:
                    event.set_event("restart.goal_line_drop", (x, y), team)
                    b.set_action("goal_line")
                else:
                    b.set_action("dropped")
        b.update(match)
        return True
    return False
