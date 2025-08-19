# states/restart.py — flags + helpers

KICK_OFF      = "restart.kick_off"   # keep the exact tag used in ActionMatrix
DROP_22       = "restart.22Drop"
GOAL_LINE     = "Goal_line"

RESTART_TAGS = {
    KICK_OFF,
    DROP_22,
    GOAL_LINE,
}

# --- NEW: helper to perform a kickoff and prime FSM for kick return flow ---

from typing import Optional, Tuple
from set_pieces.restart import kickoff as do_kickoff
import event # same module used by StateController



def kickoff_now(match, to: str = "b") -> None:
    do_kickoff(match, to=to)
    x, y, _ = match.ball.location
    #event.set_event("open_play.kick_chase", (float(x), float(y)), to)

def maybe_handle(match, tag, loc, ctx) -> bool:
    if tag in RESTART_TAGS:
        if tag == KICK_OFF:
            to = ctx if isinstance(ctx, str) else (getattr(match, "last_restart_to", None) or "b")
            kickoff_now(match, to=to)
        match.ball.update(match)
        return True
    return False
