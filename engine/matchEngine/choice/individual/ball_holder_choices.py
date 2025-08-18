# matchEngine/choice/individual/ball_holder_choices.py
from typing import Optional, Tuple, List
import math, random
from constants import PASS_MAX_RANGE, RUN_PROBE_LEN, EPS

XYZ    = Tuple[float, float, float]
Action = Tuple[str, Optional[str]]   # ("pass","flat"), ("kick","exit"/"chip"/"bomb"/"grubber"), ("move", None)

def choose(match, holder_id: str, state_tuple) -> Tuple[Optional[Action], Optional[XYZ]]:
    holder = match.get_player_by_code(holder_id)
    if not holder:
        return (None, None)

    attack_dir = _attack_dir_for(holder, match)
    x, y, _ = holder.location

    # --- close pressure gate: pure random evasion vs carry if defender < 5m ---
    if _nearest_defender_distance(holder, match) < 5.0:
        if random.random() < 0.5:
            return (("move", None), _evade_target(holder, attack_dir, match))  # sidestep + 2m forward
        else:
            return (("move", None), match.pitch.clamp_position((x + RUN_PROBE_LEN * attack_dir, y, 0.0)))

    # --- build uniformly random options (legal where needed) ---
    options: List[Tuple[Action, XYZ]] = []

    # RUN: always legal
    run_target = match.pitch.clamp_position((x + RUN_PROBE_LEN * attack_dir, y, 0.0))
    options.append((("move", None), run_target))

    # PASS: only if a legal receiver exists (not forward, within range)
    recvs = _legal_receivers(match, holder, attack_dir)
    if recvs:
        r = random.choice(recvs)  # random teammate among legal receivers
        rx, ry, _ = r.location
        options.append((("pass", "flat"), (rx, ry, 0.0)))

    # KICK: always allowed; pick subtype uniformly
    kick_subtype = random.choice(["exit", "bomb", "chip", "grubber"])
    k_target = _kick_target_for(holder, match, kick_subtype, attack_dir)
    options.append((("kick", kick_subtype), k_target))

    # pick a random option from what’s available
    action, target = random.choice(options)
    return (action, target)

# ---------------- helpers (kept simple) ----------------

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

def _legal_not_forward(attack_dir: float, dx: float) -> bool:
    # not forward relative to attack_dir
    if attack_dir > 0:  return dx <= EPS
    else:               return dx >= -EPS

def _legal_receivers(match, holder, attack_dir: float):
    hx, hy, _ = holder.location
    out = []
    max_d2 = PASS_MAX_RANGE * PASS_MAX_RANGE
    for p in match.players:
        if p is holder or p.team_code != holder.team_code: continue
        px, py, _ = p.location
        d2 = (px - hx)**2 + (py - hy)**2
        if d2 > max_d2: continue
        dx = px - hx
        if not _legal_not_forward(attack_dir, dx): continue
        out.append(p)
    return out

def _kick_target_for(holder, match, subtype: str, attack_dir: float) -> XYZ:
    x, y, _ = holder.location
    if subtype == "exit":    dist = 30.0
    elif subtype == "bomb":  dist = 35.0
    elif subtype == "chip":  dist = 12.0
    elif subtype == "grubber": dist = 18.0
    else: dist = 20.0
    return match.pitch.clamp_position((x + dist * attack_dir, y, 0.0))

def _evade_target(holder, attack_dir: float, match) -> XYZ:
    x, y, _ = holder.location
    lateral = 3.0 * (1 if (random.random() < 0.5) else -1)  # ±3m
    return match.pitch.clamp_position((x + 2.0 * attack_dir, y + lateral, 0.0))
