# utils/formations.py
# Formation library for structured set-pieces (scrum, lineout, maul) and simple defensive shapes.
# All functions return TARGETS (no teleports). States should assign these to player.action_meta["to"].

from __future__ import annotations
from typing import Dict, Tuple, Iterable, Optional, List

from constants import (
    TOUCHLINE_BOTTOM_Y, TOUCHLINE_TOP_Y,
)

# -------------------------------
# Tunable knobs
# -------------------------------
# Scrum
SCRUM_ROW_GAP_Y = 0.9
SCRUM_LOCK_BACK_X = -0.6
SCRUM_BACKROW_BACK_X = -1.2
SCRUM_NO8_X = -1.4
SCRUM_9_SIDE_OFFSET_Y = 1.5

# Lineout
LINEOUT_POD_GAP_X = 2.0
LINEOUT_LIFTER_OFFSET_Y = 0.8
LINEOUT_INFIELD_BUFFER_X = 8.0
LINEOUT_TOUCH_SAFE_Y = 6.0

# Maul
MAUL_RING_RADIUS_X = 1.2
MAUL_RING_RADIUS_Y = 0.9
MAUL_9_POCKET_X = -1.5

# Clamp margin so feet never sit on the paint
CLAMP_MARGIN_Y = 0.5

Vec3 = Tuple[float, float, float]
Vec2 = Tuple[float, float]

# -------------------------------
# Helper utilities
# -------------------------------

def _clamp_y(y: float, *, margin: float = CLAMP_MARGIN_Y) -> float:
    low = TOUCHLINE_BOTTOM_Y + margin
    high = TOUCHLINE_TOP_Y - margin
    return max(low, min(high, y))


def _auto_compress_y(points: List[Vec2], touch_y: float, safe_band: float) -> List[Vec2]:
    """If any point would spill beyond a touch-safe band from a touchline, compress Y deltas toward touch.
    touch_y is 0 (bottom) or 70 (top). safe_band is positive (e.g., 6..8m).
    """
    if not points:
        return points
    # Determine direction: for bottom touch (0), allowed band is [0, +safe_band];
    # for top touch (70), allowed band is [70-safe_band, 70].
    out: List[Vec2] = []
    if touch_y <= (TOUCHLINE_BOTTOM_Y + 0.1):
        # Bottom touchline
        base = TOUCHLINE_BOTTOM_Y
        for x, y in points:
            dy = min(max(y - base, 0.0), safe_band)
            out.append((x, base + dy))
    else:
        base = TOUCHLINE_TOP_Y
        for x, y in points:
            dy = min(max(base - y, 0.0), safe_band)
            out.append((x, base - dy))
    return out


def local_to_world(px_local: float, py_local: float, mark_xy: Vec2, attack_dir: float) -> Vec2:
    """Flip local +X by attack_dir and translate from mark. +Y is always towards top touchline in local frame."""
    mx, my = mark_xy
    wx = mx + attack_dir * px_local
    wy = my + py_local
    return (wx, _clamp_y(wy))


def fan_along_y(center_y: float, n: int, gap: float) -> List[float]:
    if n <= 0:
        return []
    if n == 1:
        return [_clamp_y(center_y)]
    # symmetric fan around center: e.g., for 4 => [-1.5,-0.5,0.5,1.5]*gap
    idxs = [i - (n - 1) / 2.0 for i in range(n)]
    ys = [center_y + k * gap for k in idxs]
    return [_clamp_y(y) for y in ys]


def nearest_role(team, rn: int, fallback: Iterable[int] | None = None):
    """Return Player with exact RN if present; otherwise try fallback list of RNs; else None."""
    p = team.get_player_by_rn(rn)
    if p:
        return p
    if fallback:
        for alt in fallback:
            q = team.get_player_by_rn(alt)
            if q:
                return q
    return None


# -------------------------------
# Scrum
# -------------------------------

# Local template (attacking team frame)
_SCRUM_LOCAL = {
    1: (0.0, -SCRUM_ROW_GAP_Y),      # LH
    2: (0.2, 0.0),                   # Hooker slightly +X
    3: (0.0, +SCRUM_ROW_GAP_Y),      # TH
    4: (SCRUM_LOCK_BACK_X, -0.4),
    5: (SCRUM_LOCK_BACK_X, +0.4),
    6: (SCRUM_BACKROW_BACK_X, -1.1),
    7: (SCRUM_BACKROW_BACK_X, +1.1),
    8: (SCRUM_NO8_X, 0.0),
    # backs default (will be refined via exit call)
    9: (+1.0, -SCRUM_9_SIDE_OFFSET_Y),
    10: (+7.0, -1.0),
    12: (+6.0, -3.0),
    13: (+6.5, -4.5),
    11: (+8.0, -6.0),
    14: (+8.0, +6.0),
    15: (-10.0, 0.0),
}


def _scrum_def_mirror(xy_local: Vec2) -> Vec2:
    # Mirror along the Y axis in local frame (flip X only)
    return (-xy_local[0], xy_local[1])


def get_scrum_formation(mark_xy: Vec2, put_in_team: str, match) -> Dict[object, Vec3]:
    """Return targets for *both* teams at a scrum mark. Attacking team = put_in_team.
    Keys are Player objects; values are (x, y, 0.0).
    """
    ax = (match.team_a if put_in_team == 'a' else match.team_b).tactics.get("attack_dir", +1.0)
    defx = (match.team_a if put_in_team != 'a' else match.team_b).tactics.get("attack_dir", -1.0)

    attack = match.team_a if put_in_team == 'a' else match.team_b
    defend = match.team_b if put_in_team == 'a' else match.team_a

    # Decide 9 side based on touch proximity
    _, my = mark_xy
    nine_side = -SCRUM_9_SIDE_OFFSET_Y if my < ( (TOUCHLINE_BOTTOM_Y + TOUCHLINE_TOP_Y) / 2.0 ) else +SCRUM_9_SIDE_OFFSET_Y

    targets: Dict[object, Vec3] = {}

    # --- Attacking pack & default backs ---
    for rn, (lx, ly) in _SCRUM_LOCAL.items():
        ly_adj = ly
        if rn == 9:
            ly_adj = nine_side
        p = nearest_role(attack, rn)
        if not p:
            continue
        wx, wy = local_to_world(lx, ly_adj, mark_xy, ax)
        targets[p] = (wx, wy, 0.0)

    # --- Defending pack: mirror in local, then world-transform by their attack dir
    for rn, (lx, ly) in _SCRUM_LOCAL.items():
        if rn in (10, 11, 12, 13, 14, 15):
            # Defending backs handled by defensive helper below
            continue
        mx_lx, mx_ly = _scrum_def_mirror((lx, ly))
        p = nearest_role(defend, rn)
        if not p:
            continue
        wx, wy = local_to_world(mx_lx, mx_ly, mark_xy, defx)
        targets[p] = (wx, wy, 0.0)

    # Defending backs line 3m off last feet (~No8 x in attack local → tail in world)
    tail_local_x = _SCRUM_LOCAL[8][0]
    tail_world_x, _ = local_to_world(tail_local_x, 0.0, mark_xy, ax)
    backs_line_x = tail_world_x - (ax * 3.0)  # 3m behind from attack POV

    # Place defending backs fanned across Y
    def_backs = [q for q in defend.squad if q.rn in {9,10,11,12,13,14,15}]
    def_backs_sorted = sorted(def_backs, key=lambda pl: (pl.rn, pl.sn))
    fan_y = fan_along_y(my, len(def_backs_sorted), 3.0)
    for py, pl in zip(fan_y, def_backs_sorted):
        targets[pl] = (backs_line_x, py, 0.0)

    return targets


# -------------------------------
# Exit shapes for scrum winners
# -------------------------------

def place_backs_exit_shape(exit_call: str, winner_team: str, mark_xy: Vec2, match) -> Dict[object, Vec3]:
    team = match.team_a if winner_team == 'a' else match.team_b
    dir_ = float(team.tactics.get("attack_dir", +1.0))

    # Base from scrum local template
    base = dict(_SCRUM_LOCAL)

    if exit_call == "8_pick":
        # Shift 8 slightly to pick-up lane; 9 inside; 10 flatter; wings tuck a touch
        base[8] = (base[8][0] + 0.5, base[8][1] + (-0.5 if base[9][1] < 0 else +0.5))
        base[9] = (+0.5, base[9][1]*0.8)
        base[10] = (+5.5, -1.5)
        base[11] = (base[11][0] - 0.8, base[11][1] * 0.9)
        base[14] = (base[14][0] - 0.8, base[14][1] * 0.9)
    elif exit_call == "9_box":
        base[9] = (+0.6, ( -1.8 if base[9][1] < 0 else +1.8))
        # use 11 & 7 (or 14 & 6) as chasers down tram
        # Keep template; state logic can tag these as chasers via meta if needed
    elif exit_call == "10_exit":
        base[9] = (+1.0, base[9][1])
        base[10] = (+7.0, -1.0)
        base[12] = (+LINEOUT_INFIELD_BUFFER_X, -3.0)
        base[15] = (+4.0, -2.5)

    # Materialize only backs + 8/9
    target_rns = {8,9,10,11,12,13,14,15}
    out: Dict[object, Vec3] = {}
    for rn, (lx, ly) in base.items():
        if rn not in target_rns:
            continue
        p = nearest_role(team, rn)
        if not p:
            continue
        wx, wy = local_to_world(lx, ly, mark_xy, dir_)
        out[p] = (wx, wy, 0.0)
    return out


# -------------------------------
# Lineout
# -------------------------------

# Zones are placed along +X infield from touch mark.
_LINEOUT_ZONE_X = {
    "front": 1.0,
    "mid": 3.0,
    "back": 5.0,
}


def _lineout_attack_pods(call: dict, touch_y: float) -> List[Tuple[str, float]]:
    """Return a list of (zone_name, center_x_local) to populate based on numbers.
    For 5-man: front+mid; 6-man: front+mid plus decoy/back; 7-man: all three.
    """
    order = ["front", "mid", "back"]
    zones = []
    nums = int(call.get("numbers", 7))
    if nums <= 5:
        zones = ["front", "mid"]
    elif nums == 6:
        zones = ["front", "mid", "back"]
    else:
        zones = order
    # Map to x centers
    return [(z, _LINEOUT_ZONE_X[z]) for z in zones]


def get_lineout_formation(mark_xy: Vec2, throw_to_team: str, call: dict, match) -> dict:
    """Build attacking lineout (pods + backs) and return {Player: (x,y,0.0)} with meta.
    Local frame: +X infield; +Y along touch towards top.
    call = {"zone":"front|mid|back", "length":"short|mid|long", "outcome":"off_top|maul", "numbers":5|6|7}
    """
    team = match.team_a if throw_to_team == 'a' else match.team_b
    opp = match.team_b if throw_to_team == 'a' else match.team_a
    dir_ = float(team.tactics.get("attack_dir", +1.0))

    mx, my = mark_xy
    touch_is_bottom = my <= (TOUCHLINE_BOTTOM_Y + 0.1)
    y_sign = +1.0 if touch_is_bottom else -1.0  # +Y should be inward from touch into field

    targets: Dict[object, Vec3] = {}
    meta: Dict[str, object] = {}

    # Hooker (2) on touch side to throw
    hook = nearest_role(team, 2, fallback=[16])
    if hook:
        wx, wy = local_to_world(-1.0, 0.0 * y_sign, mark_xy, dir_)
        targets[hook] = (wx, wy, 0.0)

    # Build pods
    pods = _lineout_attack_pods(call, my)

    # Choose jumper RN preference 4/5/6 (fallback to any forward)
    jumper_pref = [4, 5, 6]
    lifter_pref = [1, 3, 7]

    used: set = set()

    def alloc(role_list: List[int]) -> Optional[object]:
        for rn in role_list:
            p = nearest_role(team, rn)
            if p and p not in used:
                used.add(p)
                return p
        # fallback to any unused forward
        for p in sorted([q for q in team.squad if q.rn in {1,2,3,4,5,6,7,8}], key=lambda u:(u.rn, u.sn)):
            if p not in used:
                used.add(p)
                return p
        return None

    jumper_zone = call.get("zone", "mid")
    meta["pod"] = jumper_zone

    # Place requested pods; mark the primary jumper as per call.zone
    catch_xy_world: Optional[Vec2] = None

    for z_name, cx in pods:
        center_y_local = 0.0
        # Pod members: lifter-jumper-lifter across Y
        left_lifter = alloc(lifter_pref)
        jumper = alloc([4,5,6])
        right_lifter = alloc(lifter_pref)
        members = [left_lifter, jumper, right_lifter]
        local_points: List[Vec2] = []
        for i, m in enumerate(members):
            if not m:
                continue
            ly = center_y_local + ( (i - 1) * LINEOUT_LIFTER_OFFSET_Y * y_sign )
            local_points.append((cx, ly))
        # Touch safety compression
        local_points = _auto_compress_y(local_points, my, LINEOUT_TOUCH_SAFE_Y)
        # Emit
        for (lx, ly), m in zip(local_points, members):
            if not m:
                continue
            wx, wy = local_to_world(lx, ly, mark_xy, dir_)
            targets[m] = (wx, wy, 0.0)
        if z_name == jumper_zone and jumper:
            wx, wy = local_to_world(cx, center_y_local, mark_xy, dir_)
            catch_xy_world = (wx, wy)
            meta["jumper_sn"] = jumper.sn
            meta["catch_xy"] = (wx, wy, 1.9)  # nominal lift height for future animation

    # 9 inside, ready for off-top
    nine = nearest_role(team, 9)
    if nine:
        wx, wy = local_to_world(2.0, -2.0 * y_sign, mark_xy, dir_)
        targets[nine] = (wx, wy, 0.0)

    # 10/12/13 staggered infield
    for rn, (lx, ly) in [(10, (8.0, -2.0*y_sign)), (12, (9.0, -3.5*y_sign)), (13, (10.0, -5.0*y_sign))]:
        p = nearest_role(team, rn)
        if p:
            wx, wy = local_to_world(lx, ly, mark_xy, dir_)
            targets[p] = (wx, wy, 0.0)

    # Wings
    w_far = nearest_role(team, 14 if y_sign > 0 else 11)
    w_near = nearest_role(team, 11 if y_sign > 0 else 14)
    if w_far:
        wx, wy = local_to_world(12.0, -6.0*y_sign, mark_xy, dir_)
        targets[w_far] = (wx, wy, 0.0)
    if w_near:
        wx, wy = local_to_world(2.0, +3.5*y_sign, mark_xy, dir_)  # near wing can sit contest/backfield
        targets[w_near] = (wx, wy, 0.0)

    # 15 backfield
    fb = nearest_role(team, 15)
    if fb:
        wx, wy = local_to_world(-5.0, -2.0*y_sign, mark_xy, dir_)
        targets[fb] = (wx, wy, 0.0)

    return {"targets": targets, "meta": meta}


# -------------------------------
# Defensive set-piece placement
# -------------------------------

def place_defensive_setpiece(team_def, setpiece_meta: dict, match) -> Dict[object, Vec3]:
    t = setpiece_meta.get("type")
    mark_xy: Vec2 = setpiece_meta.get("mark", (0.0, 35.0))
    dir_ = float(team_def.tactics.get("attack_dir", +1.0))
    mx, my = mark_xy
    out: Dict[object, Vec3] = {}

    if t == "scrum":
        # Forwards mirror pack around mark (roughly a defensive scrum bind)
        # Backs line 3m off last feet from attack POV handled in get_scrum_formation, but ensure fallback here
        defs = sorted([p for p in team_def.squad if p.rn in {9,10,11,12,13,14,15}], key=lambda u:(u.rn,u.sn))
        ys = fan_along_y(my, len(defs), 3.0)
        # Position slightly behind mark along attack POV (towards own tryline)
        line_x = mx - dir_ * 3.0
        for y, p in zip(ys, defs):
            out[p] = (line_x, y, 0.0)
        return out

    if t == "lineout":
        # Contest at called zone: align a jumper pod opposite
        zone = setpiece_meta.get("zone", "mid")
        cx = _LINEOUT_ZONE_X.get(zone, 3.0)
        y_sign = (+1.0 if my <= (TOUCHLINE_BOTTOM_Y + 0.1) else -1.0)
        # Place defensive pod across Y at the same x, slightly infield of touch lane
        pod_y0 = 0.0
        pts_local = _auto_compress_y([(cx, pod_y0 - LINEOUT_LIFTER_OFFSET_Y * y_sign),
                                      (cx, pod_y0),
                                      (cx, pod_y0 + LINEOUT_LIFTER_OFFSET_Y * y_sign)], my, LINEOUT_TOUCH_SAFE_Y)
        defenders = sorted([p for p in team_def.squad if p.rn in {4,5,6,1,3,7}], key=lambda u:(u.rn,u.sn))
        for (lx, ly), p in zip(pts_local, defenders):
            wx, wy = local_to_world(lx, ly, mark_xy, dir_)
            out[p] = (wx, wy, 0.0)
        # Line for backs 10m from mark if not in contest
        backs = [p for p in team_def.squad if p.rn in {9,10,11,12,13,14,15}]
        line_x = mx + dir_ * 12.0
        ys = fan_along_y(my, len(backs), 3.0)
        for y, p in zip(ys, backs):
            out[p] = (line_x, y, 0.0)
        return out

    if t == "maul":
        anchor_xy: Vec2 = setpiece_meta.get("anchor", mark_xy)
        ax, ay = anchor_xy
        # 2–4 defenders form a front arc counter-ring
        cand = sorted([p for p in team_def.squad if p.rn in {1,2,3,4,5,6,7,8}], key=lambda u:(u.rn,u.sn))[:4]
        for i, p in enumerate(cand):
            # front arc points in front of maul (+X from attack POV)
            s = -1.5 + i * (3.0 / max(1,len(cand)-1))
            wx = ax + dir_ * (MAUL_RING_RADIUS_X * 0.9)
            wy = _clamp_y(ay + s * (MAUL_RING_RADIUS_Y * 0.9))
            out[p] = (wx, wy, 0.0)
        return out

    return out


# -------------------------------
# Maul ring
# -------------------------------

def get_maul_ring(anchor_xy: Vec2, team, size_meta: dict, match) -> Dict[object, Vec3]:
    count = int(size_meta.get("count", 6))
    bias = size_meta.get("bias", "tight")  # "tight" | "loose"
    dir_ = float(team.tactics.get("attack_dir", +1.0))
    ax, ay = anchor_xy

    forwards = sorted([p for p in team.squad if p.rn in {1,2,3,4,5,6,7,8}], key=lambda u:(u.rn,u.sn))
    binders = forwards[:max(0, min(count, len(forwards)))]

    # Distribute around an ellipse; biased to front arc (+X)
    out: Dict[object, Vec3] = {}
    if not binders:
        return out

    # Angle span: heavier density on front half
    span_front = 150 if bias == "tight" else 120
    # Angles from -span/2 .. +span/2 centered on +X
    import math
    for i, p in enumerate(binders):
        t = (i + 0.5) / len(binders)  # (0,1]
        ang_deg = -span_front/2 + t * span_front
        ang_rad = math.radians(ang_deg)
        ex = MAUL_RING_RADIUS_X * math.cos(ang_rad)
        ey = MAUL_RING_RADIUS_Y * math.sin(ang_rad)
        wx = ax + dir_ * ex
        wy = _clamp_y(ay + ey)
        out[p] = (wx, wy, 0.0)

    # Scrum-half support pocket behind maul
    nine = nearest_role(team, 9)
    if nine:
        out[nine] = (ax - dir_ * abs(MAUL_9_POCKET_X), _clamp_y(ay), 0.0)

    return out


__all__ = [
    "get_scrum_formation",
    "get_lineout_formation",
    "get_maul_ring",
    "place_backs_exit_shape",
    "place_defensive_setpiece",
    "local_to_world",
    "fan_along_y",
    "nearest_role",
]