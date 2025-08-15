from typing import Optional, Dict, List, Tuple
from constants import (
    FORWARD_PASS_EPS, KNOCK_ON_FORWARD_METERS, OFFSIDE_OPENPLAY_BUFFER,
    FIFTY22_MIN_ORIGIN, FIFTY22_TARGET_MINX
)

def _sign(v: float) -> int:
    return 1 if v >= 0 else -1

def detect_forward_pass(match, prev_holder_loc, new_holder_loc, attack_dir) -> Optional[Dict]:
    # Baseline: if receiver is ahead of passer in attack direction by > eps
    if not prev_holder_loc or not new_holder_loc:
        return None
    px, _, _ = prev_holder_loc
    rx, ry, rz = new_holder_loc
    if attack_dir >= 0:
        forward = (rx - px) > FORWARD_PASS_EPS
    else:
        forward = (px - rx) > FORWARD_PASS_EPS
    if forward:
        team = match.last_touch_team
        return {"type":"forward_pass","x":px,"y":ry,"team":team}
    return None

def detect_knock_on(match, last_touch_team, prev_ball_loc, new_ball_loc, attack_dir) -> Optional[Dict]:
    if not prev_ball_loc or not new_ball_loc:
        return None
    px, _, _ = prev_ball_loc
    nx, ny, nz = new_ball_loc
    if last_touch_team is None:
        return None
    # Forward delta while ball becomes loose (no holder now)
    if getattr(match.ball, "holder", None):
        return None
    delta = (nx - px) if attack_dir >= 0 else (px - nx)
    if delta > KNOCK_ON_FORWARD_METERS:
        return {"type":"knock_on","x":px,"y":ny,"team": last_touch_team}
    return None

def detect_touch(match, prev_ball_loc, new_ball_loc, last_touch_team) -> Optional[Dict]:
    # rely on pitch bounds: if now out of bounds and previously in
    if not prev_ball_loc or not new_ball_loc:
        return None
    was_in = match.pitch.is_in_play(prev_ball_loc)
    now_out = match.pitch.is_out_of_bounds(new_ball_loc)
    if was_in and now_out:
        x,y,_ = new_ball_loc
        other = 'a' if last_touch_team=='b' else 'b'
        return {"type":"into_touch","x":x,"y":y,"to": other}
    return None

def detect_offside_open_play(match) -> List[Dict]:
    evs = []
    lk = getattr(match, "last_kick", None)
    if not lk:
        return evs
    # If any teammate ahead of kick point interferes within small buffer (very simplified)
    team = lk.get("team")
    kx = lk.get("x", 0.0)
    # Check nearest contestor
    for p in match.players_for_team(team):
        px, py, pz = getattr(p, "location", (0,0,0))
        ahead = (px > kx + OFFSIDE_OPENPLAY_BUFFER) if match.get_attack_dir(team) >= 0 else (px < kx - OFFSIDE_OPENPLAY_BUFFER)
        if ahead and match.can_interfere(p):  # stub hooks expected in engine
            other = 'a' if team=='b' else 'b'
            evs.append({"type":"penalty","mark": (px, py), "to": other, "reason": "offside_kick"})
            break
    return evs

def detect_goal_line_dropout(match) -> Optional[Dict]:
    # If attackers kicked dead in-goal or defender grounded → goal-line DO to defenders.
    # For v1 we look for ball dead behind defenders' goal line with last kick by attackers.
    if getattr(match, "ball_dead", False):
        lk = getattr(match, "last_kick", None)
        if lk:
            atk = lk["team"]
            defend = 'a' if atk=='b' else 'b'
            return {"type":"goal_line_do","to": defend}
    return None

def detect_fifty22(match, kick_ctx, out_event) -> Optional[Dict]:
    """
    Given last completed kick context and an 'into_touch' event, check 50:22:
    - kicker in own half at kick point
    - ball bounced in field, then went into touch
    - cross beyond opponent 22 (attack_dir aware)
    """
    if not kick_ctx or not out_event:
        return None
    team = kick_ctx.get("team")
    if not team:
        return None
    # own half origin
    kx = kick_ctx.get("x", 0.0)
    if match.get_attack_dir(team) >= 0:
        in_own_half = kx <= FIFTY22_MIN_ORIGIN
        past_22 = out_event["x"] >= FIFTY22_TARGET_MINX
    else:
        in_own_half = kx >= (100.0 - FIFTY22_MIN_ORIGIN)
        past_22 = out_event["x"] <= (100.0 - FIFTY22_TARGET_MINX)
    if not (in_own_half and kick_ctx.get("bounced", False) and past_22):
        return None
    return {"type":"into_touch_50_22","x": out_event["x"], "y": out_event["y"], "to": team}
