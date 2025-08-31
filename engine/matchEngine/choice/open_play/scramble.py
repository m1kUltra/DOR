from typing import List, Tuple, Optional

Do = Tuple[str, Tuple[str, Optional[str]], tuple, tuple]

def _xyz(p):
    return tuple(p) if isinstance(p, (list, tuple)) else (0.0, 0.0, 0.0)

CATCH_R = 1.0
CATCH_R2 = CATCH_R * CATCH_R
CHASERS_PER_TEAM = 2

def plan(match, state_tuple) -> List[Do]:
  
    bx, by, bz = _xyz(getattr(match.ball, "location", None))
    calls: List[Do] = []

    players = list(getattr(match, "players", []))
    if not players:
        return calls

    # distance^2 to ball helper
    def d2(p):
        return (p.location[0] - bx) ** 2 + (p.location[1] - by) ** 2

    # 1) If no holder, award immediate catch to the closest player within 1m
    if getattr(match.ball, "holder", None) is None:
        within = [(d2(p), p) for p in players if d2(p) <= CATCH_R2]
        if within:
            within.sort(key=lambda t: t[0])  # shortest distance wins
            _, winner = within[0]
            pid = f"{winner.sn}{winner.team_code}"
            calls.append((pid, ("catch", None), _xyz(winner.location), (bx, by, 0.0)))
            # We still let others move below (optional), but holder will be set by the action system.
            # You can early-return here if you prefer a single action:
            # return calls

    # 2) Send nearest N per team to contest/chase the ball
    by_team = {"a": [], "b": []}
    for p in players:
        code = getattr(p, "team_code", "a")
        by_team.setdefault(code, []).append(p)

    for code, group in by_team.items():
        group.sort(key=d2)
        for p in group[:CHASERS_PER_TEAM]:
            pid = f"{p.sn}{p.team_code}"
            calls.append((pid, ("move", None), _xyz(p.location), match.pitch.clamp_position((bx, by, 0.0))))

    # (Optional) You could add a light “ring” or hold behavior for everyone else later.

    return calls
