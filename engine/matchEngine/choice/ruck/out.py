# choice/ruck/over.py
from typing import List, Tuple, Optional
from utils.player.dh_assign import assign_dummy_half
from utils.positioning.mental.phase import phase_attack_targets, phase_defence_targets

DoCall = Tuple[str, Tuple[str, Optional[str]], Tuple[float,float,float], Tuple[float,float,float]]
def _xyz(p): return tuple(p) if isinstance(p,(list,tuple)) else (0.0,0.0,0.0)

def _current_dh_id(match) -> Optional[str]:
    for p in match.players:
        if p.state_flags.get("dummy_half"):
            return f"{p.sn}{p.team_code}"
    return None

def _choose_receiver(match, atk: str, dh_id: str):
    """Prefer a flagged first-receiver; else nearest eligible attacker."""
    # Try flagged 1st receiver
    for p in match.players:
        if p.team_code != atk: 
            continue
        if p.state_flags.get("in_ruck", False):
            continue
        if f"{p.sn}{p.team_code}" == dh_id:
            continue
        if p.state_flags.get("first_receiver"):
            return p

    # Fallback: nearest attacker not in ruck and not DH
    dh = match.get_player_by_code(dh_id)
    dx, dy, _ = _xyz(dh.location)
    candidates = []
    for p in match.players:
        if p.team_code != atk: 
            continue
        if p.state_flags.get("in_ruck", False):
            continue
        if f"{p.sn}{p.team_code}" == dh_id:
            continue
        x, y, _ = _xyz(p.location)
        d2 = (x - dx) ** 2 + (y - dy) ** 2
        candidates.append((d2, p))
    candidates.sort(key=lambda t: t[0])
    return candidates[0][1] if candidates else None

def plan(match, state_tuple) -> List[DoCall]:
    bx, by, _ = _xyz(getattr(match.ball, "location", None))
    atk = getattr(match, "possession", "a")
    deff = "b" if atk == "a" else "a"

    # 1) mark in-ruck (<=2.5m)
    for p in match.players:
        dx, dy = p.location[0]-bx, p.location[1]-by
        p.state_flags["in_ruck"] = (dx*dx + dy*dy) <= (2.5*2.5)

    calls: List[DoCall] = []

    # 2) assign DH (9 or fallback) only if not already set
    dh_id: Optional[str] = _current_dh_id(match)
    if dh_id is None:
        dh_id = assign_dummy_half(match, atk, near_xy=(bx, by))

    # 3) DH sub-routine: PASS (use ball.holder — they should have it now)
    if dh_id:
        # If for some reason the holder isn't DH yet, try to pick up quickly
        if getattr(match.ball, "holder", None) != dh_id:
            dh = match.get_player_by_code(dh_id)
            px, py, _ = _xyz(dh.location)
            # If close enough, catch; else nudge toward base — purely as a safety fallback
            if (px-bx)**2 + (py-by)**2 <= (1.5*1.5):
                calls.append((dh_id, ("catch", None), (px, py, 0.0), (bx, by, 0.0)))
                match.ball.holder = dh_id
            else:
                calls.append((dh_id, ("move", None), (px, py, 0.0),
                              match.pitch.clamp_position((bx, by, 0.0))))
        # If DH has the ball, just pass
        if getattr(match.ball, "holder", None) == dh_id:
            receiver = _choose_receiver(match, atk, dh_id)
            if receiver:
                rx, ry, _ = _xyz(receiver.location)
                rid = f"{receiver.sn}{receiver.team_code}"
                dh = match.get_player_by_code(dh_id)
                calls.append((dh_id, ("pass", rid), _xyz(dh.location), (rx, ry, 0.0)))
                # (Optional) immediately transfer holder if your engine expects that on pass call:
                # match.ball.holder = rid

    # 4) Attack phase shape (non-ruck, non-DH)
    atk_targets = phase_attack_targets(match, atk, (bx, by))
    for p in match.players:
        pid = f"{p.sn}{p.team_code}"
        if p.team_code != atk: 
            continue
        if p.state_flags.get("in_ruck", False): 
            continue
        if dh_id and pid == dh_id: 
            continue  # DH is busy with the pass routine
        tgt = atk_targets.get(p)
        if not tgt: 
            continue
        calls.append((pid, ("move", None), _xyz(p.location), tgt))

    # 5) Defence line
    def_targets = phase_defence_targets(match, deff, (bx, by))
    for p in match.players:
        if p.team_code != deff: 
            continue
        if p.state_flags.get("in_ruck", False): 
            continue
        tgt = def_targets.get(p)
        if not tgt: 
            continue
        calls.append((f"{p.sn}{p.team_code}", ("move", None), _xyz(p.location), tgt))

    return calls
