# choice/lineout/start.py
"""Lineout start: organise both teams for the throw."""

from typing import List, Tuple, Optional
from shapes.lineouts.five_man import 

DoCall = Tuple[str, Tuple[str, Optional[str]], Tuple[float, float, float], Tuple[float, float, float]]


def _xyz(p):
    return tuple(p) if isinstance(p, (list, tuple)) else (0.0, 0.0, 0.0)


def plan(match, state_tuple) -> List[DoCall]:
    """Placeholder for lineout throw setup."""

    bx, by, _ = _xyz(getattr(match.ball, "location", None))
    throw = getattr(match, "possession", "a")
    call = getattr(match, "lineout_call", {"numbers": 5})

    layout = get_lineout_formation((bx, by), throw, call, match)
    atk_targets = layout.get("targets", {})
    meta = {"type": "lineout", "mark": (bx, by), **layout.get("meta", {})}
    match.lineout_meta = meta

    def_team = match.team_b if throw == "a" else match.team_a
    def_targets = place_defensive_setpiece(def_team, meta, match)

    calls: List[DoCall] = []
    all_targets = {**atk_targets, **def_targets}
    for p, tgt in all_targets.items():
        pid = f"{p.sn}{p.team_code}"
        calls.append((pid, ("move", None), _xyz(p.location), match.pitch.clamp_position(tgt)))

    return calls