# states/restart.py — flags + helpers


KICK_OFF       = "restart.kick_off"   # keep the exact tag used in ActionMatrix
DROP_22        = "restart.22_drop"
GOAL_LINE_DROP = "restart.goal_line_drop"

RESTART_TAGS = {
    KICK_OFF,
    DROP_22,
   
    GOAL_LINE_DROP,
}

# --- NEW: helper to perform a kickoff and prime FSM for kick return flow ---

from typing import Optional, Tuple
import event # same module used by StateController
from set_pieces.restart import (
    kickoff as do_kickoff,
    drop_22 as do_drop_22,
    goal_line_drop as do_goal_line_drop,
)
import event  # same module used by StateController



def kickoff_now(match, to: str = "a") -> None:
    do_kickoff(match, to=to)
    x, y, _ = match.ball.location
    #event.set_event("open_play.kick_chase", (float(x), float(y)), to)


def drop_22_now(match, to: str = "a") -> None:
    do_drop_22(match, to=to)


def goal_line_drop_now(match, to: str = "a") -> None:
    do_goal_line_drop(match, to=to)

def maybe_handle(match, tag, loc, ctx) -> bool:
    if tag in RESTART_TAGS:
        to = getattr(match, "possession", None)
        if isinstance(ctx, str) and ctx in ("a", "b"):
            to = ctx
        to = to or getattr(match, "last_restart_to", "a")  
        if tag == KICK_OFF:
            kickoff_now(match, to=to)
        elif tag == DROP_22:
            drop_22_now(match, to=to)
        elif tag == GOAL_LINE_DROP:
            goal_line_drop_now(match, to=to)
        match.ball.update(match)
        return True
    return False