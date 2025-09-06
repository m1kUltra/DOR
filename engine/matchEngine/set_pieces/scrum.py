# engine/matchEngine/set_pieces/scrum.py
from typing import List, Tuple, Optional
from actions.action_controller import do_action
from team.team_controller import set_possession
# Planners (mirror ruck structure)
from choice.scrum.crouch import plan as crouch_plan
from choice.scrum.bind import plan as bind_plan
from choice.scrum.set import plan as set_plan
from choice.scrum.feed import plan as feed_plan
from choice.scrum.drive import plan as drive_plan
from choice.scrum.stable import plan as stable_plan
from choice.scrum.out import plan as out_plan
from choice.scrum.start import plan as start_plan

# (Optional) if you want a "start" entry even though states maps START->crouch
# from choice.scrum.start import plan as start_plan

DoCall = Tuple[
    str,                                  # pid
    Tuple[str, Optional[str]],            # (action, maybe_param)
    Tuple[float, float, float],           # location (x,y,z)
    Tuple[float, float, float],           # target (x,y,z) or (0,0,0)
]

def _xyz(p) -> Tuple[float, float, float]:
    return tuple(p) if isinstance(p, (list, tuple)) and len(p) == 3 else (0.0, 0.0, 0.0)

def _team_possession(match) -> str:
    """
    Return 'a' or 'b' for the team with the scrum put-in.
    Falls back to ball.holder suffix or 'a' if unknown.
    """
    if getattr(match, "possession", None) in ("a", "b"):
        return match.possession
    hid = getattr(match.ball, "holder", None)
    code = hid[-1] if isinstance(hid, str) and hid else "a"
    match.possession = code
    set_possession(match, code)
    return code

def _other(code: str) -> str:
    return "b" if code == "a" else "a"

def _set_ball_for_scrum(match) -> None:
    """
    Normalize ball state for scrum phases: no holder, ball on ground at tunnel entry.
    """
    bx, by, _ = _xyz(getattr(match.ball, "location", None))
    
    match.ball.location = (bx, by, 0.0)
    

def _tunnel_point(match) -> Tuple[float, float, float]:
    """
    Compute/return the tunnel (feed) location.
    TODO: Replace with your scrum pack midpoint/tunnel calc.
    """
    # crude default: use current ball (x,y), z=0
    bx, by, _ = _xyz(getattr(match.ball, "location", None))
    return (bx, by, 0.0)


# -------------------------
# Handlers (invoked by states/scrum.maybe_handle)
# -------------------------
from choice.scrum.common import pid_by_jersey
def handle_start(match, state_tuple) -> None:
    """
    Initialize a scrum:
      - Clear ball holder and set to ground at its current x,y
      - Move both packs, 9s, and backs into correct formation
      - Transition ball to 'scrum_crouch'
    """
    atk = _team_possession(match)
    sh_pid = pid_by_jersey(match, atk, 9)

    bx, by, _ = _xyz(getattr(match.ball, "location", None))
    
    match.ball.location = (bx, by, 0.0)
    

    calls = start_plan(match, state_tuple) or []
    for pid, action, loc, target in calls:
        do_action(match, pid, action, loc, target)

    if sh_pid:
        sh = match.get_player_by_code(sh_pid)
        if sh and getattr(sh, "location", None):
            match.ball.holder = sh_pid
            match.ball.location = getattr(sh, "location")

    calls = start_plan(match, state_tuple) or []
    for pid, action, loc, target in calls:
        do_action(match, pid, action, loc, target)
    match.ball.set_action("scrum.crouch")
    set_possession(match, atk)
def handle_crouch(match, state_tuple) -> None:
    """
    Enter crouch: align front rows, set initial posture/spacing and camera/audio cues.
    """
    _set_ball_for_scrum(match)
    calls = crouch_plan(match, state_tuple) or []
    for pid, action, loc, target in calls:
        do_action(match, pid, action, loc, target)
    match.ball.set_action("scrum.bind")
def handle_bind(match, state_tuple) -> None:
    """
    Bind: props bind, check legal binds, stability, angle.
    Potential early resets if angles/height are illegal.
    """
    calls = bind_plan(match, state_tuple) or []
    for pid, action, loc, target in calls:
        do_action(match, pid, action, loc, target)
        match.ball.set_action("scrum.set")

    # Optional: simple illegal bind/reset gate (placeholder)
    # if _illegal_bind_detected(match): match.ball.set_action("scrum_reset")

def handle_set(match, state_tuple) -> None:
    """
    Set: packs engage to a stable, safe position before the feed.
    """
    calls = set_plan(match, state_tuple) or []
    for pid, action, loc, target in calls:
        do_action(match, pid, action, loc, target)
    match.ball.set_action("scrum.feed")
    # Optionally transition to FEED when stability threshold achieved
    # if _is_stable_enough(match): match.ball.set_action("scrum_feed_ready")

def handle_feed(match, state_tuple) -> None:
    """
    Feed: scrum-half puts the ball into the tunnel; set ball path & slight bias.
    """
    # Ensure ball is at tunnel entry
    match.ball.holder = None
    #have the rn.2 be able to hook the ball without holiding it, can move the ball without holding if within 1m of them 
    match.ball.location = _tunnel_point(match)
    

    calls = feed_plan(match, state_tuple) or []
    for pid, action, loc, target in calls:
        do_action(match, pid, action, loc, target)
    match.ball.set_action("scrum.drive") #TODO pop this

def handle_drive(match, state_tuple) -> None:
    """
    Drive: teams push; move ball through feet; possible wheel/collapse/penalty.
    """
    calls = drive_plan(match, state_tuple) or []
    for pid, action, loc, target in calls:
        do_action(match, pid, action, loc, target)
    match.ball.set_action("scrum.stable")
"""
    # Very simple pack dominance effect on ball drift (placeholder)
    bx, by, bz = _xyz(getattr(match.ball, "location", None))
    bal = _pack_balance_metric(match)
    # Move slightly toward attacking 8's feet on positive balance
    drift = 0.1 if bal > 0 else -0.1 if bal < 0 else 0.0
    match.ball.location = (bx + drift, by, max(0.0, bz))
    """

    # Optionally promote to STABLE when near back-row feet
    # if _ball_at_back_row(match): match.ball.set_action("scrum_stable")

def handle_stable(match, state_tuple) -> None:
    """
    Stable: ball is controllable at 8's feet; choose pick, 8-9, or penalty advantage.
    """
    calls = stable_plan(match, state_tuple) or []
    for pid, action, loc, target in calls:
        do_action(match, pid, action, loc, target)
        match.ball.set_action("scrum.out")

    # NOTE: stable_plan should decide when to call pickup/pass via actions
    # Optionally, timeout -> force 'use it' -> out
    # if _use_it_timer_expired(match): match.ball.set_action("scrum_out")

def handle_out(match, state_tuple) -> None:
    """
    Out: ball leaves scrum (pick/pass). Hand off to phase play or set move.
    """
    calls = out_plan(match, state_tuple) or []
    for pid, action, loc, target in calls:
        do_action(match, pid, action, loc, target)

    # Responsibility of out_plan: set next possession, e.g.:
    #   - set match.ball.holder = "<player_id>"
    #   - set match.ball.location = player's loc
    #   - set match.ball.set_action("open_play") or similar
