from typing import Tuple, Optional

from actions.action_controller import do_action

from team.team_controller import set_possession

from shapes.lineout.five_man import generate_five_man_lineout_shape
from shapes.lineout.five_man_backline import generate_phase_play_shape
from utils.actions.catch_windows import can_catch
from constants import TOUCHLINE_BOTTOM_Y, TOUCHLINE_TOP_Y
DoCall = Tuple[str, Tuple[str, Optional[str]], Tuple[float, float, float], Tuple[float, float, float]]


def _xyz(p) -> Tuple[float, float, float]:
    return tuple(p) if isinstance(p, (list, tuple)) else (0.0, 0.0, 0.0)



    set_possession(match, code)
    return code


def _other(code: str) -> str:
    return "b" if code == "a" else "a"

def handle_start(match, state_tuple) -> None:
    """Initialise a lineout and move players into formation."""
    bx, by, _ = _xyz(getattr(match.ball, "location", None))
    tag, loc, ctx = state_tuple
    
    pending = getattr(match, "pending_lineout", {}) or {}

    throw = pending.get("throw")
    if throw is None and isinstance(ctx, dict):
        throw = ctx.get("throw")
    throw = match.possession
    

    
    match.pending_lineout = {}

    throwing_team = match.team_a if throw == "a" else match.team_b
    defending_team = match.team_b if throw == "a" else match.team_a

    attack_dir = float(throwing_team.tactics.get("attack_dir", 1.0))

    if by < 1:
        touch_is_bottom = True
    else: 
        touch_is_bottom = False

    phase_shape = generate_phase_play_shape("default", attack_dir)
    layout = generate_five_man_lineout_shape(
         # or compute from pitch constants
        touch_is_bottom=touch_is_bottom,
        attack_dir=attack_dir, backline_positions= phase_shape
       )
  
   
    atk_layout = layout["team_a"]
    def_layout = layout["team_b"]
  

    def _apply(team, sub_layout):
        for rn, (lx, ly) in sub_layout.items():
            try:
                jersey = int(rn)
            except (TypeError, ValueError):
                continue
            p = team.get_player_by_rn(jersey)
            if not p:
                continue
            wx = bx + lx
            wy = by + ly if touch_is_bottom else by - ly
            
            p.update_location(match.pitch.clamp_position((wx, wy, 0.0)))

    
    
        
     
   
    _apply(throwing_team, atk_layout)
    _apply(defending_team, def_layout)

    hooker_code = f"2{throw}"
    jumper_code = f"4{throw}"
    sh_code = f"9{throw}"
    match.ball.holder = hooker_code
    match.ball.location = (bx, by, 0.0)
    match.ball.set_action("lineout_forming")

    return hooker_code, jumper_code, sh_code
 
    # For now always target jersey 4 of the throwing team
    

    
    


def handle_forming(match, codes, state_tuple) -> None:
   
    
    """Execute the throw to the jumper and deliver to the scrum‑half."""
    """Execute the throw to the jumper and deliver to the scrum‑half."""
    throw = match.possession
    hooker_code, jumper_code, sh_code= codes


    hooker = match.get_player_by_code(hooker_code)
    jumper = match.get_player_by_code(jumper_code)
    sh = match.get_player_by_code(sh_code)
    ball = match.ball
    if hooker and jumper:
        hx, hy, _ = hooker.location
        jx, jy, _ = jumper.location
        catch_point = (hx, jy, 1)
        if ball.holder == hooker_code:
            do_action(match, hooker_code, ("throw", None), hooker.location, catch_point)
       
      
        do_action(match, jumper_code, ("deliver", None), jumper.location, sh.location)
    bx, by, bz = ball.location  
    print(bz)
    if (bz == 0) and  (ball.holder == None):
        ball.set_action("lineout_exit")



def handle_over(match, codes, state_tuple) -> None:
  
   
    """Have the scrum‑half catch the delivered ball before play continues."""
    hooker_code, jumper_code, sh_code= codes
    team = match.possession
    

    sh = match.get_player_by_code(sh_code)
    ball = match.ball

    if not sh:
        return

    # Wait for the delivery trajectory to finish unless the ball is already at the scrum-half
    if ball.transit:
        bx, by, bz = ball.location
        sx, sy, _ = sh.location
        if (bx - sx) ** 2 + (by - sy) ** 2 > 1e-4:
            return

  
    # Only attempt the catch if the ball is within the scrum-half's catch radius
    if can_catch(sh, ball.location):
    
        do_action(match, sh_code, ("catch", None), ball.location, sh.location)

    elif bz == 0 and ball.holder == None:
        ball.set_action("lineout_exit")


def handle_out(match, state_tuple) -> None:
   
    """Simple first pass from the scrum‑half to the fly‑half."""
    team = match.possession
    sh_code = f"9{team}"
    ten_code = f"10{team}"
    sh = match.get_player_by_code(sh_code)
    ten = match.get_player_by_code(ten_code)
    print(ten_code)
    ball = match.ball
    if sh and ten:
        ball.set_action("lineout_exit")
        do_action(match, sh_code, ("pass", None), sh.location, ten.location)
