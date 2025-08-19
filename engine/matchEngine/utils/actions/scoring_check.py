# utils/actions/scoring_check.py
from constants import TRYLINE_A_X, TRYLINE_B_X, POST_GAP,CROSSBAR

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
    from constants import TRYLINE_A_X, TRYLINE_B_X, POST_GAP, CROSSBAR
    x, y, z = match.ball.location
    on_plane = abs(x - TRYLINE_A_X) <= tol_x or abs(x - TRYLINE_B_X) <= tol_x
    between  = (35.0 - POST_GAP) <= y <= (35.0 + POST_GAP)
    return bool(on_plane and between and z >= CROSSBAR)
        
   


   
    

       # <- property on Team