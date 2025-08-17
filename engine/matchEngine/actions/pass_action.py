# matchEngine/actions/pass_action.py

from constants import EPS


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

    speed = _speed_for(subtype)

    # NEW: mark status -> passed so the FSM sees it
    ball.set_action("passed")

    ball.release()
    ball.start_linear_to(target, speed=speed)
    return True

def _speed_for(subtype: Optional[str]) -> float:
    # super light placeholder; tweak later or replace with attr-based calc
    if subtype == "flat":
        return 16.0
    if subtype == "skip":
        return 18.0
    if subtype == "tip":
        return 14.0
    return 15.0
