
# utils/actions/scoring_check.py
from constants import PITCH_WIDTH, TRYLINE_A_X, TRYLINE_B_X, POST_GAP, CROSSBAR

def _is_over_correct_tryline(x: float, atk_sign: int) -> bool:
    return (x >= TRYLINE_B_X) if atk_sign > 0 else (x <= TRYLINE_A_X)

def check_try(match) -> bool:
    ball_x, _, _ = match.ball.location
   

    possessor = next((t for t in (match.team_a, match.team_b) if t.in_possession), None)
    if possessor is None:
        return False

    atk_sign = possessor.attack_sign   # <- property on Team
    return _is_over_correct_tryline(ball_x, atk_sign)



def conversion_checker(match, tol_x: float = 0.75) -> bool:
    """Return True if the ball passed between the posts and above the crossbar."""

    b = match.ball

    # Previous and current locations (fallback to current if last missing)
    x1, y1, z1 = b.location
    x0, y0, z0 = (b.last_status or {}).get("location", (x1, y1, z1))

    # Which posts? Use the scoring team's attack_dir if available.
    team_code = getattr(match, "last_try_team", None)
    if team_code == "a":
        team = match.team_a
    elif team_code == "b":
        team = match.team_b
    else:
        # Fallback: whoever is/was in possession
        team = match.team_a if getattr(match.team_a, "in_possession", False) else match.team_b

    attack_dir = float(getattr(getattr(team, "tactics", {}), "get", lambda *_: +1.0)("attack_dir"))
    try_x = TRYLINE_B_X if attack_dir > 0 else TRYLINE_A_X

    # Did the motion between frames cross the plane x = try_x?
    dx = x1 - x0
    crossed = (x0 - try_x) * (x1 - try_x) <= 0 and abs(dx) > 1e-6
    if crossed:
        t = (try_x - x0) / dx
        # Clamp to [0,1] to avoid tiny numeric drift
        if t < 0.0:
            t = 0.0
        elif t > 1.0:
            t = 1.0
        y = y0 + t * (y1 - y0)
        z = z0 + t * (z1 - z0)
    else:
        # Fallback: accept "close enough" to the plane at current frame
        if abs(x1 - try_x) > tol_x:
            return False
        y, z = y1, z1

    center_y = PITCH_WIDTH * 0.5
    between_posts = (center_y - POST_GAP) <= y <= (center_y + POST_GAP)
    above_bar = z >= CROSSBAR
    return bool(between_posts and above_bar)
