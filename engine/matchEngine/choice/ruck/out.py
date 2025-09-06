"""State where 9 has picked from the scrum but, before passing, we protect the sequence
from open_play logic and instant pressure. Mirrors ruck/out behavior (no tactics)."""

from typing import List, Tuple, Optional
from utils.positioning.mental.phase import phase_attack_targets, phase_defence_targets

DoCall = Tuple[str, Tuple[str, Optional[str]], Tuple[float, float, float], Tuple[float, float, float]]

READY_DIST = 5.0
READY_D2   = READY_DIST * READY_DIST
PRESENT_HOLD_TICKS = 18  # ~0.9s @ 20Hz; receiver "presents" for the pass

def _xyz(p):
    return tuple(p) if isinstance(p, (list, tuple)) and len(p) >= 2 else (0.0, 0.0, 0.0)

def _d2(a, b):
    dx, dy = a[0] - b[0], a[1] - b[1]
    return dx*dx + dy*dy

def _wait_limit_ticks(match) -> int:
    # Mirror ruck/out: 5s at engine tick rate (default 20Hz)
    tps = getattr(match, "ticks_per_second", 20)
    return int(5 * max(1, tps))

def _clear_first_receiver_flags(match, team_code: str):
    for p in match.players:
        if p.team_code == team_code:
            p.state_flags.pop("first_receiver", None)
            p.state_flags.pop("hold_for_pass", None)

def _assign_first_receiver(match, atk: str, dh_id: Optional[str], base_xy) -> Optional[object]:
    """Prefer 10, else 12, 13, 15, else nearest attacker not DH/in_ruck/in_scrum."""
    bx, by = base_xy
    team = match.team_a if atk == "a" else match.team_b

    _clear_first_receiver_flags(match, atk)

    for rn in (10, 12, 13, 15):
        p = team.get_player_by_rn(rn)
        if not p:
            continue
        pid = f"{p.sn}{p.team_code}"
        if dh_id and pid == dh_id:
            continue
        if p.state_flags.get("in_ruck", False) or p.state_flags.get("in_scrum", False):
            continue
        p.state_flags["first_receiver"] = True
        p.state_flags["hold_for_pass"] = PRESENT_HOLD_TICKS
        return p

    # Fallback: nearest eligible attacker to base
    cand = [
        p for p in match.players
        if p.team_code == atk
        and f"{p.sn}{p.team_code}" != (dh_id or "")
        and not p.state_flags.get("in_ruck", False)
        and not p.state_flags.get("in_scrum", False)
    ]
    if not cand:
        return None
    cand.sort(key=lambda p: (p.location[0] - bx) ** 2 + (p.location[1] - by) ** 2)
    r = cand[0]
    r.state_flags["first_receiver"] = True
    r.state_flags["hold_for_pass"] = PRESENT_HOLD_TICKS
    return r

def _team_ready(match, atk: str, base_xy, dh_id: Optional[str]) -> bool:
    bx, by = base_xy
    targets = phase_attack_targets(match, atk, (bx, by))
    ready = total = 0
    for p in match.players:
        if p.team_code != atk:
            continue
        if p.state_flags.get("in_ruck", False) or p.state_flags.get("in_scrum", False):
            continue
        pid = f"{p.sn}{p.team_code}"
        if dh_id and pid == dh_id:
            continue
        tgt = targets.get(p)
        if not tgt:
            continue
        total += 1
        if _d2((p.location[0], p.location[1]), (tgt[0], tgt[1])) <= READY_D2:
            ready += 1
    return (ready >= 10) or (total and ready / total >= 0.66)

def _current_dh_id(match) -> Optional[str]:
    # Prefer whoever is flagged as the active dummy-half
    for p in match.players:
        if p.state_flags.get("dummy_half"):
            return f"{p.sn}{p.team_code}"
    return None

def plan(match, state_tuple) -> List[DoCall]:
    tag, _loc, _ctx = state_tuple
    if tag != "scrum.out":
        return []

    bx, by, _ = _xyz(getattr(match.ball, "location", None))
    base_xy = (bx, by)

    atk = getattr(match, "possession", "a")
    deff = "b" if atk == "a" else "a"

    # Determine DH: prefer flagged DH; else force jersey 9 of possession side
    dh_id = _current_dh_id(match) or f"9{atk}"

    # Safety counter specific to scrum-out (separate from ruck counters)
    if not hasattr(match, "_scrum_out_wait"):
        match._scrum_out_wait = 0

    calls: List[DoCall] = []

    # Non-scrum attackers: flow to phase attack shapes (exclude DH)
    atk_targets = phase_attack_targets(match, atk, base_xy)
    for p in match.players:
        if p.team_code != atk:
            continue
        if p.state_flags.get("in_ruck", False) or p.state_flags.get("in_scrum", False):
            continue
        pid = f"{p.sn}{p.team_code}"
        if dh_id and pid == dh_id:
            continue
        tgt = atk_targets.get(p)
        if tgt:
            calls.append((pid, ("move", None), _xyz(p.location), tgt))

    # Defenders: flow to defence shapes (exclude those still marked in_scrum/in_ruck)
    def_targets = phase_defence_targets(match, deff, base_xy)
    for p in match.players:
        if p.team_code != deff:
            continue
        if p.state_flags.get("in_ruck", False) or p.state_flags.get("in_scrum", False):
            continue
        tgt = def_targets.get(p)
        if tgt:
            calls.append((f"{p.sn}{p.team_code}", ("move", None), _xyz(p.location), tgt))

    # Assign/refresh a presenting first-receiver
    _assign_first_receiver(match, atk, dh_id, base_xy)

    # If 9 is holder, gate the pass on readiness or a timeout; otherwise we just shape
    if dh_id and getattr(match.ball, "holder", None) == dh_id:
        ready = _team_ready(match, atk, base_xy, dh_id)
        timeout = match._scrum_out_wait >= _wait_limit_ticks(match)

        receiver = None
        if ready or timeout:
            # Choose receiver: flagged first_receiver else nearest eligible to DH
            dh = match.get_player_by_code(dh_id)
            dx, dy, _ = _xyz(dh.location)
            best = None
            best_d2 = 1e9
            for p in match.players:
                if p.team_code != atk:
                    continue
                if p.state_flags.get("in_ruck", False) or p.state_flags.get("in_scrum", False):
                    continue
                pid = f"{p.sn}{p.team_code}"
                if pid == dh_id:
                    continue
                if p.state_flags.get("first_receiver"):
                    receiver = p
                    break
                d2 = (p.location[0] - dx) ** 2 + (p.location[1] - dy) ** 2
                if d2 < best_d2:
                    best_d2, best = d2, p
            receiver = receiver or best

        if receiver:
            rx, ry, rz = _xyz(receiver.location)
            rid = f"{receiver.sn}{receiver.team_code}"
            dh = match.get_player_by_code(dh_id)
            tz = rz if rz else 1.0  # lift pass slightly if rz=0
            calls.append((dh_id, ("pass", rid), _xyz(dh.location), (rx, ry, tz)))
            match._scrum_out_wait = 0

            # Scrum is over once the pass leaves: clear in_scrum flags
            for p in match.players:
                if p.state_flags.get("in_scrum", False):
                    p.state_flags["in_scrum"] = False
        else:
            # Hold a beat (tiny nudge) while shapes settle
            dh = match.get_player_by_code(dh_id)
            px, py, _ = _xyz(dh.location)
            calls.append((dh_id, ("move", None), (px, py, 0.0), (bx + 0.001, by + 0.001, 0.0)))
            match._scrum_out_wait += 1
            # keep a distinct frame marker if you track it
            match._frames_since_scrum = 0

    return calls
