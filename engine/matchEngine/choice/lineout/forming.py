"""Lineout forming: execute the throw to the jumper."""

from typing import List, Tuple, Optional

DoCall = Tuple[str, Tuple[str, Optional[str]], Tuple[float, float, float], Tuple[float, float, float]]


def _xyz(p):
    return tuple(p) if isinstance(p, (list, tuple)) else (0.0, 0.0, 0.0)


def plan(match, state_tuple) -> List[DoCall]:
    """Placeholder for jump/contest phase."""
  
    meta = getattr(match, "lineout_meta", {})
    throw = getattr(match, "possession", "a")
    jumper_sn = meta.get("jumper_sn")
    catch_xy = meta.get("catch_xy")
    team = match.team_a if throw == "a" else match.team_b
    hook = team.get_player_by_rn(2)
    jumper = match.get_player_by_code(f"{jumper_sn}{throw}") if jumper_sn else None

    calls: List[DoCall] = []
    if hook and jumper and catch_xy:
        hid = f"{hook.sn}{hook.team_code}"
        jid = f"{jumper.sn}{jumper.team_code}"
        calls.append((hid, ("pass", jid), _xyz(hook.location), catch_xy))

    return calls