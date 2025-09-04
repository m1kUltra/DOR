# choice/lineout/out.py


from typing import List, Tuple, Optional

DoCall = Tuple[str, Tuple[str, Optional[str]], Tuple[float, float, float], Tuple[float, float, float]]


def _xyz(p):
    return tuple(p) if isinstance(p, (list, tuple)) else (0.0, 0.0, 0.0)


def plan(match, state_tuple) -> List[DoCall]:
    """Placeholder for ball leaving the lineout."""
  
    meta = getattr(match, "lineout_meta", {})
    atk = getattr(match, "possession", "a")
    jumper_sn = meta.get("jumper_sn")
    jumper = match.get_player_by_code(f"{jumper_sn}{atk}") if jumper_sn else None
    team = match.team_a if atk == "a" else match.team_b
    nine = team.get_player_by_rn(9)

    calls: List[DoCall] = []
    if jumper and nine:
        jid = f"{jumper.sn}{jumper.team_code}"
        nid = f"{nine.sn}{nine.team_code}"
        calls.append((jid, ("pass", nid), _xyz(jumper.location), _xyz(nine.location)))

    return calls