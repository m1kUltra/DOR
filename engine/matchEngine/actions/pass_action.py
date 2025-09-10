# matchEngine/actions/pass_action.py

from constants import EPS
import math
import random

from utils.actions import pass_helpers
from utils.laws import advantage as adv_law

def _team_attack_dir(match, team_code: str) -> float:
    team = match.team_a if team_code == 'a' else match.team_b
    return float(team.tactics.get("attack_dir", +1.0))

def _is_backward_pass(pass_dir: float, dx: float) -> bool:
    """
    Rugby union: pass must be lateral or backwards relative to the passer's team attack direction.
    Here we approximate: along X only vs team attack_dir.
    pass_dir = +1.0 if team attacks to x+, -1.0 if to x-.
    dx = recipient_x - passer_x.
    """
    if pass_dir > 0:
        return dx <= EPS
    else:
        return dx >= -EPS

from typing import Optional, Tuple

XYZ = Tuple[float, float, float]


def do_action(match, passer_id: str, subtype: Optional[str], location: XYZ, target: XYZ) -> bool:
    ball = match.ball
    if not ball.is_held():
        return False

    
    passer = match.get_player_by_code(passer_id)
    if not passer:
        return False

    # NEW: mark status -> passed so the FSM sees it
   
    passing = float(getattr(passer, "norm_attributes", {}).get("passing", 0.0))
    technique = float(getattr(passer, "norm_attributes", {}).get("technique", 0.0))

   # determine attack direction and check for forward passes
    attack_dir = _team_attack_dir(match, passer.team_code)
   
    
        
    x, y, _ = location
    tx, ty, tz = target
    attack_dir = _team_attack_dir(match, passer.team_code)
   

    


 
    speed = _speed_for(passing, technique)
    range_ = pass_helpers.pass_range(passing, technique)
    scope = pass_helpers.pass_scope(technique)
    success_bonus = 0.0

    if subtype == "flat":
        speed /= 2.5
        range_ = min(range_, 10.0)
        success_bonus += 0.50
    elif subtype == "league":
        speed *= 0.75
        range_ = min(range_, 25.0)
        success_bonus += 0.25

    # compute a gentle arc so misplaced passes still drop to ground
   
    dist = math.hypot(tx - x, ty - y)

    success = pass_helpers.pass_success(dist, range_, passing) + success_bonus
    success = max(0.0, min(1.0, success))

    roll = random.random()
    if roll > success:
        error = roll - success
        if random.random() < 0.5:
            error = -error
        max_lateral = math.tan(scope / 2.0) * dist if scope else dist
        lateral = max(-max_lateral, min(max_lateral, (error * dist) / 3.0))
        ty += lateral
        target = (tx, ty, tz)
        max_longitudinal = dist
        longitudinal = max(-max_longitudinal, min(max_longitudinal, (error * dist) / 3.0))
        tx += longitudinal
        dist = math.hypot(tx - x, ty - y)


    if not _is_backward_pass(attack_dir, tx - x):
        ball.set_action("forward_pass")
        match.advantage = adv_law.start(
            None,
            type_="knock_on",
            to=("b" if passer.team_code == "a" else "a"),
            start_x=x,
            start_y=y,
            start_t=match.match_time,
            reason="forward_pass",
        )
    else:
        ball.set_action("passed")

    ball.release()

    hang = dist / speed if speed > 0 else 0.0
    ball.start_parabola_to((tx, ty, tz), T=hang, H=1.1, gamma=1.1)
    return True


def _speed_for(passing: float, technique: float) -> float:
    """Wrapper to compute base pass speed."""
    return pass_helpers.pass_speed(passing, technique)