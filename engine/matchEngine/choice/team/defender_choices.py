# matchEngine/choice/team/defender_choices.py
from typing import List, Tuple, Optional
from states.open_play import OPEN_PLAY_TAGS

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
      - Only in open play
      - Take team NOT in possession
      - Build a flat line depth in front of ball.x, centered on ball.y
      - Use defending team's tactics: def_line_depth, def_spacing_infield
    """
    tag, _loc, _ctx = state_tuple
    if not (isinstance(tag, str) and tag in OPEN_PLAY_TAGS):
        return []

    atk_team = match.team_a if match.team_a.in_possession else (match.team_b if match.team_b.in_possession else None)
    if atk_team is None:
        return []

    def_team = match.team_b if atk_team is match.team_a else match.team_a
    def_code = "b" if def_team is match.team_b else "a"

    # Ball position & attack direction (from the ATTACKING team)
    bx, by, _ = match.ball.location
    attack_dir = float(atk_team.tactics.get("attack_dir", +1.0))

    # Defending team shape params
    line_depth = float(def_team.tactics.get("def_line_depth", 1.0))
    gap        = float(def_team.tactics.get("def_spacing_infield", 3.0))

    # X position of the defence line: in front of the ball toward the attacker
    line_x = bx + attack_dir * line_depth

    # Eligible defenders (not locked/tackling/being_tackled; on defending team)
    def _eligible(p) -> bool:
        if p.team_code != def_code:
            return False
        sf = p.state_flags
        if sf.get("locked_defender", False):
            return False
        if sf.get("tackling", False) or sf.get("being_tackled", False):
            return False
        return True

    defenders = [p for p in match.players if _eligible(p)]
    if not defenders:
        return []

    # Stable ordering (role number) and symmetric lateral slots around ball.y
    defenders.sort(key=lambda p: p.rn)
    n = len(defenders)

    calls: List[DoCall] = []
    for i, p in enumerate(defenders):
        # symmetric offsets: ..., -2g, -1g, 0, +1g, +2g, ...
        offset = (i - (n - 1) / 2.0) * gap
        tx, ty, tz = line_x, by + offset, 0.0
        target = match.pitch.clamp_position((tx, ty, tz))
        calls.append((f"{p.sn}{p.team_code}", ("move", None), _xyz(p.location), target))

    return calls
