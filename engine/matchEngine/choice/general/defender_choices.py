# matchEngine/choice/general/defender_choices.py
from typing import List, Tuple, Optional
from states.open_play import OPEN_PLAY_TAGS  # (gated upstream; ok to keep)

XYZ    = Tuple[float, float, float]
Action = Tuple[str, Optional[str]]
DoCall = Tuple[str, Action, XYZ, XYZ]   # (player_id, action, location, target)

def _xyz(p) -> XYZ:
    if p is None: return (0.0, 0.0, 0.0)
    if isinstance(p, (list, tuple)):
        if len(p) == 2: return (float(p[0]), float(p[1]), 0.0)
        if len(p) >= 3: return (float(p[0]), float(p[1]), float(p[2]))
    return (0.0, 0.0, 0.0)

def plan(match, state_tuple) -> List[DoCall]:
    """
    Minimal defence:
      - Take team NOT in possession (fallback: infer from ball.holder)
      - Build a flat line depth in front of ball.x, centered on ball.y
      - Use defending team's tactics: def_line_depth, def_spacing_infield
    """
    tag, _loc, _ctx = state_tuple

    # --- Who is attacking? ---
    atk_team = match.team_a if getattr(match.team_a, "in_possession", False) \
        else (match.team_b if getattr(match.team_b, "in_possession", False) else None)

    # Fallback: infer from holder code like "10a"/"15b"
    if atk_team is None:
        hid = getattr(match.ball, "holder", None)
        if isinstance(hid, str) and hid:
            atk_team = match.team_a if hid.endswith("a") else match.team_b

    if atk_team is None:
        return []

    # --- Defending side + params ---
    def_team = match.team_b if atk_team is match.team_a else match.team_a
    def_code = "b" if def_team is match.team_b else "a"

    bx, by, _ = _xyz(getattr(match.ball, "location", None))
    atk_tac = (getattr(atk_team, "tactics", None) or {})
    def_tac = (getattr(def_team, "tactics", None) or {})

    attack_dir = float(atk_tac.get("attack_dir", +1.0))
    line_depth = float(def_tac.get("def_line_depth", 1.0))
    gap        = float(def_tac.get("def_spacing_infield", 3.0))

    # Defence line in front of the ball toward the attackers
    line_x = bx + attack_dir * line_depth

    # --- Eligible defenders ---
    def _eligible(p) -> bool:
        if p.team_code != def_code: return False
        sf = p.state_flags
        if sf.get("locked_defender", False): return False
        if sf.get("tackling", False) or sf.get("being_tackled", False): return False
        return True

    defenders = [p for p in match.players if _eligible(p)]
    if not defenders:
        return []

    defenders.sort(key=lambda p: p.rn)
    n = len(defenders)

    # --- Targets spaced symmetrically around ball.y ---
    calls: List[DoCall] = []
    for i, p in enumerate(defenders):
        offset = (i - (n - 1) / 2.0) * gap  # ..., -2g, -g, 0, +g, +2g, ...
        tx, ty, tz = line_x, by + offset, 0.0
        target = match.pitch.clamp_position((tx, ty, tz))
        calls.append((f"{p.sn}{p.team_code}", ("move", None), _xyz(p.location), target))

    return calls
