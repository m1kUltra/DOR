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
from shapes.scrum.scrum import generate_scrum_shape
from shapes.scrum.default import generate_phase_play_shape

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
def handle_start(match, state_tuple) -> None:
    """
    Initialize a scrum:
      - Clear ball holder and set to ground at its current x,y
      - Move both packs, 9s, and backs into correct formation
      - Transition ball to 'scrum_crouch'
    """
    pending = getattr(match, "pending_scrum", {}) or {}
    atk = pending.get("put_in") or _other(_team_possession(match))
    set_possession(match, atk)
    match.pending_scrum = {}
    sh = f"9{atk}"
    bx, by, _ = _xyz(getattr(match.ball, "location", None))

    attack_team = match.team_a if atk == "a" else match.team_b
    defend_team = match.team_b if atk == "a" else match.team_a
    attack_dir = float(attack_team.tactics.get("attack_dir", 1.0))

   # backline_style = match.tactics.get("backline_style", "default")
    phase_shape = generate_phase_play_shape("default", attack_dir)
    layout = generate_scrum_shape(attack_dir=attack_dir, backline_positions=phase_shape)

    def _apply(team, sub_layout):
        for rn, (lx, ly) in sub_layout.items():
            try:
                jersey = int(rn)
            except (TypeError, ValueError):
                continue
            p = team.get_player_by_rn(jersey)
            if not p:
                continue
            wx = bx + lx
            wy = by + ly
            p.update_location(match.pitch.clamp_position((wx, wy, 0.0)))

    
    _apply(attack_team, layout['team_a'])
    _apply(defend_team, layout['team_b'])
    match.ball.holder = sh
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

    atk = _team_possession(match)                  # 'a' or 'b'
    sh_code = f"9{atk}"                            # scrum‑half code
    hk_code = f"2{atk}"                            # hooker code

    sh = match.get_player_by_code(sh_code)
    hk = match.get_player_by_code(hk_code)
    if sh and hk:
        do_action(
            match,
            sh_code,                               # passer is the scrum‑half
            ("feed", None),                       # use feed action
            sh.location,                          # current ball location
            hk.location                           # hooker’s position
        )

    # Optionally transition to FEED when stability threshold achieved
    # if _is_stable_enough(match): match.ball.set_action("scrum_feed_ready")

def handle_feed(match, state_tuple) -> None:
    """
    Feed: scrum-half puts the ball into the tunnel; set ball path & slight bias.
    """
    atk = _team_possession(match)                  # 'a' or 'b'
    n8_code = f"8{atk}"                            # scrum‑half code
    hk_code = f"2{atk}"                            # hooker code

    n8 = match.get_player_by_code(n8_code)
    hk = match.get_player_by_code(hk_code)
    if n8 and hk:
        do_action(
            match,
            hk_code,                               # passer is the scrum‑half
            ("hook", None),                       # use feed action
            hk.location,                          # current ball location
            n8.location                           # hooker’s position
        )
    

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

# ---- tiny local helpers to avoid undefined names ----
def _dist2(a_xy, b_xy) -> float:
    ax, ay = a_xy
    bx, by = b_xy
    dx = ax - bx
    dy = ay - by
    return dx*dx + dy*dy

def _wait_limit_ticks(match) -> int:
    """
    Soft cap on how long we wait in STABLE for the 9 to get set.
    Reads optional config: match.config.scrum_wait_limit; default 12 ticks.
    """
    cfg = getattr(match, "config", None)
    return int(getattr(cfg, "scrum_wait_limit", 12))

# -------------------------
# Stable: ball controllable at 8's feet
# -------------------------
# ---- mirror ruck/over constants + helpers ----
from typing import List, Tuple, Optional
from utils.positioning.mental.phase import phase_attack_targets, phase_defence_targets

READY_DIST = 5.0
READY_D2   = READY_DIST * READY_DIST

def _d2(a,b):
    dx,dy = a[0]-b[0], a[1]-b[1]
    return dx*dx + dy*dy



def _team_ready(match, atk: str, base_xy, dh_id: Optional[str]) -> bool:
    bx, by = base_xy
    targets = phase_attack_targets(match, atk, (bx, by))
    ready = 0
    total = 0
    for p in match.players:
        if p.team_code != atk:
            continue
        if p.state_flags.get("in_ruck", False):
            continue
        pid = f"{p.sn}{p.team_code}"
        if dh_id and pid == dh_id:
            continue
        tgt = targets.get(p)
        if not tgt:
            continue
        total += 1
        if _d2((p.location[0],p.location[1]), (tgt[0],tgt[1])) <= READY_D2:
            ready += 1
    # 10/15 in place (or 2/3 of available non-ruck, non-DH players)
    return (ready >= 10) or (total and ready / total >= 0.66)

# -------------------------
# Stable: mirror ruck/over "plan" EXACTLY, with DH fixed to jersey 9
# -------------------------
def handle_stable(match, state_tuple) -> None:
    """
    Stable: behave exactly like ruck/over plan():
      - Move non-ruck ATT to phase attack targets (excluding DH)
      - Move DEF to phase defence targets
      - DH (forced to 9) waits until close/ready/timeout, then PICK
      - After PICK, transition to 'scrum.out'
    """
    # Base/ball position
    bx, by, _ = _xyz(getattr(match.ball, "location", None))
    base_xy = (bx, by)

    # Team in possession
    atk = _team_possession(match)
    deff = "b" if atk == "a" else "a"

    # Force DH = jersey 9 of attacking team
    dh_id = f"9{atk}"

    # init wait counter (reuse the same attribute name as ruck/over)
    if not hasattr(match, "_ruck_over_wait"):
        match._ruck_over_wait = 0

    calls: List[DoCall] = []

    # ATT: players not in ruck -> phase shapes (excluding DH)
    atk_targets = phase_attack_targets(match, atk, base_xy)
    for p in match.players:
        if p.team_code != atk:
            continue
        if p.state_flags.get("in_ruck", False):
            continue
        pid = f"{p.sn}{p.team_code}"
        if dh_id and pid == dh_id:
            continue
        tgt = atk_targets.get(p)
        if not tgt:
            continue
        calls.append((pid, ("move", None), _xyz(p.location), tgt))

    # DEF: players not in ruck -> defence shapes
    def_targets = phase_defence_targets(match, deff, base_xy)
    for p in match.players:
        if p.team_code != deff or p.state_flags.get("in_ruck", False):
            continue
        calls.append((f"{p.sn}{p.team_code}", ("move", None), _xyz(p.location), def_targets.get(p, _xyz(p.location))))

    # DH waits until ready or timeout, then PICK
    if dh_id:
        dh = match.get_player_by_code(dh_id)
        if dh:
            px, py, _ = _xyz(dh.location)
            close = _d2((px,py), base_xy) <= (1.5*1.5)
            ready = _team_ready(match, atk, base_xy, dh_id)
            timeout = match._ruck_over_wait >= _wait_limit_ticks(match)

            if not close:
                calls.append((dh_id, ("move", None), (px,py,0.0), match.pitch.clamp_position((bx,by,0.0))))
                match._ruck_over_wait += 1
            else:
                if ready or timeout:
                    calls.append((dh_id, ("picked", None), (px,py,0.0), (bx,by,0.0)))
                    match._ruck_over_wait = 0
                    # As soon as 9 picks, they become holder and we exit scrum
                    match.ball.holder = dh_id
                    match.ball.location = (bx, by, 0.0)
                    # We'll set action to 'scrum.out' after dispatching calls below
                else:
                    # tiny nudge to keep orientation + let others settle
                    calls.append((dh_id, ("move", None), (px,py,0.0), match.pitch.clamp_position((bx+0.001,by+0.001,0.0))))
                    match._ruck_over_wait += 1

    # Dispatch calls now
    for pid, action, loc, target in calls:
        do_action(match, pid, action, loc, target)

    # If DH just picked, transition to out
    # (We check holder to avoid flipping state prematurely)

def handle_out(match, state_tuple) -> None:
    """
    Scrum OUT: 9 has picked but we're protecting the pass from open_play logic.
    Works with choice/scrum/out.plan that mirrors ruck/out (no tactics).
    """
    # Team in possession + DH = jersey 9
    atk = _team_possession(match)
    dh_id = f"9{atk}"
    dh = match.get_player_by_code(dh_id)
    if dh:
        # Mark the active dummy-half for the plan's _current_dh_id()
        dh.state_flags["dummy_half"] = True
        # Ensure holder defaults to 9 while we're in the protected state
        if getattr(match.ball, "holder", None) != dh_id:
            match.ball.holder = dh_id

    # Get planned calls for protected scrum-out phase
    calls = out_plan(match, state_tuple) or []

    # Did a pass leave this tick?
    pass_happened = False
    for pid, action, loc, target in calls:
        if isinstance(action, tuple) and action[0] == "pass":
            # prefer detecting a pass from DH; if DH missing, any pass exits
            if (dh_id and pid == dh_id) or not dh_id:
                pass_happened = True
        do_action(match, pid, action, loc, target)

    # Advance state only once the pass actually goes; otherwise remain protected
    
   
