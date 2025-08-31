from typing import List, Tuple, Optional
Do = Tuple[str, Tuple[str, Optional[str]], tuple, tuple]
def _xyz(p): return tuple(p) if isinstance(p,(list,tuple)) else (0.0,0.0,0.0)

R2 = 2.0*2.0  # 2m “contest bubble”
def plan(match, state_tuple) -> List[Do]:
    print("scramble")
    bx, by, bz = _xyz(getattr(match.ball, "location", None))
    calls: List[Do] = []
    # nearest 2 per team crash toward ball; everyone else holds recent targets (phase/kick planners will take over after regather)
    near = sorted(match.players, key=lambda p:(p.location[0]-bx)**2 + (p.location[1]-by)**2)
    take = near[:4]  # 2+2-ish
    for p in take:
        pid = f"{p.sn}{p.team_code}"
        calls.append((pid, ("move", None), _xyz(p.location), match.pitch.clamp_position((bx, by, 0.0))))
    # quick auto-catch if on top of it
    for p in near[:6]:
        d2 = (p.location[0]-bx)**2 + (p.location[1]-by)**2
        if d2 <= R2 and getattr(match.ball, "holder", None) is None:
            pid = f"{p.sn}{p.team_code}"
            calls.append((pid, ("catch", None), _xyz(p.location), (bx, by, 0.0)))
            break
    return calls
