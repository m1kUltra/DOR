# matchEngine/choice/individual/locked_defender_choices.py
from typing import Optional, Tuple
import math
from constants import TACKLE_RANGE

XYZ    = Tuple[float, float, float]
Action = Tuple[str, Optional[str]]   # ("contact","tackle") or ("move", None)

def _xyz(p) -> XYZ:
    if p is None: return (0.0, 0.0, 0.0)
    if isinstance(p, (list, tuple)):
        if len(p) == 2: return (float(p[0]), float(p[1]), 0.0)
        if len(p) >= 3: return (float(p[0]), float(p[1]), float(p[2]))
    return (0.0, 0.0, 0.0)

def choose(match, locked_id: str, state_tuple) -> Tuple[Optional[Action], Optional[XYZ]]:
    """
    Locked defender behaviour:
      - If close enough to the ball holder -> tackle
      - Else -> move to the holder's current position
    """
    defender = match.get_player_by_code(locked_id)
    if not defender:
        return (None, None)

    holder_id = getattr(match.ball, "holder", None)
    # If no holder (loose ball), chase the live ball instead
    if not holder_id:
        bx, by, _ = _xyz(getattr(match.ball, "location", None))
        return (("move", None), match.pitch.clamp_position((bx, by, 0.0)))

    holder = match.get_player_by_code(holder_id)
    if not holder:
        bx, by, _ = _xyz(getattr(match.ball, "location", None))
        return (("move", None), match.pitch.clamp_position((bx, by, 0.0)))

    # If somehow same team, don't tackle; just move toward ball to avoid weirdness
    if holder.team_code == defender.team_code:
        hx, hy, _ = _xyz(holder.location)
        return (("move", None), match.pitch.clamp_position((hx, hy, 0.0)))

    dx = holder.location[0] - defender.location[0]
    dy = holder.location[1] - defender.location[1]
    dist = math.hypot(dx, dy)

    radius = float(getattr(match, "tackle_radius", TACKLE_RANGE))

    if dist <= radius:
        # Tackle at the holder’s current spot (z=0); action_controller routes "contact" -> enter_contact
        hx, hy, _ = _xyz(holder.location)
        return (("tackle",None), (hx, hy, 0.0))

    # Otherwise, close the distance
    hx, hy, _ = _xyz(holder.location)
    return (("move", None), (hx, hy, 0.0))
