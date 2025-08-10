# matchEngine/utils/position_utils.py
from typing import Tuple
from constants import (
    TOUCHLINE_TOP_Y, TOUCHLINE_BOTTOM_Y,
    TRYLINE_A_X, TRYLINE_B_X
)

def _clamp_y(y: float, margin: float) -> float:
    """
    Clamp Y inside touchlines. If margin <= 0, players can stand right on the line.
    """
    low = TOUCHLINE_BOTTOM_Y + max(0.0, margin)
    high = TOUCHLINE_TOP_Y - max(0.0, margin)
    if low > high:  # pathological margin; fall back to hard bounds
        low, high = TOUCHLINE_BOTTOM_Y, TOUCHLINE_TOP_Y
    return max(low, min(high, y))

def _ahead(bx: float, dir_: float, dx: float) -> float:
    # "ahead" means towards opposition tryline from this team's POV
    return bx + dir_ * dx

def backline_shape_positions(team, ball_loc, rn: int, squad_n: int) -> Tuple[float,float,float]:
    t = team.tactics
    bx, by, _ = ball_loc
    dir_ = t.get("attack_dir", +1.0)

    depth10     = t["attack_depth_10"]
    gap         = t["backline_lateral_gap"]
    min_behind  = t["backline_min_behind"]
    wing_margin = t["far_wing_margin"]

    z = 0.0
    clamp_y = lambda y: _clamp_y(y, wing_margin)

    if rn == 9:
        # service lane just off ball
        y = clamp_y(by + (1.5 if (squad_n % 2) else -1.5))
        x = _ahead(bx, dir_, -1.0)
        return (x, y, z)

    if rn == 10:
        y = clamp_y(by + gap * 0.2)
        raw = _ahead(bx, dir_, -depth10)
        x = min(raw, bx - min_behind) if dir_ > 0 else max(raw, bx + min_behind)
        return (x, y, z)

    if rn in (12, 13):
        lane = 1 if rn == 12 else 2
        y = clamp_y(by + lane * gap)
        raw = _ahead(bx, dir_, -(depth10 - 2.0))
        x = min(raw, bx - min_behind) if dir_ > 0 else max(raw, bx + min_behind)
        return (x, y, z)

    if rn in (11, 14):
        # wings near edges; honor margin (0 means right on the line)
        y = (TOUCHLINE_BOTTOM_Y + wing_margin) if rn == 11 else (TOUCHLINE_TOP_Y - wing_margin)
        raw = _ahead(bx, dir_, -(depth10 - 1.0))
        x = min(bx - min_behind, raw) if dir_ > 0 else max(bx + min_behind, raw)
        return (x, y, z)

    if rn == 15:
        # median x toward own tryline, same y as ball
        own_try_x = TRYLINE_A_X if dir_ > 0 else TRYLINE_B_X
        x = (bx + own_try_x) / 2.0
        return (x, clamp_y(by), z)

    # default back
    y = clamp_y(by + gap)
    raw = _ahead(bx, dir_, -depth10)
    x = min(raw, bx - min_behind) if dir_ > 0 else max(raw, bx + min_behind)
    return (x, y, z)

def forward_pod_lane(index0: int) -> int:
    # 1-3-3-1-ish: [-1] [0,0,0] [+1,+1,+1] [+1]
    if index0 == 0: return -1
    if 1 <= index0 <= 3: return 0
    if 4 <= index0 <= 6: return +1
    return +1

def forwards_shape_positions(team, ball_loc, rn: int, ordinal_in_forwards: int) -> Tuple[float,float,float]:
    t = team.tactics
    bx, by, _ = ball_loc
    dir_ = t.get("attack_dir", +1.0)

    pod_gap     = t["pod_gap"]
    pod_depth   = t["pod_depth"]
    min_behind  = t["backline_min_behind"]
    wing_margin = t["far_wing_margin"]

    z = 0.0
    clamp_y = lambda y: _clamp_y(y, wing_margin)

    lane = forward_pod_lane(ordinal_in_forwards)
    y = clamp_y(by + lane * pod_gap)
    x = _ahead(bx, dir_, -pod_depth)
    if dir_ > 0:
        x = min(x, bx - min_behind)
    else:
        x = max(x, bx + min_behind)
    return (x, y, z)
