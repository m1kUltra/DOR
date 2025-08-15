# utils/attackAI/offense.py
from typing import Optional, Tuple
from math import cos, sin
from constants import (
    EPS, PASS_MAX_RANGE, RUN_PROBE_LEN, TOUCHLINE_BOTTOM_Y, TOUCHLINE_TOP_Y,
    PITCH_WIDTH, CROSSFIELD_MIN_SPACE,
)
from utils.attackAI.helpers import forward_ray_vectors

def evaluate_pass_targets(holder, ctx) -> Optional[dict]:
    rng, tick = ctx["_rng"], ctx["_tick"]
    hcode = f"{holder.sn}{holder.team_code}"
    bx, by = ctx["ball"]["x"], ctx["ball"]["y"]
    team = ctx["teams"][holder.team_code]
    dir_ = team["dir"]
    mates = sorted([p for p in team["players"] if p["code"] != hcode], key=lambda m: (m["rn"], m["sn"]))

    cands = []
    for m in mates:
        dx, dy = m["x"] - bx, m["y"] - by
        legal = (dx <= EPS) if dir_ > 0 else (dx >= -EPS)
        if not legal:
            continue
        d2 = dx*dx + dy*dy
        if d2 > PASS_MAX_RANGE * PASS_MAX_RANGE:
            continue
        cands.append((m, d2))
    cands.sort(key=lambda t: (t[1], t[0]["rn"], t[0]["sn"]))
    cands = cands[:ctx["caps"]["MAX_PASS_CANDIDATES"]]
    if not cands:
        return None

    defs = ctx.get("defense_map", {}).get("nearest_to_holder", [])

    def space_ahead_norm(mx, my) -> float:
        best = None
        for _, dist, dx, dy, _ in defs:
            if (dx*dir_) > 0 and abs(dy) <= 12.0:
                best = dist if best is None else min(best, dist)
        return 0.0 if best is None else min(best, 12.0)/12.0

    best_m, best_u = None, -1.0
    for m, _ in cands:
        space_ahead = space_ahead_norm(m["x"], m["y"])
        gain_x = max(0.0, (m["x"] - bx) * dir_) / PASS_MAX_RANGE
        sideline_clearance = min(m["y"] - TOUCHLINE_BOTTOM_Y, TOUCHLINE_TOP_Y - m["y"]) / 10.0
        chain = 0
        for n in mates:
            if n["code"] == m["code"]:
                continue
            ndx, ndy = n["x"] - m["x"], n["y"] - m["y"]
            legal2 = (ndx <= EPS) if dir_ > 0 else (ndx >= -EPS)
            if legal2 and (ndx*ndx + ndy*ndy) <= 100.0:
                chain += 1
        chain_opt = min(chain, 5)/5.0
        u = 0.4*space_ahead + 0.3*gain_x + 0.2*chain_opt + 0.1*sideline_clearance
        if abs(u - best_u) <= 1e-12:
            tb = rng.randf("pass_tie", tick, key=holder.sn*100 + m["sn"])
            if tb < 0.5:
                continue
        if u > best_u:
            best_u = u; best_m = m

    if not best_m:
        return None
    return {"target": best_m["obj"], "score": float(best_u), "target_xy": (best_m["x"], best_m["y"])}

def compute_run_lane(holder, ctx) -> Tuple[float, float]:
    bx, by = ctx["ball"]["x"], ctx["ball"]["y"]
    dir_ = ctx["teams"][holder.team_code]["dir"]
    angles = [-35, -20, -10, 0, 10, 20, 35]
    best_score, best_xy = -1e9, (bx + dir_*3.0, by)
    defs = ctx.get("defense_map", {}).get("nearest_to_holder", [])
    step = 2.0
    samples = int(RUN_PROBE_LEN / step)

    for deg in angles:
        fx, fy = forward_ray_vectors(dir_, deg)
        score = 0.0
        last_pt = (bx, by)
        for i in range(1, samples+1):
            px = bx + fx * (i*step)
            py = by + fy * (i*step)
            near = min((((px - (bx+dx))**2 + (py - (by+dy))**2) ** 0.5) for _,_,dx,dy,_ in defs) if defs else 20.0
            safety = min(near, 10.0) / 10.0
            edge = min(py - TOUCHLINE_BOTTOM_Y, TOUCHLINE_TOP_Y - py)
            touch_safe = max(0.0, min(edge, 10.0) / 10.0)
            score += safety * 0.7 + touch_safe * 0.3
            last_pt = (px, py)
        score += 0.5 * max(0.0, (last_pt[0] - bx) * dir_) / RUN_PROBE_LEN
        if score > best_score:
            best_score, best_xy = score, (bx + fx * 3.0, by + fy * 3.0)
    return best_xy

def choose_kick_type(holder, ctx):
    zone = ctx["zone"]
    dm = ctx.get("defense_map") or {}
    line_density = dm.get("line_density", 0)
    nearest = dm.get("nearest_to_holder", [])
    edge = dm.get("edge_space") or {"low": 0, "high": 0}
    by = ctx["ball"]["y"]

    # Clearance
    if zone in {"own_22", "own_half"} and line_density >= 4:
        return ("clearance", 1.0, +0.12 if by < (PITCH_WIDTH/2) else -0.12)
    # Bomb
    if zone in {"mid", "opp_half"} and nearest and nearest[0][1] < 8.0:
        return ("bomb", 0.9, 0.05)
    # Chip
    if nearest and nearest[0][1] < 12.0 and line_density >= 3:
        return ("chip", 0.6, 0.02)
    # Crossfield: choose toward larger edge space
    if edge.get("low", 0) >= CROSSFIELD_MIN_SPACE or edge.get("high", 0) >= CROSSFIELD_MIN_SPACE:
        lat = +0.15 if edge.get("high", 0) > edge.get("low", 0) else -0.15
        return ("crossfield", 0.85, lat)
    # Grubber near opp 22 under pressure
    if zone == "opp_22" and line_density >= 3:
        return ("grubber", 0.5, +0.10 if by < (PITCH_WIDTH/2) else -0.10)
    return None

def score_action_run(holder, ctx, lane_xy) -> float:
    bx = ctx["ball"]["x"]
    dir_ = ctx["teams"][holder.team_code]["dir"]
    forward = max(0.0, (lane_xy[0] - bx) * dir_) / 5.0
    return 0.5 + 0.5*forward

def score_action_pass(holder, ctx, pass_eval) -> float:
    return 0.0 if not pass_eval else float(pass_eval["score"])

def score_action_kick(holder, ctx, kick_tuple) -> float:
    if not kick_tuple:
        return 0.0
    ktype = kick_tuple[0]
    base = {"clearance": 0.75, "bomb": 0.6, "chip": 0.55, "crossfield": 0.65, "grubber": 0.5}.get(ktype, 0.4)
    return base

def choose_offensive_action(holder, ctx):
    pass_eval = evaluate_pass_targets(holder, ctx)
    kick_tuple = choose_kick_type(holder, ctx)
    run_xy = compute_run_lane(holder, ctx)

    u_run  = score_action_run(holder, ctx, run_xy)
    u_pass = score_action_pass(holder, ctx, pass_eval)
    u_kick = score_action_kick(holder, ctx, kick_tuple)

    best_u = max(u_run, u_pass, u_kick)
    rng, tick = ctx["_rng"], ctx["_tick"]

    if abs(best_u - u_run) <= 1e-12 and abs(best_u - u_pass) <= 1e-12 and abs(best_u - u_kick) <= 1e-12:
        tb = rng.randf("action_tie", tick, key=holder.sn)
        pick = "run" if tb < 1/3 else ("pass" if tb < 2/3 else "kick")
    elif best_u == u_run:
        pick = "run"
    elif best_u == u_pass:
        pick = "pass"
    else:
        pick = "kick"

    if pick == "run":
        return ("run", (run_xy[0], run_xy[1], 0.0), None)
    if pick == "pass":
        tgt = pass_eval["target"]
        return ("pass", tgt.location, {"target_sn": tgt.sn})
    return ("kick", None, {"kick_tuple": kick_tuple})
