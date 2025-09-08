
# matchEngine/choice/individual/ball_holder_choices.py
from typing import Optional, Tuple, List
import math, random

from constants import RUN_PROBE_LEN, EPS, TRYLINE_A_X, TRYLINE_B_X
from utils.actions.pass_helpers import pass_range, pass_scope

XYZ    = Tuple[float, float, float]
Action = Tuple[str, Optional[str]]

OFFLOAD_MAX_RANGE = 10.0  # m

def choose(match, holder_id: str, state_tuple) -> Tuple[Optional[Action], Optional[XYZ]]:
    holder = match.get_player_by_code(holder_id)
    if not holder:
        return (None, None)
  
    attack_dir = _attack_dir_for(holder, match)  # +1 or -1
    x, y, _ = holder.location

    norms = getattr(holder, "norm_attributes", {})
    norm_passing = float(norms.get("passing", 0.0))
    norm_technique = float(norms.get("technique", 0.0))
    range_ = pass_range(norm_passing, norm_technique)
    scope = pass_scope(norm_technique)

    # --- 0) Tryline check → ground immediately ---
    try_x = TRYLINE_B_X if attack_dir > 0 else TRYLINE_A_X
    crossed = (
        (attack_dir > 0 and x >= try_x - EPS) or
        (attack_dir < 0 and x <= try_x + EPS)
    )
    if crossed:
        return (("ground", None), match.pitch.clamp_position((x, y, 0.0)))

    # --- 1) If being tackled, attempt a short offload (<=10m, not forward) ---
    if holder.state_flags.get("being_tackled", False):
        recv = _nearest_legal_receiver_within(match, holder, attack_dir, OFFLOAD_MAX_RANGE)
        if recv is not None:
            rx, ry, rz = recv.location
            return (("offload", None), match.pitch.clamp_position((rx, ry, rz if rz else 1.0)))
        else:
            hx, hy, _ = holder.location
            return (("tackled", None), match.pitch.clamp_position((hx, hy, 0.0)))
            
    # --- 2) Under pressure → evade or short probe ---
    if _nearest_defender_distance(holder, match) < 5.0:
        if random.random() < 0.5:
            return (("move", None), _evade_target(holder, attack_dir, match))
        else:
            return (("move", None), match.pitch.clamp_position(
                (x + RUN_PROBE_LEN * attack_dir, y, 0.0)
            ))

    # --- 3) Passing option ---
 
    recvs = _legal_receivers(match, holder, attack_dir, range_, scope)
    if recvs:
        r = random.choice(recvs)
        rx, ry, rz = r.location
        
        dist = math.hypot(rx - x, ry - y)
        if dist < 10.0:
            subtype = "flat"
        elif dist < 20.0:
            subtype = "spin"
        else:
            subtype = "league"
        return (("pass", subtype), match.pitch.clamp_position((rx, ry, rz if rz else 1.0)))

    # --- 4) Kick option ---
    kick_subtype = random.choice(["exit", "bomb", "chip", "grubber"])
    k_target = _kick_target_for(holder, match, kick_subtype, attack_dir)
    return (("kick", kick_subtype), k_target)

# ---------------- helpers ----------------

def _attack_dir_for(player, match) -> float:
    return float(match.team_a.tactics["attack_dir"] if player.team_code == "a"
                 else match.team_b.tactics["attack_dir"])

def _nearest_defender_distance(holder, match) -> float:
    hx, hy, _ = holder.location
    best = 1e9
    for p in match.players:
        if p.team_code == holder.team_code: continue
        px, py, _ = p.location
        d = math.hypot(px - hx, py - hy)
        if d < best: best = d
    return best

def _nearest_legal_receiver_within(match, holder, attack_dir: float, max_range: float):
    hx, hy, _ = holder.location
    best = None
    best_d2 = (max_range * max_range) + 1.0
    for p in match.players:
        if p is holder or p.team_code != holder.team_code:
            continue
        sf = p.state_flags
        if sf.get("being_tackled", False) or sf.get("off_feet", False):
            continue
        px, py, _ = p.location
        dx, dy = px - hx, py - hy
        d2 = dx*dx + dy*dy
        if d2 > max_range * max_range:
            continue
        if (attack_dir > 0 and dx > EPS) or (attack_dir < 0 and dx < -EPS):
            continue
        if d2 < best_d2:
            best_d2 = d2
            best = p
    return best

def _legal_not_forward(attack_dir: float, dx: float) -> bool:
    if attack_dir > 0:  return dx <= EPS
    else:               return dx >= -EPS


def _legal_receivers(match, holder, attack_dir: float, range_: float, scope: float):
    hx, hy, _ = holder.location
    out = []
 
    max_d2 = range_ * range_
    half_scope = scope / 2.0
    for p in match.players:
        
        if p is holder or p.team_code != holder.team_code:
            continue
        px, py, _ = p.location
      
        dx, dy = px - hx, py - hy
        d2 = dx * dx + dy * dy
        if d2 > max_d2:
            continue
        if not _legal_not_forward(attack_dir, dx):
            continue
        angle = abs(math.atan2(dy, dx if attack_dir > 0 else -dx))
        if angle > half_scope:
            continue
        sf = p.state_flags
        if sf.get("being_tackled", False) or sf.get("off_feet", False):
            continue
        out.append(p)
    return out

def _kick_target_for(holder, match, subtype: str, attack_dir: float) -> XYZ:
    x, y, _ = holder.location
    if subtype == "exit":    dist = 60.0
    elif subtype == "bomb":  dist = 35.0
    elif subtype == "chip":  dist = 12.0
    elif subtype == "grubber": dist = 18.0
    else: dist = 50.0
    return match.pitch.clamp_position((x + dist * attack_dir, y, 0.0))

def _evade_target(holder, attack_dir: float, match) -> XYZ:
    x, y, _ = holder.location
    lateral = 3.0 * (1 if (random.random() < 0.5) else -1)  # ±3m
    return match.pitch.clamp_position((x + 2.0 * attack_dir, y + lateral, 0.0))