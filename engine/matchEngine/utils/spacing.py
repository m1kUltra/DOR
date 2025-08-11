# matchEngine/utils/spacing.py
from typing import Dict, Tuple, List, Optional
from math import copysign
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
    exempt: Optional[set] = None,
    mode: str = "attack",
    panic_spread: bool = False,   # ← NEW
) -> Dict[object, Target]:

    if state_name == "ruck":
        return dict(proposals)

    holder_code = holder_code or ""
    exempt = exempt or set()

    def is_holder(player) -> bool:
        return f"{player.sn}{player.team_code}" == holder_code

    adj: Dict[object, Target] = dict(proposals)

    t = team.tactics
    wing_margin   = float(t.get("far_wing_margin", 0.0))
    min_gap_lat   = float(t.get("min_gap_lateral", 2.0))
    min_gap_depth = float(t.get("min_gap_depth",   1.0))
    attack_dir    = float(t.get("attack_dir", +1.0))

    forwards_all = [p for p in team.squad if p.rn in {1,2,3,4,5,6,7,8}]
    backs_all    = [p for p in team.squad if p.rn in {9,10,11,12,13,14,15}]

    def movable(players: List[object]) -> List[object]:
        base = sorted(players, key=lambda pl: (pl.rn, pl.sn))
        return [p for p in base if (p in proposals) and (p not in exempt) and (not is_holder(p))]

    # ---------- PANIC SPREAD: rapid unbunching (Y-only) ----------
    # We spread *all movable players* evenly across width, preserving X,
    # and keeping a stable, deterministic order by (rn, sn).
    if panic_spread:
        line = movable(forwards_all + backs_all)
        if not line:
            return adj

        avail = (TOUCHLINE_TOP_Y - wing_margin) - (TOUCHLINE_BOTTOM_Y + wing_margin)
        # even spacing: N players ⇒ N segments, place in centers
        n = len(line)
        if n == 1:
            targets_y = [ (TOUCHLINE_BOTTOM_Y + TOUCHLINE_TOP_Y) * 0.5 ]
        else:
            step = avail / (n + 1)
            base = TOUCHLINE_BOTTOM_Y + wing_margin
            targets_y = [ base + step * (i + 1) for i in range(n) ]

        # assign in stable order
        for (pl, ty) in zip(line, targets_y):
            tx, _old_ty, tz = adj.get(pl, (*pl.location, 0.0))
            ty = _clamp_y(ty, wing_margin)
            adj[pl] = (tx, ty, tz)   # X unchanged → “Y-only” focus

        # holder + exempt already untouched
        return adj

    # ---------- DEFENSE: one flat line, resolve overlaps first ----------
    if mode == "defense":
        line = movable(forwards_all + backs_all)
        line_sorted = sorted(line, key=lambda pl: proposals.get(pl, (pl.location))[1])
        last_y: Optional[float] = None
        for pl in line_sorted:
            tx, ty, tz = adj.get(pl, (*pl.location, 0.0))
            if last_y is not None and abs(ty - last_y) < min_gap_lat:
                ty = last_y + (min_gap_lat if ty >= last_y else -min_gap_lat)
            ty = _clamp_y(ty, wing_margin)
            adj[pl] = (tx, ty, tz)
            last_y = ty
        return adj

    # ---------- ATTACK: forwards pods + backline ----------
    # (same as before)
    lanes: Dict[int, List[object]] = {-1: [], 0: [], +1: []}
    f_sorted = sorted(movable(forwards_all), key=lambda pl: (pl.rn, pl.sn))
    for i, pl in enumerate(f_sorted):
        lanes[forward_pod_lane(i)].append(pl)

    for lane, members in lanes.items():
        if not members:
            continue
        members = sorted(members, key=lambda pl: proposals.get(pl, (pl.location))[1])
        for idx, pl in enumerate(members):
            tx, ty, tz = adj.get(pl, (*pl.location, 0.0))
            if idx > 0:
                prev = members[idx - 1]
                _, py, _ = adj.get(prev, (*prev.location, 0.0))
                if abs(ty - py) < min_gap_lat:
                    ty = py + copysign(min_gap_lat, (ty - py) if ty != py else 1.0)
            ty = _clamp_y(ty, wing_margin)
            if idx % 2 == 1:
                tx = tx - 0.5 if attack_dir > 0 else tx + 0.5
            adj[pl] = (tx, ty, tz)

    backs_sorted = sorted(movable(backs_all), key=lambda pl: proposals.get(pl, (pl.location))[1])
    for idx, pl in enumerate(backs_sorted):
        tx, ty, tz = adj.get(pl, (*pl.location, 0.0))
        if idx > 0:
            prev = backs_sorted[idx - 1]
            px, py, _ = adj.get(prev, (*prev.location, 0.0))
            if abs(ty - py) < min_gap_lat:
                ty = py + (min_gap_lat if ty >= py else -min_gap_lat)
            if abs(tx - px) < min_gap_depth:
                tx = (tx - 0.4) if attack_dir > 0 else (tx + 0.4)
        ty = _clamp_y(ty, wing_margin)
        adj[pl] = (tx, ty, tz)

    return adj
