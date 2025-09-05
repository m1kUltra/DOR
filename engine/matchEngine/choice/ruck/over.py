# engine/matchEngine/choice/ruck/over.py
from typing import List, Tuple, Optional
from utils.positioning.mental.phase import phase_attack_targets, phase_defence_targets
from utils.player.dh_assign import assign_dh_for_over

DoCall = Tuple[str, Tuple[str, Optional[str]], Tuple[float,float,float], Tuple[float,float,float]]

READY_DIST = 5.0
READY_D2   = READY_DIST * READY_DIST

def _xyz(p): return tuple(p) if isinstance(p,(list,tuple)) else (0.0,0.0,0.0)
def _d2(a,b): dx,dy=a[0]-b[0],a[1]-b[1]; return dx*dx+dy*dy

def _wait_limit_ticks(match) -> int:
    # 5s; try to read engine tick rate if available, else assume 20Hz
    tps = getattr(match, "ticks_per_second", 5)
    return int(5 * max(1, tps))

def _team_ready(match, atk: str, base_xy, dh_id: Optional[str]) -> bool:
    bx, by = base_xy
    targets = phase_attack_targets(match, atk, (bx, by))
    ready = 0
    total = 0
    for p in match.players:
        if p.team_code != atk: 
            continue
        if p.state_flags.get("in_ruck", False):
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
    # 10/15 in place (or 2/3 of available non-ruck, non-DH players)
    return (ready >= 10) or (total and ready / total >= 0.66)

def plan(match, state_tuple) -> List[DoCall]:
    bx, by, _ = _xyz(getattr(match.ball, "location", None))
    base_xy = (bx, by)
    atk = getattr(match, "possession", "a")
    deff = "b" if atk == "a" else "a"

    # ensure a DH according to your rules
    dh_id = assign_dh_for_over(match, atk, base_xy)

    # init wait counter
    if not hasattr(match, "_ruck_over_wait"):
        match._ruck_over_wait = 0

    calls: List[DoCall] = []

    # players not in ruck: move to phase shapes
    atk_targets = phase_attack_targets(match, atk, base_xy)
    for p in match.players:
        if p.team_code != atk: 
            continue
        if p.state_flags.get("in_ruck", False):
            continue
        pid = f"{p.sn}{p.team_code}"
        if dh_id and pid == dh_id:
            continue
        tgt = atk_targets.get(p)
        if not tgt:
            continue
        calls.append((pid, ("move", None), _xyz(p.location), tgt))

    def_targets = phase_defence_targets(match, deff, base_xy)
    for p in match.players:
        if p.team_code != deff or p.state_flags.get("in_ruck", False):
            continue
        calls.append((f"{p.sn}{p.team_code}", ("move", None), _xyz(p.location), def_targets.get(p, _xyz(p.location))))

    # DH waits until ready or timeout, then PICK
    if dh_id:
        dh = match.get_player_by_code(dh_id)
        px, py, _ = _xyz(dh.location)
        close = _d2((px,py), base_xy) <= (1.5*1.5)
        ready = _team_ready(match, atk, base_xy, dh_id)
        timeout = match._ruck_over_wait >= _wait_limit_ticks(match)

        if not close:
            calls.append((dh_id, ("move", None), (px,py,0.0), match.pitch.clamp_position((bx,by,0.0))))
            match._ruck_over_wait += 1
        else:
            if ready or timeout:
                calls.append((dh_id, ("picked", None), (px,py,0.0), (bx,by,0.0)))
                match._ruck_over_wait = 0
            else:
                # tiny nudge to keep orientation + let others settle
                calls.append((dh_id, ("move", None), (px,py,0.0), match.pitch.clamp_position((bx+0.001,by+0.001,0.0))))
                match._ruck_over_wait += 1

    return calls
