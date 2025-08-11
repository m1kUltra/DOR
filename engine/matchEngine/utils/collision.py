# utils/collision.py
from typing import Optional, Dict, Tuple
from constants import TACKLE_TRIGGER_DIST, TACKLER_DOWN_TICKS, GATE_DEPTH

def _closing_along_dir(holder_xy: Tuple[float,float], tack_xy: Tuple[float,float],
                        prev_tack_xy: Tuple[float,float] | None, attack_dir: float) -> bool:
    hx, hy = holder_xy
    tx, ty = tack_xy
    d_now2 = (tx-hx)**2 + (ty-hy)**2
    if prev_tack_xy is None:
        return True  # first frame: allow
    ptx, pty = prev_tack_xy
    d_prev2 = (ptx-hx)**2 + (pty-hy)**2
    # strictly closing OR overlapping
    if d_now2 <= (TACKLE_TRIGGER_DIST**2) and d_now2 <= d_prev2:
        # also check approach along attack axis is not moving away
        dx_now = (tx - hx) * attack_dir
        dx_prev = (ptx - hx) * attack_dir
        return dx_now <= dx_prev + 1e-6
    return False

def detect_tackle_event(match) -> Optional[Dict]:
    if not match.ball.holder:
        return None
    holder = match.get_player_by_code(match.ball.holder)
    if not holder:
        return None
    hx, hy, _ = holder.location
    attack_dir = (match.team_a if holder.team_code=='a' else match.team_b).tactics.get("attack_dir", +1.0)

    nearest, best_d2 = None, None
    for p in match.players:
        if p.team_code == holder.team_code:
            continue
        px, py, _ = p.location
        d2 = (px-hx)**2 + (py-hy)**2
        if best_d2 is None or d2 < best_d2:
            best_d2, nearest = d2, p

    if nearest and best_d2 <= (TACKLE_TRIGGER_DIST**2):
        prev = getattr(nearest, "_prev_xy", None)
        if _closing_along_dir((hx,hy), (nearest.location[0], nearest.location[1]), prev, attack_dir):
            return {"tackler": nearest, "holder": holder, "anchor": (hx, hy)}
    return None

def resolve_tackle(match, tackler, holder, anchor_xy) -> None:
    holder.state_flags["is_tackled"] = True
    tackler.state_flags["is_on_feet"] = False
    setattr(tackler, "_down_ticks", TACKLER_DOWN_TICKS)

    match.ball.release()
    ax, ay = anchor_xy
    match.ball.location = (ax, ay, 0.0)

    dir_ = (match.team_a if holder.team_code=='a' else match.team_b).tactics.get("attack_dir", +1.0)
    match.ruck_meta = {
        "anchor": (ax, ay),
        "phase": "forming",
        "since_tick": match.tick_count,
        "last_feet_line": ax - dir_ * GATE_DEPTH,  # ← spec: +/- GATE_DEPTH
        "winner": None,
        "ball_speed": None,
        "attack_dir": dir_,
    }
