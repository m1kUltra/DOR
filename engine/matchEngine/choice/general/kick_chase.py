# matchEngine/choice/team/kick_chase.py
from typing import List, Tuple, Optional
from utils.actions.catch_windows import can_catch, best_catcher
from utils.actions.jump_helpers import lateral_catch_radius
XYZ    = Tuple[float, float, float]
Action = Tuple[str, Optional[str]]
DoCall = Tuple[str, Action, XYZ, XYZ]   # (player_id, action, location, target)

def _xyz(p) -> XYZ:
    if p is None: return (0.0, 0.0, 0.0)
    if isinstance(p, (list, tuple)):
        if len(p) == 2: return (float(p[0]), float(p[1]), 0.0)
        if len(p) >= 3: return (float(p[0]), float(p[1]), float(p[2]))
    return (0.0, 0.0, 0.0)
def _live_ball_point(ball) -> XYZ:
    """
    While the ball is in the air, chase its transit target (drop zone).
    After it lands (bounced/skid/idle), chase the live ball.location.
    """
    tr = getattr(ball, "transit", None) or {}
    if tr.get("type") == "parabola":
        return _xyz(tr.get("target", getattr(ball, "location", None)))
    return _xyz(getattr(ball, "location", None))

def _team_code_of(team, match) -> str:
    return "a" if team is match.team_a else "b"

def _infer_receiving_team(match):
    """
    Prefer opposite of last_kick.team_code; otherwise nearest-player-to-target heuristic.
    """
    lk = getattr(match, "last_kick", None)
    if isinstance(lk, dict) and "team_code" in lk:
        return match.team_b if lk["team_code"] == "a" else match.team_a

    # Fallback: which side has the nearest player to where the ball is headed?
    tgt = getattr(match.ball, "target", None) or getattr(match.ball, "location", None)
    bx, by, _ = _live_ball_point(match.ball)
    best = {"a": (1e18, None), "b": (1e18, None)}
    for p in getattr(match, "players", []):
        px, py, _ = _xyz(p.location)
        d2 = (px - bx)**2 + (py - by)**2
        code = getattr(p, "team_code", "a")
        if d2 < best[code][0]:
            best[code] = (d2, p)
    return match.team_a if best["a"][0] <= best["b"][0] else match.team_b
CATCH_RADIUS = 1.0  # meters
def plan(match, state_tuple) -> List[DoCall]:
    tag, _loc, _ctx = state_tuple
    if not (isinstance(tag, str) and (tag == "open_play.kick_chase" or tag.startswith("open_play.kick_chase."))):
        return []

    # --- NEW: early catch if ball is within 1m of any player ---
    # live, actual ball position (includes height for catch)
    ball_loc = _xyz(getattr(match.ball, "location", None))

    # quick single-player catch (fast path)
    if 2.0 < ball_loc[2] <= 3.5:
        for p in match.players:
            radius = lateral_catch_radius(p)
            px, py, _ = _xyz(p.location)
            dx, dy = ball_loc[0] - px, ball_loc[1] - py
            if dx * dx + dy * dy <= radius * radius:
                return [(f"{p.sn}{p.team_code}", ("jump", None),
                        (px, py, 0.0), ball_loc)]
    catcher = best_catcher(match.players, ball_loc, radius=1.0, max_height=1.6)
    if catcher and getattr(match.ball, "holder", None) is None:
        return [(f"{catcher.sn}{catcher.team_code}", ("catch", None),
                _xyz(catcher.location), (ball_loc[0], ball_loc[1], 0.0))]

            # single catch action; target = live ball point on ground
            
    # --- existing kick-return formation logic follows ---

    # use live pointer: drop zone while airborne; live location after bounce/skid
    bx, by, _ = _live_ball_point(match.ball)

    recv_team = _infer_receiving_team(match)
    def_team  = match.team_b if recv_team is match.team_a else match.team_a
    recv_code = _team_code_of(recv_team, match)
    def_code  = _team_code_of(def_team, match)

    recv_players = [p for p in match.players if getattr(p, "team_code", None) == recv_code]
    def_players  = [p for p in match.players if getattr(p, "team_code", None) == def_code]

    def _dist2(p):
        px, py, _ = _xyz(p.location)
        return (px - bx)**2 + (py - by)**2

    fielder = min(recv_players, key=_dist2) if recv_players else None

    calls: List[DoCall] = []

    if fielder:
        calls.append((f"{fielder.sn}{fielder.team_code}", ("move", None), _xyz(fielder.location), (bx, by, 0.0)))

    recv_dir = float((getattr(recv_team, "tactics", {}) or {}).get("attack_dir", +1.0))
    def_dir  = float((getattr(def_team,  "tactics", {}) or {}).get("attack_dir", +1.0))

    for p in recv_players:
        if p is fielder:
            continue
        px, py, pz = _xyz(p.location)
        tx = bx - recv_dir * 5.0
        ty = py + (by - py) * 0.20
        calls.append((f"{p.sn}{p.team_code}", ("move", None), (px, py, pz), match.pitch.clamp_position((tx, ty, 0.0))))

    for p in def_players:
        px, py, pz = _xyz(p.location)
        tx = bx + def_dir * 5.0
        ty = py + (by - py) * 0.15
        calls.append((f"{p.sn}{p.team_code}", ("move", None), (px, py, pz), match.pitch.clamp_position((tx, ty, 0.0))))

    return calls

