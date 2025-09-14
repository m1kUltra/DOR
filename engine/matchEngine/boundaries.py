"""Boundary checks for ball out-of-play situations."""

from constants import (
    TRYLINE_A_X,
    TRYLINE_B_X,
    DEADBALL_LINE_A_X,
    DEADBALL_LINE_B_X,
    TOUCHLINE_TOP_Y,
    TOUCHLINE_BOTTOM_Y,
)
from team.team_controller import set_possession

def _opp(team: str | None) -> str | None:
    if team == "a":
        return "b"
    if team == "b":
        return "a"
    return None

def check(match) -> None:
    """Inspect ball position and mark boundary actions.

    This updates ``match.ball.action`` and related restart metadata when the
    ball leaves the playing area.  Touchline checks trigger ``in_touch``; going
    over the tryline or dead‑ball line triggers either a 22‑drop or a scrum
    restart depending on the origin of the kick.
    """
    ball = match.ball
    x, y, _ = ball.location

    last = getattr(ball, "last_status", {}) or {}
    last_holder = last.get("holder")
    last_team = last_holder[-1] if isinstance(last_holder, str) else None
    restart_team = _opp(last_team)
    
     
    
      

    # --- Touchlines -------------------------------------------------------
    if y <= TOUCHLINE_BOTTOM_Y or y >= TOUCHLINE_TOP_Y:
        ball.set_action("in_touch")
        set_possession(match, restart_team)
        return

    # --- Trylines / dead‑ball lines --------------------------------------
    side = None
    if x <= TRYLINE_A_X or x <= DEADBALL_LINE_A_X:
        side = ("a", TRYLINE_A_X)
    elif x >= TRYLINE_B_X or x >= DEADBALL_LINE_B_X:
        side = ("b", TRYLINE_B_X)

    if side is None:
        return

    defend_team, try_x = side
    last_loc = last.get("location") or (x, y, 0.0)
    last_x = last_loc[0]
    dist = abs(last_x - try_x)

    is_pen_goal = getattr(ball, "_last_action", None) == "penalty_goal"

    match.restart_spot = (x, y)

    if dist <= 30 or is_pen_goal:
        ball.set_action("dead")
        match.last_restart_to = defend_team
       
        set_possession(match, defend_team)
    else:
        ball.set_action("scrum_pending")
        match.pending_scrum = {
            "x": x,
            "y": y,
            "put_in": defend_team,
            "reason": "ball_dead",
        }
       
        set_possession(match, defend_team)