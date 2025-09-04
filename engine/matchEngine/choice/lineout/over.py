"""Lineout over: reorganise into phase shapes."""

from typing import List, Tuple, Optional
from utils.positioning.mental.phase import (
    phase_attack_targets,
    phase_defence_targets,
)

DoCall = Tuple[str, Tuple[str, Optional[str]], Tuple[float, float, float], Tuple[float, float, float]]


def _xyz(p):
    return tuple(p) if isinstance(p, (list, tuple)) else (0.0, 0.0, 0.0)


def plan(match, state_tuple) -> List[DoCall]:
    """Placeholder for post-catch organisation."""
 
    meta = getattr(match, "lineout_meta", {})
    bx, by = meta.get("mark", (0.0, 0.0))
    atk = getattr(match, "possession", "a")
    deff = "b" if atk == "a" else "a"

    atk_targets = phase_attack_targets(match, atk, (bx, by))
    def_targets = phase_defence_targets(match, deff, (bx, by))

    calls: List[DoCall] = []
    for p in match.players:
        pid = f"{p.sn}{p.team_code}"
        tgt = atk_targets.get(p) if p.team_code == atk else def_targets.get(p)
        if tgt:
            calls.append((pid, ("move", None), _xyz(p.location), tgt))

    return calls
