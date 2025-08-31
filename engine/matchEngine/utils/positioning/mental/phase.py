# utils/positioning/phase.py
from typing import Dict, Tuple
from utils.positioning.mental.formations import fan_along_y, local_to_world, nearest_role

Vec3 = Tuple[float,float,float]
Vec2 = Tuple[float,float]
# engine/matchEngine/utils/positioning/mental/phase.py
from typing import Dict, Tuple
from utils.positioning.mental.position_utils import (
    forwards_shape_positions,
    backline_shape_positions,
)

def phase_attack_targets(
    match,
    side: str,
    ruck_xy: Vec2,
) -> Dict[object, Vec3]:
    rx, ry = ruck_xy
    team = match.team_a if side == "a" else match.team_b
    ball_loc: Vec3 = (rx, ry, 0.0)

    targets: Dict[object, Vec3] = {}

    # --- Forwards: create a lane/pod layout for ALL 1..8 ---
    forwards = sorted(
        [p for p in team.squad if p.rn in {1,2,3,4,5,6,7,8}],
        key=lambda pl: (pl.rn, pl.sn),
    )
    for i, p in enumerate(forwards):
        targets[p] = forwards_shape_positions(team, ball_loc, p.rn, i)

    # --- Backs: 9 handled as DH upstream; place the rest relative to ball ---
    backs = sorted(
        [p for p in team.squad if p.rn in {10,11,12,13,14,15}],
        key=lambda pl: (pl.rn, pl.sn),
    )
    squad_n = len(team.squad) or 15
    for p in backs:
        targets[p] = backline_shape_positions(team, ball_loc, p.rn, squad_n)

    return targets


def phase_defence_targets(
    match,
    side_def: str,
    ruck_xy: Vec2,
    *,
    line_depth: float = -2,
    gap: float = 3.0,
) -> Dict[object, Vec3]:
    rx, ry = ruck_xy
    team = match.team_a if side_def == "a" else match.team_b
    dir_ = float((team.tactics or {}).get("attack_dir", +1.0))

    # Flat line in front of the ball (toward attackers) along defender's own attack_dir
    line_x, _ = local_to_world(+line_depth, 0.0, (rx, ry), dir_)

    # Everyone on this team who isn't in the ruck
    defs = [
        p for p in sorted(team.squad, key=lambda u: (u.rn, u.sn))
        if not getattr(p, "state_flags", {}).get("in_ruck", False)
    ]

    # Evenly fan along Y around ball.y
    ys = fan_along_y(ry, len(defs), gap)

    return {p: (line_x, y, 0.0) for p, y in zip(defs, ys)}
