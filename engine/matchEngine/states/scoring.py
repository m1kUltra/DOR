# states/scoring.py
from typing import Tuple
import event
from states.nudge import CONVERSION
from utils.actions.scoring_check import check_try

CHECK_TRY = "score.check_try"
SCORING_TAGS = { CHECK_TRY }




def try_now(match, to: str = "b") -> bool:
    
    b = match.ball
        
    holder = getattr(b, "holder", None)
    loc = tuple(getattr(b, "location", (0.0, 0.0, 0.0)))
        # set current action to "try" (controller will pick it up next tick)
    b.status = {"action": "try", "holder": holder, "location": loc}
    return True
    

    #return False 

def maybe_handle(match, tag, loc, ctx) -> bool:
    if tag in SCORING_TAGS:
        if tag == CHECK_TRY:
            try_now(match, ctx if isinstance(ctx, str) else "b")
        match.ball.update(match)
        return True
    return False
