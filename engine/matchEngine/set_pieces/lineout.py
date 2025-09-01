# engine/matchEngine/set_pieces/lineout.py
from typing import List, Tuple, Optional
from actions.action_controller import do_action
from choice.lineout.start import plan as start_plan
from choice.lineout.forming import plan as forming_plan
from choice.lineout.over import plan as over_plan
from choice.lineout.out import plan as out_plan

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

# --- placeholder calculation hooks (see calculations.txt lines 181+) ---

def _throw_score(match) -> float:
    """Hooker throw accuracy placeholder."""
    return 0.0

def _contest_score(match) -> float:
    """Jump/lift contest placeholder."""
    return 0.0

# --- state handlers ---

def handle_start(match, state_tuple) -> None:
    bx, by, _ = _xyz(getattr(match.ball, "location", None))
    _team_possession(match)
    match.ball.holder = None
    match.ball.location = (bx, by, 0.0)
    match.ball.set_action("lineout_forming")
    calls = start_plan(match, state_tuple) or []
    for pid, action, loc, target in calls:
        do_action(match, pid, action, loc, target)
    match.lineout_score = _throw_score(match)

def handle_forming(match, state_tuple) -> None:
    calls = forming_plan(match, state_tuple) or []
    for pid, action, loc, target in calls:
        do_action(match, pid, action, loc, target)
    match.lineout_score = getattr(match, "lineout_score", 0.0) + _contest_score(match)
    match.ball.set_action("lineout_over")

def handle_over(match, state_tuple) -> None:
    calls = over_plan(match, state_tuple) or []
    for pid, action, loc, target in calls:
        do_action(match, pid, action, loc, target)


def handle_out(match, state_tuple) -> None:
    calls = out_plan(match, state_tuple) or []
    for pid, action, loc, target in calls:
        do_action(match, pid, action, loc, target)