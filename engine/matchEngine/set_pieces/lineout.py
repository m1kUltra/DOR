from typing import Tuple, Optional

from actions.action_controller import do_action

from team.team_controller import set_possession

from shapes.scrum.default import generate_phase_play_shape
from shapes.lineout.five_man import generate_five_man_lineout_shape


DoCall = Tuple[str, Tuple[str, Optional[str]], Tuple[float, float, float], Tuple[float, float, float]]


def _xyz(p) -> Tuple[float, float, float]:
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






# --- state handlers ---

# ---------------------------------------------------------------------------
# State handlers
# ---------------------------------------------------------------------------

def handle_start(match, state_tuple) -> None:
    """Initialise a lineout and move players into formation."""
    bx, by, _ = _xyz(getattr(match.ball, "location", None))
    tag, loc, ctx = state_tuple
    
    pending = getattr(match, "pending_lineout", {}) or {}

    throw = pending.get("throw")
    if throw is None and isinstance(ctx, dict):
        throw = ctx.get("throw")
    throw = _team_possession(match, throw)
    

    set_possession(match, throw)
    match.pending_lineout = {}

    throwing_team = match.team_a if throw == "a" else match.team_b
    defending_team = match.team_b if throw == "a" else match.team_a

    attack_dir = float(throwing_team.tactics.get("attack_dir", 1.0))

    phase_shape = generate_phase_play_shape("default", attack_dir)
    layout = generate_five_man_lineout_shape(
        attack_dir=attack_dir,
        backline_positions=phase_shape,
    )

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
            wy = by + ly
            p.update_location(match.pitch.clamp_position((wx, wy, 0.0)))

    _apply(throwing_team, layout.get("team_a", {}))
    _apply(defending_team, layout.get("team_b", {}))

    hooker_code = f"2{throw}"
    
    match.ball.holder = hooker_code
    match.ball.location = (bx, by, 0.0)
    match.ball.set_action("lineout_forming")


    # For now always target jersey 4 of the throwing team
    match.lineout_target = f"4{throw}"


def handle_forming(match, state_tuple) -> None:
   
    
    """Execute the throw to the jumper and deliver to the scrum‑half."""
    """Execute the throw to the jumper and deliver to the scrum‑half."""
    throw = _team_possession(match)
    hooker_code = f"2{throw}"
    jumper_code = getattr(match, "lineout_target", f"4{throw}")
    sh_code = f"9{throw}"

    hooker = match.get_player_by_code(hooker_code)
    jumper = match.get_player_by_code(jumper_code)
    sh = match.get_player_by_code(sh_code)

    if hooker and jumper:
        hx, hy, _ = hooker.location
        jx, jy, _ = jumper.location
        catch_point = (hx, jy, 2.0)
        do_action(match, hooker_code, ("throw", None), hooker.location, catch_point)
        if sh:
            do_action(match, jumper_code, ("deliver", None), catch_point, sh.location)

    match.ball.set_action("lineout_over")


def handle_over(match, state_tuple) -> None:
  
    """Have the scrum‑half catch the delivered ball before play continues."""
    team = _team_possession(match)
    sh_code = f"9{team}"
    sh = match.get_player_by_code(sh_code)

    if sh:
        # The jumper has delivered the ball down; the scrum‑half must still catch it
        do_action(match, sh_code, ("catch", None), match.ball.location, sh.location)

    match.ball.set_action("lineout_out")


def handle_out(match, state_tuple) -> None:
   
    """Simple first pass from the scrum‑half to the fly‑half."""
    team = _team_possession(match)
    sh_code = f"9{team}"
    ten_code = f"10{team}"
    sh = match.get_player_by_code(sh_code)
    ten = match.get_player_by_code(ten_code)

    if sh and ten:
        do_action(match, sh_code, ("pass", None), sh.location, ten.location)
