# states/nudge.py

QUICK_TAP   = "nudge.quick_tap"
SLOW_TAP    = "nudge.slow_tap"
CONVERSION  = "nudge.conversion"
PEN_PUNT    = "nudge.pen_punt"
FREE_KICK   = "nudge.free_kick_punt"
AFTER_CONVERSION ="nudge.after_conversion"

NUDGE_TAGS = { QUICK_TAP, SLOW_TAP, CONVERSION, PEN_PUNT, FREE_KICK, AFTER_CONVERSION }

from typing import Optional
import event
from set_pieces.place_kick import conversion as do_conversion, conversion_transit
success= False
def conversion_now(match, to: Optional[str] = None) -> None:
    do_conversion(match, team_code=to)
    x, y, _ = match.ball.location
    event.set_event("open_play.kick_chase", (float(x), float(y)), to)

def maybe_handle(match, tag, loc, ctx) -> bool:
    if tag == CONVERSION:
        
        to = (ctx[-1].lower() if isinstance(ctx, str) and ctx and ctx[-1].lower() in ("a","b") else None)
        conversion_now(match, to=to)

    
        match.ball.update(match)   # same as restart.maybe_handle
        return True
    if tag == AFTER_CONVERSION:
        conversion_transit(match, success)
        return True
        
        
    
    
