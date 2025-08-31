# choice/ruck/out.py
"""all this is the state wher the 9 picks the ball but before they pass it 
allows the nine to pass without getti ng insta hit or effected by open_play logiuc """
# engine/matchEngine/choice/ruck/out.py
from typing import List, Tuple, Optional
from utils.positioning.mental.phase import phase_attack_targets, phase_defence_targets

DoCall = Tuple[str, Tuple[str, Optional[str]], Tuple[float,float,float], Tuple[float,float,float]]
READY_DIST = 5.0
READY_D2   = READY_DIST * READY_DIST

def _xyz(p): return tuple(p) if isinstance(p,(list,tuple)) else (0.0,0.0,0.0)
def _d2(a,b): dx,dy=a[0]-b[0],a[1]-b[1]; return dx*dx+dy*dy
def _wait_limit_ticks(match) -> int:
    tps = getattr(match, "ticks_per_second", 20)
    return int(5 * max(1, tps))

def _team_ready(match, atk: str, base_xy, dh_id: Optional[str]) -> bool:
    bx, by = base_xy
    targets = phase_attack_targets(match, atk, (bx, by))
    ready = total = 0
    for p in match.players:
        if p.team_code != atk or p.state_flags.get("in_ruck", False):
            continue
        pid = f"{p.sn}{p.team_code}"
        if dh_id and pid == dh_id:
            continue
        tgt = targets.get(p)
        if not tgt:
            continue
        total += 1
        if _d2((p.location[0],p.location[1]), (tgt[0],tgt[1])) <= READY_D2:
            ready += 1
    return (ready >= 10) or (total and ready/total >= 0.66)

def _current_dh_id(match) -> Optional[str]:
    for p in match.players:
        if p.state_flags.get("dummy_half"): 
            return f"{p.sn}{p.team_code}"
    return None

def _choose_receiver(match, atk: str, dh_id: str):
    # prefer flagged first_receiver, else nearest eligible attacker
    dh = match.get_player_by_code(dh_id)
    dx, dy, _ = _xyz(dh.location)
    best = None
    best_d2 = 1e9
    for p in match.players:
        if p.team_code != atk or p.state_flags.get("in_ruck", False):
            continue
        pid = f"{p.sn}{p.team_code}"
        if pid == dh_id:
            continue
        if p.state_flags.get("first_receiver"):
            return p
        d2 = (p.location[0]-dx)**2 + (p.location[1]-dy)**2
        if d2 < best_d2:
            best_d2, best = d2, p
    return best

def plan(match, state_tuple) -> List[DoCall]:
    bx, by, _ = _xyz(getattr(match.ball, "location", None))
    atk = getattr(match, "possession", "a")
    deff = "b" if atk == "a" else "a"
    dh_id = _current_dh_id(match)

    # safety counter
    if not hasattr(match, "_ruck_out_wait"):
        match._ruck_out_wait = 0

    calls: List[DoCall] = []

    # non-ruck players follow shapes
    atk_targets = phase_attack_targets(match, atk, (bx, by))
    for p in match.players:
        if p.team_code != atk or p.state_flags.get("in_ruck", False):
            continue
        pid = f"{p.sn}{p.team_code}"
        if dh_id and pid == dh_id:
            continue
        tgt = atk_targets.get(p)
        if tgt:
            calls.append((pid, ("move", None), _xyz(p.location), tgt))

    def_targets = phase_defence_targets(match, deff, (bx, by))
    for p in match.players:
        if p.team_code != deff or p.state_flags.get("in_ruck", False):
            continue
        tgt = def_targets.get(p)
        if tgt:
            calls.append((f"{p.sn}{p.team_code}", ("move", None), _xyz(p.location), tgt))

    # DH pass gating
    if dh_id and getattr(match.ball, "holder", None) == dh_id:
        ready = _team_ready(match, atk, (bx, by), dh_id)
        timeout = match._ruck_out_wait >= _wait_limit_ticks(match)
        receiver = _choose_receiver(match, atk, dh_id) if (ready or timeout) else None

        if receiver:
            rx, ry, _ = _xyz(receiver.location)
            rid = f"{receiver.sn}{receiver.team_code}"
            dh = match.get_player_by_code(dh_id)
            calls.append((dh_id, ("pass", rid), _xyz(dh.location), (rx, ry, 0.0)))
            match._ruck_out_wait = 0
        else:
            # hold position briefly
            dh = match.get_player_by_code(dh_id)
            px, py, _ = _xyz(dh.location)
            calls.append((dh_id, ("move", None), (px,py,0.0), (bx+0.001,by+0.001,0.0)))
            match._ruck_out_wait += 1
            match._frames_since_ruck = 0

    return calls
