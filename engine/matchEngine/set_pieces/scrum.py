import random
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


# --- scrum calculation helpers -------------------------------------------------

def _attr(player, name: str) -> float:
    return getattr(player, name, 0.0) if player else 0.0


def _initial_score(match) -> Tuple[float, bool]:
    """Stages 1‑3: crouch, bind, set. Returns (score, lock_out)."""
    atk = _team_possession(match)
    team = match.teams[atk]

    lh = team.get_player_by_rn(1)
    hk = team.get_player_by_rn(2)
    th = team.get_player_by_rn(3)

    leadership = _attr(hk, "leadership")
    scr_lh = _attr(lh, "scrummaging")
    scr_th = _attr(th, "scrummaging")

    score = (leadership ** 2) * (scr_lh + scr_th) / 3.0
    score += (scr_lh * _attr(lh, "strength")) * (scr_th * _attr(th, "strength"))

    pack_weight = 0.0
    for rn in range(1, 9):
        p = team.get_player_by_rn(rn)
        pack_weight += getattr(p, "weight", 0.0)

    score += (pack_weight / 1000.0) * (scr_lh + scr_th) * random.random()
    lock_out = random.random() > 0.5
    return score, lock_out


def _drive_score(match) -> float:
    """Drive phase accumulation; placeholder for future calculation."""
  
    """Stage 5 drive accumulation."""
    atk = _team_possession(match)
    team = match.teams[atk]

    term = (
        _attr(team.get_player_by_rn(3), "scrummaging")
        * _attr(team.get_player_by_rn(3), "strength")
        * _attr(team.get_player_by_rn(3), "aggression")
        + _attr(team.get_player_by_rn(1), "scrummaging")
        * _attr(team.get_player_by_rn(1), "strength")
        * _attr(team.get_player_by_rn(1), "aggression")
        + _attr(team.get_player_by_rn(2), "scrummaging")
        * _attr(team.get_player_by_rn(2), "strength")
        * _attr(team.get_player_by_rn(2), "aggression")
        / 2.0
        + _attr(team.get_player_by_rn(4), "determination")
        * _attr(team.get_player_by_rn(4), "strength")
        + _attr(team.get_player_by_rn(5), "determination")
        * _attr(team.get_player_by_rn(5), "strength")
        * 1.5
    ) / 5.0
    return term


def _counter_shove(match) -> float:
    """Counter shove during stable phase; placeholder for future calculation."""
    
    """Opposition counter shove during stable phase."""
    atk = _team_possession(match)
    opp = _other(atk)
    atk_team = match.teams[atk]
    def_team = match.teams[opp]

# --- state handlers ---
    feed_val = (
        _attr(atk_team.get_player_by_rn(1), "strength")
        * _attr(atk_team.get_player_by_rn(1), "weight")
        / 150.0
        * _attr(atk_team.get_player_by_rn(3), "strength")
        * _attr(atk_team.get_player_by_rn(3), "weight")
        / 150.0
    )

    opp_val = (
        _attr(def_team.get_player_by_rn(1), "aggression")
        * _attr(def_team.get_player_by_rn(1), "scrummaging")
        / 150.0
        * _attr(def_team.get_player_by_rn(3), "aggression")
        * _attr(def_team.get_player_by_rn(3), "scrummaging")
        / 150.0
    )

    rnd = random.random() ** (1.0 / 3.0)
    return feed_val * rnd - opp_val * rnd


def _should_scrum(match) -> bool:
    tactic = getattr(match, "scrum_tactic", "mixed")
    score = getattr(match, "scrum_score", 0.0)
    if tactic == "channel1":
        return score <= -0.75
    if tactic == "mixed":
        if score > 0.5:
            return True
        if score < -0.75:
            return True
        return False
    if tactic == "leave_in":
        return not (-0.75 < score < -0.25)
    return True


def _check_penalty(match) -> bool:
    score = getattr(match, "scrum_score", 0.0)
    if score > 1.0:
        match.scrum_penalty = _team_possession(match)
        match.ball.set_action("penalty")
        return True
    if score < -1.0:
        match.scrum_penalty = _other(_team_possession(match))
        match.ball.set_action("penalty")
        return True
    return False


# --- state handlers -----------------------------------------------------------

def handle_start(match, state_tuple) -> None:
    bx, by, _ = _xyz(getattr(match.ball, "location", None))
    _team_possession(match)
   

    match.ball.location = (bx, by, 0.0)
    atk = match.possession
    team = match.get_team(atk)
    p9 = team.get_player_by_rn(9) if team else None
    if p9:
        match.ball.holder = f"{p9.sn}{p9.team_code}"
        match.ball.location = p9.location
    
    calls = start_plan(match, state_tuple) or []
    for pid, action, loc, target in calls:
        do_action(match, pid, action, loc, target)
    

    score, lock_out = _initial_score(match)
    match.scrum_score = score
    if _check_penalty(match):
        return
    if lock_out:
        match.ball.set_action("scrum_out")
    else:
        match.ball.set_action("scrum_forming")


def handle_forming(match, state_tuple) -> None:
    calls = forming_plan(match, state_tuple) or []
    for pid, action, loc, target in calls:
        do_action(match, pid, action, loc, target)
    if not _should_scrum(match):
        match.ball.set_action("scrum_out")
        return
    match.scrum_score = getattr(match, "scrum_score", 0.0) + _drive_score(match)
    if _check_penalty(match):
        return
    match.ball.set_action("scrum_over")


def handle_over(match, state_tuple) -> None:
    calls = over_plan(match, state_tuple) or []
    for pid, action, loc, target in calls:
        do_action(match, pid, action, loc, target)
    match.scrum_score = getattr(match, "scrum_score", 0.0) + _counter_shove(match)
    _check_penalty(match)


def handle_out(match, state_tuple) -> None:
    calls = out_plan(match, state_tuple) or []
    for pid, action, loc, target in calls:
     
        do_action(match, pid, action, loc, target)
