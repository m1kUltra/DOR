# choice/scrum/over.py
"""Scrum over phase: backlines move into exit shapes."""

from typing import List, Tuple, Optional
from utils.positioning.mental.formations import place_backs_exit_shape

DoCall = Tuple[str, Tuple[str, Optional[str]], Tuple[float, float, float], Tuple[float, float, float]]


def _xyz(p):
    return tuple(p) if isinstance(p, (list, tuple)) else (0.0, 0.0, 0.0)


def plan(match, state_tuple) -> List[DoCall]:
    """Placeholder for scrum stability phase."""
    
    bx, by, _ = _xyz(getattr(match.ball, "location", None))
    winner = getattr(match, "possession", "a")
    exit_call = getattr(match, "scrum_exit_call", "8_pick")

    targets = place_backs_exit_shape(exit_call, winner, (bx, by), match)
    calls: List[DoCall] = []
    for p, tgt in targets.items():
        pid = f"{p.sn}{p.team_code}"
        calls.append((pid, ("move", None), _xyz(p.location), match.pitch.clamp_position(tgt)))

    return calls