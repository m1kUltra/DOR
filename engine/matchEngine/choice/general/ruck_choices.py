# matchEngine/choice/general/ruck_choices.py
from typing import List, Tuple, Optional

XYZ    = Tuple[float, float, float]
Action = Tuple[str, Optional[str]]
DoCall = Tuple[str, Action, XYZ, XYZ]

def _xyz(p) -> XYZ:
    if p is None: return (0.0, 0.0, 0.0)
    if isinstance(p, (list, tuple)):
        if len(p) == 2: return (float(p[0]), float(p[1]), 0.0)
        if len(p) >= 3: return (float(p[0]), float(p[1]), float(p[2]))
    return (0.0, 0.0, 0.0)

def plan(match, state_tuple) -> List[DoCall]:
    """
    Very light ruck logic:
      - find ruck center (from match.ruck_meta or ball)
      - nearest 2 attackers: move to ruck and 'clearout' (bind)
      - nearest 1 defender: move to ruck and 'jackal' (bind)
      - everyone else: hold position (no calls)
    """
    tag, _loc, _ctx = state_tuple
    meta = getattr(match, "ruck_meta", None)
    rx = float(meta["x"]) if meta else float(getattr(match.ball, "location", (0,0,0))[0])
    ry = float(meta["y"]) if meta else float(getattr(match.ball, "location", (0,0,0))[1])

    atk = (meta["atk"] if meta else _infer_atk(match))
    deff = "b" if atk == "a" else "a"

    def _near(team_code):
        ps = [p for p in match.players if getattr(p, "team_code", None) == team_code]
        ps.sort(key=lambda p: (p.location[0]-rx)**2 + (p.location[1]-ry)**2)
        return ps

    atk_near = _near(atk)[:2]
    def_near = _near(deff)[:1]

    calls: List[DoCall] = []
    for p in atk_near:
        calls.append((f"{p.sn}{p.team_code}", ("move", None), _xyz(p.location), match.pitch.clamp_position((rx, ry, 0.0))))
        calls.append((f"{p.sn}{p.team_code}", ("clearout", None), _xyz(p.location), (rx, ry, 0.0)))

    for p in def_near:
        calls.append((f"{p.sn}{p.team_code}", ("move", None), _xyz(p.location), match.pitch.clamp_position((rx, ry, 0.0))))
        calls.append((f"{p.sn}{p.team_code}", ("jackal", None), _xyz(p.location), (rx, ry, 0.0)))

    return calls

def _infer_atk(match) -> str:
    if getattr(match.team_a, "in_possession", False): return "a"
    if getattr(match.team_b, "in_possession", False): return "b"
    hid = getattr(match.ball, "holder", None)
    return (hid[-1] if isinstance(hid, str) and hid else "a")
