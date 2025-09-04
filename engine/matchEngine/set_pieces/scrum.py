# engine/matchEngine/set_pieces/scrum.py
from typing import List, Tuple, Optional
from actions.action_controller import do_action
from choice.scrum.start import plan as start_plan
from choice.scrum.forming import plan as forming_plan
from choice.scrum.over import plan as over_plan
from choice.scrum.out import plan as out_plan

DoCall = Tuple[str, Tuple[str, Optional[str]], Tuple[float, float, float], Tuple[float, float, float]]

def _xyz(p):
    return tuple(p) if isinstance(p, (list, tuple)) else (0.0, 0.0, 0.0)

def _team_possession(match) -> str:
    if getattr(match, "possession", None) in ("a", "b"):
        return match.possession
    hid = getattr(match.ball, "holder", None)
    code = hid[-1] if isinstance(hid, str) and hid else "a"
    match.possession = code
    return code

def _other(code: str) -> str:
    return "b" if code == "a" else "a"

# --- placeholder calculation hooks (see calculations.txt lines 150-179) ---

def _initial_score(match) -> float:
    """Initial engage score; insert formula from calculations.txt later."""
    return 0.0

def _drive_score(match) -> float:
    """Drive phase accumulation; placeholder for future calculation."""
    return 0.0

def _counter_shove(match) -> float:
    """Counter shove during stable phase; placeholder for future calculation."""
    return 0.0

# --- state handlers ---

def handle_start(match, state_tuple) -> None:
    bx, by, _ = _xyz(getattr(match.ball, "location", None))
    _team_possession(match)
   
    match.ball.location = (bx, by, 0.0)
    atk = match.possession
    p9 = match.teams[atk].get_player_by_rn(9)
    if p9:
        match.ball.holder = f"{p9.sn}{p9.team_code}"
        match.ball.location = p9.location
    match.ball.set_action("scrum_forming")
    calls = start_plan(match, state_tuple) or []
    for pid, action, loc, target in calls:
        do_action(match, pid, action, loc, target)
    match.scrum_score = _initial_score(match)

def handle_forming(match, state_tuple) -> None:
    calls = forming_plan(match, state_tuple) or []
    for pid, action, loc, target in calls:
        do_action(match, pid, action, loc, target)
    match.scrum_score = getattr(match, "scrum_score", 0.0) + _drive_score(match)
    match.ball.set_action("scrum_over")

def handle_over(match, state_tuple) -> None:
    calls = over_plan(match, state_tuple) or []
    for pid, action, loc, target in calls:
        do_action(match, pid, action, loc, target)
    match.scrum_score = getattr(match, "scrum_score", 0.0) + _counter_shove(match)


def handle_out(match, state_tuple) -> None:
    calls = out_plan(match, state_tuple) or []
    for pid, action, loc, target in calls:
        do_action(match, pid, action, loc, target)