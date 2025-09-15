from typing import List, Tuple, Optional

from .phase import plan as phase_plan

Do = Tuple[str, Tuple[str, Optional[str]], tuple, tuple]


def _xyz(p):
    return tuple(p) if isinstance(p, (list, tuple)) else (0.0, 0.0, 0.0)


CATCH_R = 1.0
CATCH_R2 = CATCH_R * CATCH_R
CHASERS_PER_TEAM = 2


def plan(match, state_tuple) -> List[Do]:
    """Contest a loose ball.

    Base behaviour mirrors ``phase.play`` – all non‑chasers follow their
    normal phase targets.  In addition, the nearest two players from each team
    sprint to the ball and, if close enough, attempt an immediate catch.
    """

    bx, by, bz = _xyz(getattr(match.ball, "location", None))

    # Start from standard phase behaviour
    calls: List[Do] = list(phase_plan(match, state_tuple) or [])

    players = list(getattr(match, "players", []))
    if not players:
        return calls

    def d2(p):
        return (p.location[0] - bx) ** 2 + (p.location[1] - by) ** 2

    catcher_id: Optional[str] = None
    if getattr(match.ball, "holder", None) is None:
        within = [(d2(p), p) for p in players if d2(p) <= CATCH_R2]
        if within:
            within.sort(key=lambda t: t[0])
            _, winner = within[0]
            catcher_id = f"{winner.sn}{winner.team_code}"
            calls = [c for c in calls if c[0] != catcher_id]
            calls.append((catcher_id, ("catch", None), _xyz(winner.location), (bx, by, bz)))

    by_team = {"a": [], "b": []}
    for p in players:
        code = getattr(p, "team_code", "a")
        by_team.setdefault(code, []).append(p)

    for code, group in by_team.items():
        group.sort(key=d2)
        for p in group[:CHASERS_PER_TEAM]:
            pid = f"{p.sn}{p.team_code}"
            if pid == catcher_id:
                continue
            calls = [c for c in calls if c[0] != pid]
            calls.append((pid, ("move", None), _xyz(p.location), match.pitch.clamp_position((bx, by, bz))))

    return calls