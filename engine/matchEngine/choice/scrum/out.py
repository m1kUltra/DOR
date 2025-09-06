"""Scrum exit decisions: run or pass."""
from typing import List, Tuple, Optional

XYZ = Tuple[float, float, float]
Action = Tuple[str, Optional[str]]
DoCall = Tuple[str, Action, XYZ, XYZ]


def _xyz(p) -> XYZ:
    if p is None:
        return (0.0, 0.0, 0.0)
    if isinstance(p, (list, tuple)):
        if len(p) == 2:
            return (float(p[0]), float(p[1]), 0.0)
        if len(p) >= 3:
            return (float(p[0]), float(p[1]), float(p[2]))
    return (0.0, 0.0, 0.0)


def plan(match, state_tuple, decision: str) -> List[DoCall]:
    """Return action calls for a scrum-out decision.

    Args:
        match:   Match object.
        state_tuple: (tag, loc, ctx) state triple. Only handled when tag is
            ``"scrum.out"``.
        decision: "run" or "pass".
    """
    tag, _loc, _ctx = state_tuple
    if tag != "scrum.out":
        return []

    atk = getattr(match, "possession", "a")
    team = match.team_a if atk == "a" else match.team_b
    calls: List[DoCall] = []
    decision = (decision or "").lower()

    if decision == "run":
        eight = team.get_player_by_rn(8)
        if eight:
            pid = f"{eight.sn}{eight.team_code}"
            t = getattr(team, "tactics", {}) or {}
            attack_dir = float(t.get("attack_dir", +1.0))
            dest = match.pitch.clamp_position((
                eight.location[0] + attack_dir * 1.0,
                eight.location[1],
                0.0,
            ))
            calls.append((pid, ("pick_and_go", None), _xyz(eight.location), _xyz(dest)))
    elif decision == "pass":
        nine = team.get_player_by_rn(9)
        ten = team.get_player_by_rn(10)
        if nine and ten:
            nid = f"{nine.sn}{nine.team_code}"
            tid = f"{ten.sn}{ten.team_code}"
            calls.append((nid, ("pass", tid), _xyz(nine.location), _xyz(ten.location)))
             

    return calls