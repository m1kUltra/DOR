# states/offside.py
from typing import Tuple, Optional, Any
import event

# --------- tiny helpers (no Match/Player edits required) ---------
def _all_players(match):
    return getattr(match, "players", [])

def _teams(match):
    return (getattr(match, "team_a", None), getattr(match, "team_b", None))

def _team_of(match, p):
    # map by team_code
    return match.team_a if getattr(p, "team_code", None) == "a" else match.team_b

def _other_team(match, team):
    ta, tb = _teams(match)
    return tb if team is ta else ta

def _code(p):
    return f"{p.sn}{p.team_code}"
# -----------------------------------------------------------------

# Tunables
TEN_METRES = 10.0
INTERFERENCE_RADIUS = 3.0
LINEOUT_GAP = 10.0
SCRUM_5M = 5.0

def update_flags(match, tag: str, loc: Tuple[float, float, float], ctx: Optional[Any]) -> None:
    """Set per-player offside flags based on the current phase/state tag."""
    phase = tag.split(".")[0] if isinstance(tag, str) and "." in tag else (tag or "open_play")

    if phase in ("ruck", "maul"):
        _offside_breakdown(match)
    elif phase == "scrum":
        _offside_scrum(match, loc)
    elif phase in ("restart", "lineout"):
        _offside_lineout(match, loc)
    else:
        _offside_open_play(match)

    # universal puts-onside (mostly open play)
    _apply_open_play_puts_onside(match)

def maybe_infringement(match, tag, loc, ctx) -> None:
    """If an offside player materially interferes, raise an event."""
    ball_pos = getattr(match.ball, "location", loc)
    holder = getattr(match.ball, "holder", None)
    aerial = holder is None and getattr(match.ball, "in_air", False)

    for p in _all_players(match):
        if not p.flags.get("offside", False):
            continue
        if _is_retreating(match, p):
            continue

        # close to ball/receiver
        if _dist2(p.location, ball_pos) <= INTERFERENCE_RADIUS ** 2:
            event.set_event(("penalty.offside", ball_pos, _code(p)))
            return

        # 10m protection for aerial ball
        if aerial and _dist2(p.location, ball_pos) <= (TEN_METRES ** 2):
            event.set_event(("penalty.offside_10m", ball_pos, _code(p)))
            return

# ---------- Phase implementations ----------

def _offside_breakdown(match):
    """Ruck/Maul: offside line is hindmost bound player for each team."""
    left_team, right_team = _teams(match)
    ruckers = _participants_in_contact(match)

    if not ruckers or not left_team or not right_team:
        _offside_open_play(match)
        return

    l_dir = left_team.attack_sign
    r_dir = right_team.attack_sign

    l_bound = [p for p in ruckers if _team_of(match, p) is left_team]
    r_bound = [p for p in ruckers if _team_of(match, p) is right_team]

    if not l_bound or not r_bound:
        _offside_open_play(match)
        return

    l_line_x = min(p.location[0] for p in l_bound) if l_dir > 0 else max(p.location[0] for p in l_bound)
    r_line_x = max(p.location[0] for p in r_bound) if r_dir > 0 else min(p.location[0] for p in r_bound)

    for p in _all_players(match):
        team = _team_of(match, p)
        if team is left_team:
            p.flags["offside"] = _is_past_line(p.location[0], l_line_x, l_dir, buffer=0.5)
        else:
            p.flags["offside"] = _is_past_line(p.location[0], r_line_x, r_dir, buffer=0.5)

def _offside_scrum(match, mark):
    """Scrum: ±5m behind hindmost foot (use mark.x)."""
    mx = float(mark[0])
    for p in _all_players(match):
        dirn = _team_of(match, p).attack_sign
        p.flags["offside"] = _is_past_line(p.location[0], mx, dirn, buffer=SCRUM_5M)

def _offside_lineout(match, mark):
    """Lineout: everyone not in the lineout 10m back from line-of-touch (mark.x)."""
    mx = float(mark[0])
    for p in _all_players(match):
        if p.flags.get("in_lineout", False):
            p.flags["offside"] = False
        else:
            dirn = _team_of(match, p).attack_sign
            p.flags["offside"] = _is_past_line(p.location[0], mx, dirn, buffer=LINEOUT_GAP)

def _offside_open_play(match):
    """Open play: only enforce kick offside (teammates ahead of kicker)."""
    ball = match.ball
    last = getattr(ball, "last_status", {}) or {}
    curr = getattr(ball, "status", {}) or {}

    last_action = last.get("action")
    curr_action = curr.get("action")
    # your kick action sets "kicked" in actions/kick.py; include both spellings
    kicked = (last_action in ("kick", "kicked")) or (curr_action in ("kick", "kicked"))

    last_holder = last.get("holder")
    if not kicked or not last_holder:
        for p in _all_players(match):
            p.flags["offside"] = False
        return

    kicker = match.get_player_by_code(last_holder)
    team = _team_of(match, kicker)
    kicker_x = kicker.location[0]
    dirn = team.attack_sign

    # kicking team: ahead of kicker => offside
    for p in team.squad:
        p.flags["offside"] = _ahead_of(p.location[0], kicker_x, dirn)

    # opponents never offside by this law
    other = _other_team(match, team)
    for p in other.squad:
        p.flags["offside"] = False

def _apply_open_play_puts_onside(match):
    """Put offside teammates onside via movement, opponent touch, or retreat."""
    ball = match.ball
    last = getattr(ball, "last_status", {}) or {}
    last_holder = last.get("holder")
    if not last_holder:
        return

    kicker = match.get_player_by_code(last_holder)
    team = _team_of(match, kicker)
    dirn = team.attack_sign

    # A) any onside teammate moves ahead of them
    onside_teammates = [p for p in team.squad if not p.flags.get("offside", False)]
    if onside_teammates:
        lead_x = max(p.location[0] for p in onside_teammates) if dirn > 0 else min(p.location[0] for p in onside_teammates)
        for p in team.squad:
            if p.flags.get("offside", False) and _behind_or_equal(p.location[0], lead_x, dirn):
                p.flags["offside"] = False

    # B) opponent touch → everyone onside
    if last.get("touched_by_opposition", False) or getattr(ball, "touched_by_opposition", False):
        for p in team.squad:
            p.flags["offside"] = False
        # optional: clear transient if you set it elsewhere
        # ball.touched_by_opposition = False

    # C) retreat behind kicker line
    kicker_x = kicker.location[0]
    for p in team.squad:
        if p.flags.get("offside", False) and _behind_or_equal(p.location[0], kicker_x, dirn):
            p.flags["offside"] = False

# ---------- helpers ----------

def _participants_in_contact(match):
    get = getattr(match, "get_current_contact_players", None)
    return get() if get else []

def _is_retreating(match, p) -> bool:
    vx = getattr(p, "velocity", (0.0, 0.0, 0.0))[0]
    return (vx * _team_of(match, p).attack_sign) < -0.5  # negative along attack axis

def _is_past_line(px: float, line_x: float, dirn: int, buffer: float = 0.0) -> bool:
    """Beyond the offside line toward opponent tryline (with buffer)."""
    if dirn > 0:
        return px > (line_x + buffer)
    else:
        return px < (line_x - buffer)

def _ahead_of(px: float, ref_x: float, dirn: int) -> bool:
    return px > ref_x if dirn > 0 else px < ref_x

def _behind_or_equal(px: float, ref_x: float, dirn: int) -> bool:
    return px <= ref_x if dirn > 0 else px >= ref_x

def _dist2(a, b) -> float:
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    return dx * dx + dy * dy
