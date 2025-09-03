# engine/matchEngine/set_pieces/ruck.py
from typing import List, Tuple, Optional
from actions.action_controller import do_action
from choice.ruck.start import plan as start_plan
from choice.ruck.forming import plan as forming_plan
from choice.ruck.over import plan as over_plan
from choice.ruck.out import plan as out_plan

DoCall = Tuple[str, Tuple[str, Optional[str]], Tuple[float,float,float], Tuple[float,float,float]]

def _xyz(p):
    return tuple(p) if isinstance(p, (list,tuple)) else (0.0,0.0,0.0)

def _team_possession(match) -> str:
    if getattr(match, "possession", None) in ("a","b"):
        return match.possession
    hid = getattr(match.ball, "holder", None)
    code = hid[-1] if isinstance(hid, str) and hid else "a"
    match.possession = code
    return code

def _other(code: str) -> str: return "b" if code == "a" else "a"

def handle_start(match, state_tuple) -> None:
    #TODO implment check over_line 
    """
    if over. own tryline implment goaline restart
    else its a try (call check_scoring)
    """
    bx, by, _ = _xyz(getattr(match.ball, "location", None))
    _team_possession(match)
    match.ball.holder   = None
    match.ball.location = (bx, by, 0.0)
    match.ball.set_action("ruck_forming")

    calls = start_plan(match, state_tuple) or []
    for pid, action, loc, target in calls:
        do_action(match, pid, action, loc, target)

def handle_forming(match, state_tuple) -> None:
    bx, by, _ = _xyz(getattr(match.ball, "location", None))
    atk = _team_possession(match)
    deff = _other(atk)

    calls = forming_plan(match, state_tuple) or []
    for pid, action, loc, target in calls:
        do_action(match, pid, action, loc, target)

    # outcome: simple secure vs turnover (can keep your current heuristic)
    R2 = 2.5 * 2.5
    a_cnt = d_cnt = 0
    for p in match.players:
        dx, dy = p.location[0]-bx, p.location[1]-by
        if dx*dx + dy*dy <= R2:
            if p.team_code == atk: a_cnt += 1
            else:                  d_cnt += 1

    if a_cnt >= 2 or (d_cnt >= 1 and a_cnt == 0):
        # flip to "ruck_over" and let over_plan gate pickup
        match.ball.holder   = None
        match.ball.location = (bx, by, 0.0)
        match.ball.set_action("ruck_over")

def handle_over(match, state_tuple) -> None:
    calls = over_plan(match, state_tuple) or []
    for pid, action, loc, target in calls:
        do_action(match, pid, action, loc, target)
    # NOTE: over_plan will issue ("picked", None) when ready/timeout

def handle_out(match, state_tuple) -> None:
    calls = out_plan(match, state_tuple) or []
    for pid, action, loc, target in calls:
        do_action(match, pid, action, loc, target)
    # NOTE: out_plan will "pass" when ready/timeout
