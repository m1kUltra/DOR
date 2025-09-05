# choice/ruck/start.py
from typing import List, Tuple, Optional
DoCall = Tuple[str, Tuple[str, Optional[str]], Tuple[float,float,float], Tuple[float,float,float]]

def _xyz(p): 
    return tuple(p) if isinstance(p,(list,tuple)) else (0.0,0.0,0.0)

def plan(match, state_tuple) -> List[DoCall]:
    bx, by, _ = _xyz(getattr(match.ball, "location", None))
    atk = getattr(match, "possession", "a")
    deff = "b" if atk == "a" else "a"

    def nearest(code, n):
        ps = [p for p in match.players if p.team_code == code]
        ps.sort(key=lambda p:(p.location[0]-bx)**2 + (p.location[1]-by)**2)
        return ps[:n]

    calls: List[DoCall] = []
    for p in nearest(atk, 2):
        calls.append((f"{p.sn}{p.team_code}", ("move", None), _xyz(p.location), match.pitch.clamp_position((bx, by, 0.0))))
    for p in nearest(deff, 1):
        calls.append((f"{p.sn}{p.team_code}", ("move", None), _xyz(p.location), match.pitch.clamp_position((bx, by, 0.0))))
    return calls
