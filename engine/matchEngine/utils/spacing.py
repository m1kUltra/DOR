# matchEngine/utils/spacing.py
from typing import Dict, Tuple, List
from constants import TOUCHLINE_BOTTOM_Y, TOUCHLINE_TOP_Y
from utils.position_utils import forward_pod_lane

Vec2 = Tuple[float, float]
Target = Tuple[float, float, float]

def _clamp_y(y: float, margin: float) -> float:
    low = TOUCHLINE_BOTTOM_Y + max(0.0, margin)
    high = TOUCHLINE_TOP_Y - max(0.0, margin)
    if low > high:
        low, high = TOUCHLINE_BOTTOM_Y, TOUCHLINE_TOP_Y
    return max(low, min(high, y))
def resolve_team_spacing(team, proposals, state_name, ball_loc, holder_code=None)-> Dict[object, Target]:
    """
    Fan-out resolver to avoid crowding.
    - Applies to open play (and most states) but NOT to 'ruck'
    - Works per unit:
        * Forwards: per lane (pods)
        * Backs: one backline group
    """
    
    if state_name == "ruck":
        return proposals

    holder_code = holder_code or ""
    
    def is_holder(player):
        return f"{player.sn}{player.team_code}" == holder_code

    adj = dict(proposals)

    # Wherever you loop over players to adjust gaps:
    for p in sorted(team.squad, key=lambda pl: pl.rn):
        if is_holder(p):
            continue 

        return proposals  # bunching around the breakdown is allowed

    t = team.tactics
    wing_margin   = t["far_wing_margin"]
    min_gap_lat   = t.get("min_gap_lateral", 2.0)     # meters between teammates laterally
    min_gap_depth = t.get("min_gap_depth",   1.0)     # meters front-back to avoid stacking

    # Split into forwards lanes & backline
    forwards = [p for p in team.squad if p.rn in {1,2,3,4,5,6,7,8}]
    backs    = [p for p in team.squad if p.rn in {9,10,11,12,13,14,15}]

    # ---------- Forwards: group by lane (pods) ----------
    lane_groups: Dict[int, List[object]] = { -1:[], 0:[], +1:[] }
    # Keep a stable order by rn
    f_sorted = sorted(forwards, key=lambda pl: pl.rn)
    for i, pl in enumerate(f_sorted):
        lane = forward_pod_lane(i)
        lane_groups.setdefault(lane, []).append(pl)

    adj: Dict[object, Target] = dict(proposals)  # start with proposals

    for lane, members in lane_groups.items():
        if not members:
            continue
        # Sort by proposed Y to lay them out without overlap
        members = sorted(members, key=lambda pl: proposals.get(pl, (pl.location))[1])
        # Fan outward around the lane center Y (which is already in proposals)
        # Guarantee min lateral gap between neighbors
        for idx, pl in enumerate(members):
            tx, ty, tz = adj[pl]
            # target base y stays; shift neighbors away if too close
            if idx > 0:
                prev = members[idx-1]
                px, py, pz = adj[prev]
                if abs(ty - py) < min_gap_lat:
                    # push current away from previous
                    sign = +1.0 if (ty >= py) else -1.0
                    ty = py + sign * min_gap_lat
            # Clamp to touchlines (honor margin)
            ty = _clamp_y(ty, wing_margin)
            # Depth staggering inside pods to avoid stacking x
            # Slight sawtooth: odd members stand 0.5m deeper behind their proposed x
            if idx % 2 == 1:
                tx = tx - 0.5 if t.get("attack_dir", +1.0) > 0 else tx + 0.5
            adj[pl] = (tx, ty, tz)

    # ---------- Backs: single line fan-out ----------
    backs_sorted = sorted(backs, key=lambda pl: proposals.get(pl, (pl.location))[1])
    for idx, pl in enumerate(backs_sorted):
        tx, ty, tz = adj[pl]
        if idx > 0:
            prev = backs_sorted[idx-1]
            px, py, pz = adj[prev]
            # enforce lateral spacing
            if abs(ty - py) < min_gap_lat:
                sign = +1.0 if (ty >= py) else -1.0
                ty = py + sign * min_gap_lat
            # enforce some depth staggering so receivers don't stack on same x
            if abs(tx - adj[prev][0]) < min_gap_depth:
                # move slightly further behind the ball line
                tx = (tx - 0.4) if t.get("attack_dir", +1.0) > 0 else (tx + 0.4)
        ty = _clamp_y(ty, wing_margin)
        adj[pl] = (tx, ty, tz)

    return adj
