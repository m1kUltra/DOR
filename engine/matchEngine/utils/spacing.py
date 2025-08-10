# matchEngine/utils/spacing.py
from typing import Dict, Tuple, List, Optional
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

def resolve_team_spacing(
    team,
    proposals: Dict[object, Target],
    state_name: str,
    ball_loc: Target,
    holder_code: Optional[str] = None,
    exempt: Optional[set] = None,   # ⬅️ NEW: players we must NOT move (tackler/cover/set-lines)
) -> Dict[object, Target]:
    """
    Fan-out resolver to avoid crowding.

    - Applies in open play (and most states) but NOT in 'ruck'
    - Respects 'exempt' players (e.g., primary tackler, cover, set-line roles)
    - Holder is always exempt
    - Forwards: fan within pods (lanes)
    - Backs: fan as a single line
    """
    if state_name == "ruck":
        return proposals

    holder_code = holder_code or ""
    exempt = exempt or set()

    def is_holder(player) -> bool:
        return f"{player.sn}{player.team_code}" == holder_code

    # Start with existing targets
    adj: Dict[object, Target] = dict(proposals)

    # Pull spacing parameters
    t = team.tactics
    wing_margin   = t.get("far_wing_margin", 0.0)
    min_gap_lat   = t.get("min_gap_lateral", 2.0)
    min_gap_depth = t.get("min_gap_depth",   1.0)

    # Partition by unit and filter out exempt/holder
    forwards_all = [p for p in team.squad if p.rn in {1,2,3,4,5,6,7,8}]
    backs_all    = [p for p in team.squad if p.rn in {9,10,11,12,13,14,15}]

    def movable(ps: List[object]) -> List[object]:
        # stable order: rn then sn
        base = sorted(ps, key=lambda pl: (pl.rn, pl.sn))
        return [p for p in base if (p not in exempt and not is_holder(p) and p in proposals)]

    forwards = movable(forwards_all)
    backs    = movable(backs_all)

    # ---------- Forwards: group by lane (pods) ----------
    lane_groups: Dict[int, List[object]] = {-1: [], 0: [], +1: []}
    f_sorted = sorted(forwards, key=lambda pl: (pl.rn, pl.sn))
    for i, pl in enumerate(f_sorted):
        lane = forward_pod_lane(i)
        lane_groups.setdefault(lane, []).append(pl)

    for lane, members in lane_groups.items():
        if not members:
            continue
        # Sort by current proposed Y to lay them out deterministically
        members = sorted(members, key=lambda pl: proposals.get(pl, pl.location)[1])
        for idx, pl in enumerate(members):
            tx, ty, tz = adj[pl]
            if idx > 0:
                prev = members[idx - 1]
                px, py, _ = adj[prev]
                if abs(ty - py) < min_gap_lat:
                    ty = py + (min_gap_lat if ty >= py else -min_gap_lat)
            ty = _clamp_y(ty, wing_margin)
            # small depth staggering to avoid same-x stacking
            if idx % 2 == 1:
                tx = tx - 0.5 if t.get("attack_dir", +1.0) > 0 else tx + 0.5
            adj[pl] = (tx, ty, tz)

    # ---------- Backs: single line fan-out ----------
    backs_sorted = sorted(backs, key=lambda pl: proposals.get(pl, pl.location)[1])
    for idx, pl in enumerate(backs_sorted):
        tx, ty, tz = adj[pl]
        if idx > 0:
            prev = backs_sorted[idx - 1]
            px, py, _ = adj[prev]
            # enforce lateral spacing
            if abs(ty - py) < min_gap_lat:
                ty = py + (min_gap_lat if ty >= py else -min_gap_lat)
            # depth staggering so receivers don't sit same x
            if abs(tx - adj[prev][0]) < min_gap_depth:
                tx = (tx - 0.4) if t.get("attack_dir", +1.0) > 0 else (tx + 0.4)
        ty = _clamp_y(ty, wing_margin)
        adj[pl] = (tx, ty, tz)

    # Holder + exempt players remain untouched (we never modified their adj)
    return adj
