# choice/lineout/start.py
# engine/matchEngine/choice/lineout/start.py
"""Lineout start: organise both teams for the throw."""

from typing import List, Tuple, Optional

from shapes.five_man import generate_five_man_lineout_shape
from utils.positioning.mental.formations import local_to_world, nearest_role
from utils.positioning.mental.phase import phase_attack_targets, phase_defence_targets

DoCall = Tuple[str, Tuple[str, Optional[str]], Tuple[float, float, float], Tuple[float, float, float]]


def _xyz(p):
    return tuple(p) if isinstance(p, (list, tuple)) else (0.0, 0.0, 0.0)


def plan(match, state_tuple) -> List[DoCall]:
  
    """Organise both teams into a simple five-man lineout shape."""

    bx, by, _ = _xyz(getattr(match.ball, "location", None))
    mark_xy = (bx, by)
    throw = getattr(match, "possession", "a")
    

    atk_team = match.team_a if throw == "a" else match.team_b
    def_team = match.team_b if throw == "a" else match.team_a
    
    atk_dir = float(atk_team.tactics.get("attack_dir", +1.0))
    def_dir = float(def_team.tactics.get("attack_dir", -1.0))

    layout = generate_five_man_lineout_shape()
    atk_layout = layout["team_a"] if throw == "a" else layout["team_b"]
    def_layout = layout["team_b"] if throw == "a" else layout["team_a"]

    calls: List[DoCall] = []
    
    # Position attacking forwards and hooker
    for rn, (lx, ly) in atk_layout.items():
        p = nearest_role(atk_team, rn)
        if not p:
            continue
        wx, wy = local_to_world(lx, ly, mark_xy, atk_dir)
        pid = f"{p.sn}{p.team_code}"
       
        calls.append((pid, ("move", None), _xyz(p.location), (wx, wy, 0.0)))
        p.state_flags["in_lineout"] = True

    # Position defensive forwards
    for rn, (lx, ly) in def_layout.items():
        p = nearest_role(def_team, rn)
        if not p:
            continue
        wx, wy = local_to_world(lx, ly, mark_xy, def_dir)
        pid = f"{p.sn}{p.team_code}"
        calls.append((pid, ("move", None), _xyz(p.location), (wx, wy, 0.0)))
        p.state_flags["in_lineout"] = True

    # Mark 9s as part of the lineout but position all non-participants using phase shapes
    for team in (atk_team, def_team):
        nine = team.get_player_by_rn(9)
        if nine:
            nine.state_flags["in_lineout"] = True

    atk_phase = phase_attack_targets(match, throw, mark_xy)
    def_phase = phase_defence_targets(match, "b" if throw == "a" else "a", mark_xy)

    for p, tgt in atk_phase.items():
        if p.state_flags.get("in_lineout"):
            continue
        pid = f"{p.sn}{p.team_code}"
        calls.append((pid, ("move", None), _xyz(p.location), tgt))

    for p, tgt in def_phase.items():
        if p.state_flags.get("in_lineout"):
            continue
        pid = f"{p.sn}{p.team_code}"
        calls.append((pid, ("move", None), _xyz(p.location), tgt))

    match.lineout_meta = {"type": "lineout", "mark": mark_xy}

    return calls
   