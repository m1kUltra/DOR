from typing import List, Tuple, Optional
from utils.positioning.mental.phase import phase_attack_targets, phase_defence_targets

Do = Tuple[str, Tuple[str, Optional[str]], tuple, tuple]
def _xyz(p): return tuple(p) if isinstance(p,(list,tuple)) else (0.0,0.0,0.0)

def plan(match, state_tuple) -> List[Do]:
    tag, _loc, _ctx = state_tuple
    bx, by, _ = _xyz(getattr(match.ball, "location", None))
    atk = getattr(match, "possession", "a")
    deff = "b" if atk == "a" else "a"

    calls: List[Do] = []

    # non-holders (not in ruck) → phase shapes
    atk_targets = phase_attack_targets(match, atk, (bx, by))
    for p in match.players:
        if p.team_code != atk: continue
        if p.state_flags.get("in_ruck", False): continue
        pid = f"{p.sn}{p.team_code}"
        if getattr(match.ball, "holder", None) == pid: continue
        tgt = atk_targets.get(p)
        if tgt: calls.append((pid, ("move", None), _xyz(p.location), tgt))

    def_targets = phase_defence_targets(match, deff, (bx, by))
    for p in match.players:
        if p.team_code != deff: continue
        if p.state_flags.get("in_ruck", False): continue
        pid = f"{p.sn}{p.team_code}"
        tgt = def_targets.get(p)
        if tgt: calls.append((pid, ("move", None), _xyz(p.location), tgt))

    return calls
