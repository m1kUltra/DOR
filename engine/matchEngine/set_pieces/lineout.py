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

def _team_possession(match, code: Optional[str] = None) -> str:
    if code in ("a", "b"):
        match.possession = code
        return code
    if getattr(match, "possession", None) in ("a", "b"):
        return match.possession
    hid = getattr(match.ball, "holder", None)
    code = hid[-1] if isinstance(hid, str) and hid else "a"
    match.possession = code
    return code

def _other(code: str) -> str:
    return "b" if code == "a" else "a"

# --- placeholder calculation hooks (see calculations.txt lines 181+) ---

import random


def _throw_score(match) -> float:
    """Hooker throw accuracy placeholder."""
    
    team_code = _team_possession(match)
    team = match.team_a if team_code == "a" else match.team_b
    hooker = team.get_player_by_rn(2) if team else None
    if not hooker:
        return 0.0
    attrs = getattr(hooker, "norm_attributes", {}) or {}
    darts = float(attrs.get("darts", 0.0))
    composure = float(attrs.get("composure", 0.0))
    decisions = float(attrs.get("decisions", 0.0))
    skill = (darts * 0.6) + (composure * 0.25) + (decisions * 0.15)
    return max(0.0, min(1.0, skill * (random.random() ** 0.5)))


def _contest_score(match) -> float:
    """Jump/lift contest placeholder."""
    
    meta = getattr(match, "lineout_meta", {}) or {}
    team_code = _team_possession(match)
    atk = match.team_a if team_code == "a" else match.team_b
    dfn = match.team_b if team_code == "a" else match.team_a
    jsn = meta.get("jumper_sn")
    atk_jumper = atk.get_player_by_sn(jsn) if (atk and jsn) else None
    def_jumper = (dfn.get_player_by_rn(4) or dfn.get_player_by_rn(5) or dfn.get_player_by_rn(6)) if dfn else None
    if not atk_jumper or not def_jumper:
        return 0.0
    a_attrs = getattr(atk_jumper, "norm_attributes", {}) or {}
    d_attrs = getattr(def_jumper, "norm_attributes", {}) or {}
    a_skill = float(a_attrs.get("lineouts", 0.0)) * (0.5 + 0.5 * float(a_attrs.get("jumping_reach", 0.0)))
    d_skill = float(d_attrs.get("lineouts", 0.0)) * (0.5 + 0.5 * float(d_attrs.get("jumping_reach", 0.0)))
    return max(-1.0, min(1.0, (a_skill * (random.random() ** (1/3))) - (d_skill * (random.random() ** (1/3)))))


# --- state handlers ---

def handle_start(match, state_tuple) -> None:
    bx, by, _ = _xyz(getattr(match.ball, "location", None))
    tag, loc, ctx = state_tuple
    throw = ctx.get("throw") if isinstance(ctx, dict) else None
    throw = _team_possession(match, throw)
    calls = start_plan(match, state_tuple) or []
    hooker_code = f"2{throw}"
    hooker_target = (bx, by, 0.0)
    for pid, action, loc, target in calls:
        if pid == hooker_code and target:
            hooker_target = target
        do_action(match, pid, action, loc, target)
    match.ball.holder = hooker_code
    match.ball.location = hooker_target
    match.ball.set_action("lineout_forming")
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
    match.ball.set_action("lineout_out")

def handle_out(match, state_tuple) -> None:
    calls = out_plan(match, state_tuple) or []
    for pid, action, loc, target in calls:
        do_action(match, pid, action, loc, target)