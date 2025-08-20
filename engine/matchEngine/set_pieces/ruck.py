# set_pieces/ruck.py
from typing import List, Tuple, Optional
from actions.action_controller import do_action
from choice.ruck.start import plan as start_plan
from choice.ruck.forming import plan as forming_plan
from choice.ruck.over import plan as over_plan

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

# ----- PHASE HANDLERS -----

def handle_start(match, state_tuple) -> None:
    """Neutralise ball at ground and flip to ruck.forming; run start choices."""
    bx, by, _ = _xyz(getattr(match.ball, "location", None))
    _team_possession(match)             # ensure possession set for later phases
    match.ball.holder   = None
    match.ball.location = (bx, by, 0.0)
    match.ball.set_action("ruck_forming")

    calls = start_plan(match, state_tuple) or []
    for pid, action, loc, target in calls:
        do_action(match, pid, action, loc, target)

def handle_forming(match, state_tuple) -> None:
    """Run contest logic + forming choices. Decide outcome → ruck_over."""
    bx, by, _ = _xyz(getattr(match.ball, "location", None))
    atk = _team_possession(match)
    deff = _other(atk)

    # 1) Move bodies according to your ruck behaviour
    calls = forming_plan(match, state_tuple) or []
    for pid, action, loc, target in calls:
        do_action(match, pid, action, loc, target)

    # 2) Decide outcome (ultra-minimal: 2 attackers within R wins; 1 defender & 0 attackers → turnover)
    R2 = 2.5 * 2.5
    a_cnt = d_cnt = 0
    for p in match.players:
        dx, dy = p.location[0]-bx, p.location[1]-by
        if dx*dx + dy*dy <= R2:
            if p.team_code == atk: a_cnt += 1
            else:                  d_cnt += 1

    if a_cnt >= 2:
        # attack secures
        match.possession = atk
        match.ball.holder   = None
        match.ball.location = (bx, by, 0.0)
        match.ball.set_action("ruck_over")
        return

    if d_cnt >= 1 and a_cnt == 0:
        # turnover
        match.possession = deff
        match.ball.holder   = None
        match.ball.location = (bx, by, 0.0)
        match.ball.set_action("ruck_over")
        return

    # else: keep forming (no flip)

def handle_over(match, state_tuple) -> None:
    """Ball is out + playable; give phase‑specific choices (e.g., 9 pickup)."""
    calls = over_plan(match, state_tuple) or []
    for pid, action, loc, target in calls:
        do_action(match, pid, action, loc, target)
    # leave ball action/tag alone; open play will resume once someone picks it up
