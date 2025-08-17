# states/restart.py — flags + helpers

KICK_OFF      = "restart.kick_off"    # keep the exact tag used in ActionMatrix
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
    """
    Hard-setup + execute kickoff, then set a one-frame event so the next tick
    starts in 'open_play.kick_return'. After that, normal status transitions take over.
    """
    # 1) Do the actual placement + kick
    do_kickoff(match, to=to)

    # 2) Prime FSM for next tick: tag as open play (kick return phase)
    x, y, _ = match.ball.location
    # Team 'to' is the receiving team; pass it through as the event 'team' field
    event.set_event("open_play.kick_return", (float(x), float(y)), to)
