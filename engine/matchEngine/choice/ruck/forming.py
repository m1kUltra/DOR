# choice/ruck/forming.py
from typing import List, Tuple, Optional
DoCall = Tuple[str, Tuple[str, Optional[str]], Tuple[float,float,float], Tuple[float,float,float]]


def _xyz(p): 
    return tuple(p) if isinstance(p,(list,tuple)) else (0.0,0.0,0.0)

def plan(match, state_tuple) -> List[DoCall]:
    bx, by, _ = _xyz(getattr(match.ball, "location", None))

    calls: List[DoCall] = []
   
    # nudge any nearby players (<6m) to close to 2m
    for p in match.players:
        sf = p.state_flags
        sf["dummy_half"] = False
        sf["first_receiver"] = False
        dx, dy = p.location[0]-bx, p.location[1]-by
        if dx*dx + dy*dy <= 36.0:
            tx = bx + (0.001 if dx==0 else 0.0)
            ty = by + (0.001 if dy==0 else 0.0)
            calls.append((f"{p.sn}{p.team_code}", ("move", None), _xyz(p.location), match.pitch.clamp_position((tx, ty, 0.0))))
    return calls
