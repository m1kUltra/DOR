# matchEngine/choice/individual/ball_holder_choices.py
from typing import Optional, Tuple
import math
from constants import PASS_MAX_RANGE, RUN_PROBE_LEN, EPS, Twenty2_A_X, Twenty2_B_X

XYZ    = Tuple[float, float, float]
Action = Tuple[str, Optional[str]]   # ("pass","flat"), ("kick","exit"), ("move", None)

def choose(match, holder_id: str, state_tuple) -> Tuple[Optional[Action], Optional[XYZ]]:
    """
    Simple policy for the ball carrier:
      1) If in own 22 → ("kick","exit") 30m ahead (same y)
      2) Else if nearest legal receiver (not forward, within range) → ("pass","flat")
      3) Else → ("move", None) straight ahead by RUN_PROBE_LEN
    """
    holder = match.get_player_by_code(holder_id)
    if not holder:
        return (None, None)

    # attack_dir straight from team tactics (set in setup)
    attack_dir = (match.team_a.tactics["attack_dir"]
                  if holder.team_code == "a"
                  else match.team_b.tactics["attack_dir"])
    attack_dir = float(attack_dir)

    x, y, _ = holder.location

    # 1) own 22 → exit kick
    if _in_own_22(holder.team_code, x):
        target = match.pitch.clamp_position((x + 30.0 * attack_dir, y, 0.0))
        return (("kick", "exit"), target)

    # 2) nearest legal receiver (backward/not-forward + within range)
    recv = _best_receiver(match, holder, attack_dir)
    if recv:
        rx, ry, _ = recv.location
        return (("pass", "flat"), (rx, ry, 0.0))

    # 3) carry forward
    target = match.pitch.clamp_position((x + RUN_PROBE_LEN * attack_dir, y, 0.0))
    return (("move", None), target)


# ---------- internals ----------

def _in_own_22(team_code: str, x: float) -> bool:
    # A attacks to +x; own 22 is x <= 22
    # B attacks to -x; own 22 is x >= 78
    if team_code == "a":
        return x <= float(Twenty2_A_X) + EPS
    return x >= float(Twenty2_B_X) - EPS

def _dist2(ax: float, ay: float, bx: float, by: float) -> float:
    dx, dy = ax - bx, ay - by
    return dx*dx + dy*dy

def _legal_not_forward(attack_dir: float, dx: float) -> bool:
    # Not forward relative to attack_dir; allow tiny EPS
    if attack_dir > 0:
        return dx <= EPS
    return dx >= -EPS

def _best_receiver(match, holder, attack_dir: float):
    hx, hy, _ = holder.location
    best = None
    best_d2 = float("inf")
    max_d2 = PASS_MAX_RANGE * PASS_MAX_RANGE
    for p in match.players:
        if p is holder or p.team_code != holder.team_code:
            continue
        px, py, _ = p.location
        d2 = _dist2(hx, hy, px, py)
        if d2 > max_d2:
            continue
        dx = px - hx
        if not _legal_not_forward(attack_dir, dx):
            continue
        if d2 < best_d2:
            best_d2 = d2
            best = p
    return best
