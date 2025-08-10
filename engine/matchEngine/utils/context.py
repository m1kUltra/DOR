# utils/context.py
from math import atan2
from typing import Dict
from constants import (
    MAX_DEF_CONSIDERED, MAX_PASS_CANDIDATES, MAX_CHASERS,
    TOUCHLINE_BOTTOM_Y, TOUCHLINE_TOP_Y,
)

def build_context(match) -> Dict:
    """
    Single per-tick snapshot for the decision layers.
    """
    ball = match.ball
    bx, by, bz = ball.location
    holder = ball.holder
    in_flight = bool(ball.in_flight)

    def slim(team_code: str):
        team = match.team_a if team_code == 'a' else match.team_b
        arr = []
        for p in sorted(team.squad, key=lambda pp: (pp.rn, pp.sn)):
            x, y, _ = p.location
            arr.append({"sn": p.sn, "rn": p.rn, "x": x, "y": y, "code": f"{p.sn}{p.team_code}", "obj": p})
        return {
            "dir": float(team.tactics.get("attack_dir", +1.0)),
            "in_possession": bool(team.in_possession),
            "players": arr,
            "holder_sn": int(holder[:-1]) if holder and holder.endswith(team_code) else None,
        }

    teams = {"a": slim('a'), "b": slim('b')}

    poss_code = 'a' if (holder and holder.endswith('a')) else ('b' if (holder and holder.endswith('b')) else None)
    zone = None
    if poss_code:
        dir_ = teams[poss_code]["dir"]
        proj = bx if dir_ > 0 else (100.0 - bx)
        if proj <= 22:
            zone = "own_22"
        elif proj <= 50:
            zone = "own_half"
        elif proj <= 78:
            zone = "opp_half" if proj > 50 else "mid"
        else:
            zone = "opp_22"

    def build_defense_map(attacking: str):
        defending = 'b' if attacking == 'a' else 'a'
        defs = teams[defending]["players"]

        nearest = []
        for d in defs:
            dx, dy = d["x"] - bx, d["y"] - by
            dist = (dx*dx + dy*dy) ** 0.5
            ang = atan2(dy, dx)
            nearest.append((d["sn"], dist, dx, dy, ang))
        nearest.sort(key=lambda t: (t[1], t[0]))  # stable
        nearest = nearest[:MAX_DEF_CONSIDERED]

        max_def_y = max((p["y"] for p in defs), default=by)
        min_def_y = min((p["y"] for p in defs), default=by)
        edge_space = {
            "low":  max(0.0, by - min_def_y),   # toward y=0
            "high": max(0.0, max_def_y - by),   # toward y=70
        }

        # simple 12m band ahead of ball from defense POV
        dir_def = teams[defending]["dir"]
        line_density = sum(1 for d in defs if 0 < (d["x"] - bx) * dir_def <= 12.0)

        return {
            "nearest_to_holder": nearest,
            "line_density": line_density,
            "edge_space": edge_space,
        }

    defense_map = build_defense_map(poss_code) if poss_code else None

    return {
        "ball": {"x": bx, "y": by, "z": bz, "holder_code": holder, "in_flight": in_flight},
        "teams": teams,
        "zone": zone,
        "defense_map": defense_map,
        "score_time": dict(match.period),
        "advantage": match.advantage,
        "caps": {
            "MAX_PASS_CANDIDATES": MAX_PASS_CANDIDATES,
            "MAX_DEF_CONSIDERED": MAX_DEF_CONSIDERED,
            "MAX_CHASERS": MAX_CHASERS
        },
        "_rng": match.rng,
        "_tick": match.tick_count,
        "_match": match,
    }
