from typing import Dict, Tuple
from constants import POINTS, CONVERSION_WINDOW_S, CONVERSION_DEFAULT_DIST, CONV_SUCCESS_BASE

def award_try(match, team: str, at_xy: Tuple[float,float]) -> Dict:
    other = 'a' if team=='b' else 'b'
    match.scoreboard[team] = match.scoreboard.get(team, 0) + POINTS['try']
    x,y = at_xy
    deadline = match.match_time + CONVERSION_WINDOW_S
    conv = {"team": team, "spot": (x, y), "deadline_t": deadline}
    match.conversion_ctx = conv
    return {"type":"post_score","next_restart_to": other, "conversion": conv}

def attempt_conversion(match) -> Dict:
    # Simple deterministic success based on seed & tick
    rng = match.rng if hasattr(match, 'rng') else None
    prob = CONV_SUCCESS_BASE
    success = True
    if rng:
        val = rng.randf("conv_kick", match.tick_count, key=0)
        success = (val <= prob)
    if success:
        # Who is converting?
        team = match.conversion_ctx.get("team") if match.conversion_ctx else None
        if team:
            match.scoreboard[team] = match.scoreboard.get(team, 0) + 2
    return {"type":"conversion_result","success": success}

def award_penalty_goal(match, team: str, mark_xy: Tuple[float,float]) -> Dict:
    other = 'a' if team=='b' else 'b'
    match.scoreboard[team] = match.scoreboard.get(team, 0) + 3
    return {"type":"post_score","next_restart_to": other}

def award_drop_goal(match, team: str, at_xy: Tuple[float,float]) -> Dict:
    other = 'a' if team=='b' else 'b'
    match.scoreboard[team] = match.scoreboard.get(team, 0) + 3
    return {"type":"post_score","next_restart_to": other}
