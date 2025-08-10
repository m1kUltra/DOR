# matchEngine/utils/decision_engine.py

from typing import Dict, Tuple
from constants import FORWARDS, BACKS, DEFAULT_PLAYER_SPEED, TACKLE_RANGE, EPS
from utils.position_utils import forwards_shape_positions, backline_shape_positions
from utils.spacing import resolve_team_spacing

Action = str
Target = Tuple[float, float, float]

# -------------------------
# Holder decision helpers
# -------------------------

def _attack_dir(team) -> float:
    return float(team.tactics.get("attack_dir", +1.0))

def _dist2(a, b) -> float:
    ax, ay, _ = a; bx, by, _ = b
    dx, dy = ax - bx, ay - by
    return dx*dx + dy*dy

def _nearest_defender(holder, opponents):
    hx, hy, _ = holder.location
    best = None
    best_d2 = None
    for p in opponents:
        px, py, _ = p.location
        d2 = (px - hx)**2 + (py - hy)**2
        if best_d2 is None or d2 < best_d2:
            best_d2 = d2; best = p
    return best, (best_d2 ** 0.5) if best_d2 is not None else None

def _count_defenders_ahead(holder, opponents, team_dir: float, cone_y=12.0, depth_x=12.0):
    """Rough pressure cone ahead of the ball-carrier."""
    hx, hy, _ = holder.location
    ahead = 0
    for d in opponents:
        dx = (d.location[0] - hx) * team_dir
        dy = abs(d.location[1] - hy)
        if dx > 0 and dx <= depth_x and dy <= cone_y:
            ahead += 1
    return ahead

def _find_support_receivers(holder, teammates, team_dir: float, max_dist=12.0):
    """Potential pass targets: lateral or behind only (no forward)."""
    hx, hy, _ = holder.location
    cands = []
    for m in teammates:
        if m is holder: continue
        mx, my, _ = m.location
        dx = (mx - hx)
        # legal if not forward relative to attack dir
        legal = (dx <= EPS if team_dir > 0 else dx >= -EPS)
        if not legal: continue
        d2 = (mx - hx)**2 + (my - hy)**2
        if d2 <= max_dist*max_dist:
            cands.append((m, d2))
    # sort by closeness first (you can add angle/role heuristics later)
    cands.sort(key=lambda t: t[1])
    return [m for (m, _) in cands]

def _holder_action(match, holder, team, opp_team) -> Tuple[Action, Target]:
    """
    Decide what the ball-carrier should do right now.
    Returns (action, target). For pass/kick/contact, target is holder's current spot.
    For run, target is a point ahead; BaseState will move them toward it.
    """
    dir_ = _attack_dir(team)
    hx, hy, hz = holder.location

    # Attributes (defaults if missing)
    ment = holder.attributes.get("mental", {})
    tech = holder.attributes.get("technical", {})
    phys = holder.attributes.get("physical", {})

    awareness = float(ment.get("awareness", 55))
    decision   = float(ment.get("decision_making", ment.get("composure", 55)))
    kicking    = float(tech.get("kicking", 55))
    passing    = float(tech.get("passing", 55))
    speed_attr = float(phys.get("speed", DEFAULT_PLAYER_SPEED))

    # Situational reads
    opponents = [p for p in match.players if p.team_code != holder.team_code]
    teammates = [p for p in match.players if p.team_code == holder.team_code]

    nearest_def, dist_nearest = _nearest_defender(holder, opponents)
    pressure_cone = _count_defenders_ahead(holder, opponents, dir_)
    supports = _find_support_receivers(holder, teammates, dir_)

    # Field context (very simple for now)
    in_own_half   = (holder.location[0] < 50.0) if dir_ > 0 else (holder.location[0] > 50.0)
    near_tryline  = (holder.location[0] > 90.0) if dir_ > 0 else (holder.location[0] < 10.0)

    # Heuristic thresholds
    safe_run_space   = 5.0   # meters
    panic_pressure   = 2     # defenders in cone
    offload_window   = 4.0   # meters

    # 1) Under heavy pressure & in own half: KICK for territory if decent kicker
    if pressure_cone >= panic_pressure and in_own_half and kicking >= 55 and decision >= 55:
        return "kick", (hx, hy, hz)

    # 2) Good support near & decent passing: PASS
    if supports and passing >= 50 and awareness >= 50:
        # Prefer backs (10/12/13) first, then nearest
        backs_first = sorted(supports, key=lambda p: (0 if p.rn in {10,12,13} else 1, _dist2(p.location, holder.location)))
        target_mate = backs_first[0]
        # mark pass; dispatcher will transfer the ball
        return "pass", (hx, hy, hz)

    # 3) Space to run (no defender within safe_run_space) OR high pace
    if (dist_nearest is None or dist_nearest > safe_run_space) or speed_attr >= 6.5:
        # Set a run target a few meters ahead; BaseState will move the carrier
        ahead = 3.0  # desired gain this phase; BaseState caps by speed*dt anyway
        return "run", (hx + dir_*ahead, hy, 0.0)

    # 4) Near tryline & short on options: enter contact to set a ruck
    if near_tryline or pressure_cone >= 1:
        return "enter_contact", (hx, hy, hz)

    # Fallback
    return "run", (hx + dir_*2.0, hy, 0.0)

# -------------------------
# Non-holder positioning (unchanged API)
# -------------------------

def _propose_target_for_player(player, game_state, ball, team, opp_team) -> Tuple[Action, Target]:
    holder_code = f"{player.sn}{player.team_code}"
    is_holder = (ball.holder == holder_code)

    if game_state.name == "open_play":
        if is_holder:
            # Decide a real action for holder
            return _holder_action(team=team, opp_team=opp_team, match=ball.match if hasattr(ball, 'match') else None, holder=player)
        if player.rn in FORWARDS:
            forwards_sorted = sorted([p for p in team.squad if p.rn in FORWARDS], key=lambda p: p.rn)
            idx = forwards_sorted.index(player)
            tgt = forwards_shape_positions(team, ball.location, player.rn, idx)
            return ("support", tgt)
        if player.rn in BACKS:
            tgt = backline_shape_positions(team, ball.location, player.rn, player.sn)
            return ("shape", tgt)
        return ("drift", player.location)

    # Other states can add their own logic later
    return (player.current_action or "idle", player.location)

# -------------------------
# Batch: both teams → spacing → single move
# -------------------------

# matchEngine/utils/decision_engine.py
from typing import Dict, Tuple

def compute_positions_for_teams(match, game_state) -> Dict[object, Tuple[Action, Target]]:
    """
    Build proposed (action,target) for every player, resolve spacing per team,
    and return a dict {player: (action, target)}.
    """
    a_team = match.team_a
    b_team = match.team_b

    # (Optional) make match available to holder logic that needs it
    setattr(match.ball, "match", match)

    # 1) raw proposals per team
    props_a = {p: _propose_target_for_player(p, game_state, match.ball, a_team, b_team) for p in a_team.squad}
    props_b = {p: _propose_target_for_player(p, game_state, match.ball, b_team, a_team) for p in b_team.squad}

    # 2) spacing resolve (fan-out), skipping holder
    holder_code = match.ball.holder
    adj_a_targets = resolve_team_spacing(
        a_team,
        {p: tgt for p, (_, tgt) in props_a.items()},
        game_state.name,
        match.ball.location,
        holder_code,
    )
    adj_b_targets = resolve_team_spacing(
        b_team,
        {p: tgt for p, (_, tgt) in props_b.items()},  # ← single braces (a plain dict)
        game_state.name,
        match.ball.location,
        holder_code,
    )

    # 3) combine action + adjusted targets
    final: Dict[object, Tuple[Action, Target]] = {}
    for p, (act, _) in props_a.items():
        final[p] = (act, adj_a_targets[p])
    for p, (act, _) in props_b.items():
        final[p] = (act, adj_b_targets[p])

    # clean transient
    if hasattr(match.ball, "match"):
        delattr(match.ball, "match")

    return final
