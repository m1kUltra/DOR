"""State where 9 picks the ball from a scrum but, before passing,
we protect the sequence from open_play logic and instant pressure.
Mirrors ruck/out but for scrums.
"""

from typing import List, Tuple, Optional
from utils.positioning.mental.phase import phase_attack_targets, phase_defence_targets
import math
DoCall = Tuple[str, Tuple[str, Optional[str]], Tuple[float,float,float], Tuple[float,float,float]]
READY_DIST = 5.0
READY_D2   = READY_DIST * READY_DIST
PRESENT_HOLD_TICKS = 18  # ~0.9s @ 20Hz; tweak to taste

def _xyz(p): 
    return tuple(p) if isinstance(p,(list,tuple)) else (0.0,0.0,0.0)

def _d2(a,b): 
    dx,dy=a[0]-b[0],a[1]-b[1]; 
    return dx*dx+dy*dy

def _wait_limit_ticks(match) -> int:
    tps = getattr(match, "ticks_per_second", 20)
    return int(5 * max(1, tps))

def _clear_first_receiver_flags(match, team_code: str):
    for p in match.players:
        if p.team_code == team_code:
            p.state_flags.pop("first_receiver", None)
            p.state_flags.pop("hold_for_pass", None)

def _assign_first_receiver(match, atk: str, dh_id: str, base_xy) -> Optional[object]:
    """Prefer 10, else 12, 13, 15, else nearest attacker not DH/in_scrum."""
    bx, by = base_xy
    team = match.team_a if atk == "a" else match.team_b

    _clear_first_receiver_flags(match, atk)

    for rn in (10, 12, 13, 15):
        p = team.get_player_by_rn(rn)
        if not p: 
            continue
        pid = f"{p.sn}{p.team_code}"
        if pid == dh_id: 
            continue
        if p.state_flags.get("in_scrum", False): 
            continue
        p.state_flags["first_receiver"] = True
        p.state_flags["hold_for_pass"] = PRESENT_HOLD_TICKS
        return p

    # fallback: nearest eligible attacker
    cand = [p for p in match.players 
            if p.team_code == atk 
            and f"{p.sn}{p.team_code}" != dh_id
            and not p.state_flags.get("in_scrum", False)]
    if not cand:
        return None
    cand.sort(key=lambda p:(p.location[0]-bx)**2+(p.location[1]-by)**2)
    r = cand[0]
    r.state_flags["first_receiver"] = True
    r.state_flags["hold_for_pass"] = PRESENT_HOLD_TICKS
    return r

def _team_ready(match, atk: str, base_xy, dh_id: Optional[str]) -> bool:
    bx, by = base_xy
    targets = phase_attack_targets(match, atk, (bx, by))
    ready = total = 0
    for p in match.players:
        if p.team_code != atk or p.state_flags.get("in_scrum", False):
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
    dh = match.get_player_by_code(dh_id)
    dx, dy, _ = _xyz(dh.location)
    best = None
    best_d2 = 1e9
    for p in match.players:
        if p.team_code != atk or p.state_flags.get("in_scrum", False):
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

    if not hasattr(match, "_scrum_out_wait"):
        match._scrum_out_wait = 0

    calls: List[DoCall] = []

    # attackers not in scrum → shapes
    atk_targets = phase_attack_targets(match, atk, (bx, by))
    for p in match.players:
        if p.team_code != atk or p.state_flags.get("in_scrum", False):
            continue
        pid = f"{p.sn}{p.team_code}"
        if dh_id and pid == dh_id:
            continue
        tgt = atk_targets.get(p)
        if tgt:
            calls.append((pid, ("move", None), _xyz(p.location), tgt))

    # defenders not in scrum → shapes
    def_targets = phase_defence_targets(match, deff, (bx, by))
    for p in match.players:
        if p.team_code != deff or p.state_flags.get("in_scrum", False):
            continue
        tgt = def_targets.get(p)
        if tgt:
            calls.append((f"{p.sn}{p.team_code}", ("move", None), _xyz(p.location), tgt))

    # DH gating
    receiver = _assign_first_receiver(match, atk, dh_id, (bx, by))
    if dh_id and getattr(match.ball, "holder", None) == dh_id:
        ready = _team_ready(match, atk, (bx, by), dh_id)
        timeout = match._scrum_out_wait >= _wait_limit_ticks(match)
        receiver = _choose_receiver(match, atk, dh_id) if (ready or timeout) else None

        if receiver:
            rx, ry, rz = _xyz(receiver.location)
            
            dh = match.get_player_by_code(dh_id)
            px, py, pz = _xyz(dh.location)
            dist = math.hypot(rx - px, ry - py)
           
            tz = rz if rz else 1.0
            
            calls.append((dh_id, ("pass", "spin"), (px, py, pz), (rx, ry, tz)))
        else:
            dh = match.get_player_by_code(dh_id)
            px, py, _ = _xyz(dh.location)
            calls.append((dh_id, ("move", None), (px,py,0.0), (bx+0.001,by+0.001,0.0)))
            match._scrum_out_wait += 1
            match._frames_since_ruck = 0

    # clear scrum flags once out logic runs
    for p in match.players:
        p.state_flags["in_scrum"] = False

    return calls
