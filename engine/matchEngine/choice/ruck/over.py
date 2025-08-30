# choice/ruck/over.py
from typing import List, Tuple, Optional
from utils.player.dh_assign import assign_dummy_half
from utils.positioning.mental.phase import phase_attack_targets, phase_defence_targets


DoCall = Tuple[str, Tuple[str, Optional[str]], Tuple[float,float,float], Tuple[float,float,float]]
def _xyz(p): return tuple(p) if isinstance(p,(list,tuple)) else (0.0,0.0,0.0)

def plan(match, state_tuple) -> List[DoCall]:
    bx, by, _ = _xyz(getattr(match.ball, "location", None))
    atk = getattr(match, "possession", "a")
    deff = "b" if atk == "a" else "a"

    # 1) mark in-ruck (<=2.5m) & clear old flags
    for p in match.players:
        sf = p.state_flags
        
        # keep any existing tackling flags as your pipeline sets them
        dx, dy = p.location[0]-bx, p.location[1]-by
        sf["in_ruck"] = (dx*dx + dy*dy) <= (2.5*2.5)

    calls: List[DoCall] = []

    # 2) assign DH (9 or fallback)
    
        # 2) assign DH (9 or fallback) only if no dummy_half already assigned
    if not any(p.state_flags.get("dummy_half") for p in match.players):
        dh_id = assign_dummy_half(match, atk, near_xy=(bx, by))
    

  

    # 3) DH: pick up if close, else move to base
    if dh_id:
        p = match.get_player_by_code(dh_id)
        px, py, _ = _xyz(p.location)
        if (px-bx)**2 + (py-by)**2 <= (1.5*1.5):
            calls.append((dh_id, ("catch", None), (px, py, 0.0), (bx, by, 0.0)))
            ball.holder=dh_id
        else:
            calls.append((dh_id, ("move", None), (px, py, 0.0), match.pitch.clamp_position((bx, by, 0.0))))

    # 4) Attack phase shape (non-ruck, non-DH)
    atk_targets = phase_attack_targets(match, atk, (bx, by))
    for p in match.players:
        pid = f"{p.sn}{p.team_code}"
        if p.team_code != atk: continue
        if p.state_flags.get("in_ruck", False): continue
        if dh_id and pid == dh_id: continue
        tgt = atk_targets.get(p)
        if not tgt: continue
        calls.append((pid, ("move", None), _xyz(p.location), tgt))

    # 5) (Optional) Defence line
    def_targets = phase_defence_targets(match, deff, (bx, by))
    for p in match.players:
        if p.team_code != deff: continue
        if p.state_flags.get("in_ruck", False): continue
        tgt = def_targets.get(p)
        if not tgt: continue
        calls.append((f"{p.sn}{p.team_code}", ("move", None), _xyz(p.location), tgt))

    return calls
