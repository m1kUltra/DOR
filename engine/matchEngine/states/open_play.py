# states/open_play.py

# flat string constants for open-play substates
LAUNCH_PLAY = "open_play.launch_play"
PHASE_PLAY  = "open_play.phase_play"
KICK_RETURN = "open_play.kick_return"
TURNOVER    = "open_play.turnover"
LINE_BREAK  = "open_play.line_break"
SCRAMBLE    = "open_play.scramble"
KICK_CHASE  = "open_play.kick_chase"
TACKLE      = "open_play.tackle"
JOUE        = "open_play.joue"

OPEN_PLAY_TAGS = {
    LAUNCH_PLAY, PHASE_PLAY, KICK_RETURN, TURNOVER, LINE_BREAK,
    SCRAMBLE, KICK_CHASE, TACKLE, JOUE,
}

from typing import Any, Tuple, Optional
import event


# --- tunables (fast to tweak) ---
PASS_ERROR_Z   = 0.0     # if pass hits ground at/below this height
READY_LINE_N   = 11      # line-break threshold: defenders behind holder >= this many
STATIC_LOOSE_D2 = 0.09   # ~0.3m^2 → “ball is basically idle on ground”
TURNOVER_GRACE_TICKS = 6 # frames to ignore “possession flip” right after ruck/out
LINEBREAK_BUFFER_X = 0.7 # allow small tolerance on X when counting “behind”

def _xyz(v, default=(0.0,0.0,0.0)):
    if isinstance(v, (list, tuple)):
        if len(v) >= 3: return (float(v[0]), float(v[1]), float(v[2]))
        if len(v) == 2: return (float(v[0]), float(v[1]), 0.0)
    return default

def _z(loc) -> float:
    return float(loc[2]) if isinstance(loc,(list,tuple)) and len(loc)>=3 else 0.0

def _d2(a, b) -> float:
    dx, dy = a[0]-b[0], a[1]-b[1]
    return dx*dx + dy*dy

def _attack_dir_of_holder(match, holder_id: Optional[str]) -> float:
    if not holder_id: return +1.0
    team = match.team_a if holder_id.endswith("a") else match.team_b
    return float((team.tactics or {}).get("attack_dir", +1.0))

def _count_defenders_behind_holder(match, holder_id: str) -> int:
    holder = match.get_player_by_code(holder_id)
    if not holder: return 0
    hx, hy, _ = holder.location
    dirn = _attack_dir_of_holder(match, holder_id)
    # “behind” means toward ball carrier’s own tryline (opposite attack dir)
    def is_behind(px):
        if dirn > 0:  # attacking +x → behind == px <= hx + buffer
            return px <= (hx + LINEBREAK_BUFFER_X)
        else:         # attacking -x → behind == px >= hx - buffer
            return px >= (hx - LINEBREAK_BUFFER_X)
    cnt = 0
    for p in match.players:
        if p.team_code == holder.team_code: continue
        if is_behind(p.location[0]):
            cnt += 1
    return cnt

def _possession_code_from_holder(holder_id: Optional[str]) -> Optional[str]:
    if not holder_id or not isinstance(holder_id, str) or len(holder_id) < 1:
        return None
    return holder_id[-1]  # 'a' or 'b'

def _recently_left_ruck(match) -> bool:
    # optional soft guard: during transition frames after ruck.out, ignore turnover heuristics
    return getattr(match, "_frames_since_ruck", 0) < TURNOVER_GRACE_TICKS

def maybe_handle(match, tag, loc, ctx) -> bool:
    b = match.ball
    last = getattr(b, "last_status", {}) or {}
    curr = getattr(b, "status", {}) or {}

    # A) pass hits ground
    if getattr(b, "holder", None) is None:
        if last.get("action") == "passed" and curr.get("action") != "pass_error":
            if _z(getattr(b, "location", loc)) <= PASS_ERROR_Z:
                print(loc)
                b.set_action("pass_error")
                return True
    if curr.get("action") in ("tackle_broken", "passive_tackle"):
        for p in match.players:
            p.state_flags["being_tackled"] = False
            p.state_flags["tackling"] = False
        return False
    # B1) line break → set action on the ball
    hid = getattr(b, "holder", None)
    if isinstance(hid, str) and len(hid) >= 2:
        if _count_defenders_behind_holder(match, hid) >= READY_LINE_N:
            b.set_action("line_break")
            return True

    # B2) turnover → set action on the ball
    prev_holder = (last or {}).get("holder")
    curr_holder = (curr or {}).get("holder") or getattr(b, "holder", None)
    prev_side = _possession_code_from_holder(prev_holder)
    curr_side = _possession_code_from_holder(curr_holder)

    if curr_holder and prev_side and curr_side and (prev_side != curr_side) and not _recently_left_ruck(match):
        b.set_action("turnover")
        return True
    
       # B3) idle loose ball on ground → scramble
    if isinstance(tag, str) and tag.startswith("open_play"):
        if getattr(b, "holder", None) is None and last.get("action") != "kicked":
            if _z(getattr(b, "location", loc)) == 0.0 and curr.get("action") != "dropped":
                b.set_action("dropped")
                return True

    # C) grace counter
    match._frames_since_ruck = getattr(match, "_frames_since_ruck", 0) + 1
    return False

    