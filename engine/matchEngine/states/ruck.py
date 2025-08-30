# states/ruck.py
from typing import Optional
import random, event

START   = "ruck.start"
FORMING = "ruck.forming"
OVER    = "ruck.over"
OUT = "ruck.out"
RUCK_TAGS = {START, FORMING, OVER, OUT}




# states/ruck.py
from set_pieces.ruck import handle_start, handle_forming, handle_over, handle_out



def maybe_handle(match, tag, loc, ctx) -> bool:
    
    if not isinstance(tag, str) or not (tag == START or tag.startswith("ruck.")):
        return False
    
    if tag == START:
        handle_start(match, (tag, loc, ctx))
        return True

    if tag == FORMING:
        handle_forming(match, (tag, loc, ctx))
        return True

    if tag == OVER:
        handle_over(match, (tag, loc, ctx))
        return True
    if tag == OUT:
        handle_out(match, (tag, loc, ctx))
        return True


    return False
