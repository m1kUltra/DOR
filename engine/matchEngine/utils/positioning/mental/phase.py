# utils/positioning/phase.py
from typing import Dict, Tuple
from utils.positioning.mental.formations import fan_along_y, local_to_world, nearest_role

Vec3 = Tuple[float,float,float]
Vec2 = Tuple[float,float]

def phase_attack_targets(match, side: str, ruck_xy: Vec2,
                         *, pod_depth=2.0, pod_gap=4.0, backs_gap=7.0, min_behind=3.0) -> Dict[object, Vec3]:
    rx, ry = ruck_xy
    team = match.team_a if side=="a" else match.team_b
    dir_ = float((team.tactics or {}).get("attack_dir", +1.0))

    targets: Dict[object, Vec3] = {}

    # Forwards pod: use two nearest forwards (prefer 1–8 via nearest_role)
    f1 = nearest_role(team, 3, fallback=[1,4,5,6,7,8])
    f2 = nearest_role(team, 1, fallback=[3,4,5,6,7,8])
    for i, p in enumerate([x for x in [f1, f2] if x]):
        lx = -pod_depth
        ly = (-pod_gap if i==0 else +pod_gap)
        wx, wy = local_to_world(lx, ly, (rx, ry), dir_)
        targets[p] = (wx, wy, 0.0)

    # Backs (excluding 9 if used as DH): 10/12/13 + wings/15 fan around ruck.y
    backs = [nearest_role(team, rn) for rn in [10,12,13,11,14,15]]
    backs = [p for p in backs if p]
    ys = fan_along_y(ry, len(backs), backs_gap)
    for p, py in zip(backs, ys):
        wx, wy = local_to_world(-min_behind, py - ry, (rx, ry), dir_)
        targets[p] = (wx, wy, 0.0)

    return targets

def phase_defence_targets(match, side_def: str, ruck_xy: Vec2, *, line_depth=1.5, gap=3.0) -> Dict[object, Vec3]:
    rx, ry = ruck_xy
    team = match.team_a if side_def=="a" else match.team_b
    dir_ = float((team.tactics or {}).get("attack_dir", +1.0))
    # Defence line sits *in front* of the ball toward attackers → +line_depth along their own attack_dir
    line_x, line_y = local_to_world(+line_depth, 0.0, (rx, ry), dir_)
    defs = sorted([p for p in team.squad if p.rn in {9,10,11,12,13,14,15,6,7,8}], key=lambda u:(u.rn,u.sn))
    ys = fan_along_y(ry, len(defs), gap)
    return { p:(line_x, y, 0.0) for p, y in zip(defs, ys) }
