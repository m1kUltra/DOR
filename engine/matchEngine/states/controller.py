# states/controller.py
STATUS_TO_STATE = {
    "restart.kick_off:waiting": ("restart", {"kind": "kick_off", "phase": "waiting"}),
    "restart.kick_off:in_flight": ("restart", {"kind": "kick_off", "phase": "in_flight"}),

    "open_play:in_hand": ("open_play", {"mode": "in_hand"}),
    "open_play:in_flight": ("open_play", {"mode": "kick_return"}),
    "open_play:loose": ("open_play", {"mode": "loose"}),

    "setpiece:scrum:forming": ("scrum", {"phase": "forming"}),
    "setpiece:scrum:active": ("scrum", {"phase": "active"}),
    "setpiece:lineout:forming": ("lineout", {"phase": "forming"}),
    "setpiece:lineout:active": ("lineout", {"phase": "active"}),
    "setpiece:lineout:in_flight": ("lineout", {"phase": "throw"}),

    "contact:tackle:active": ("tackle", {}),
    "contact:ruck:forming": ("ruck", {"phase": "forming"}),
    "contact:ruck:active": ("ruck", {"phase": "active"}),

    "dead:touch": ("restart", {"kind": "lineout", "phase": "award"}),
    "dead:in_goal": ("restart", {"kind": "goal_line_dropout", "phase": "award"}),

    "score:try_awarded": ("restart", {"kind": "post_score", "phase": "waiting"}),
}

def route(match) -> bool:
    s = match.ball.status
    tup = STATUS_TO_STATE.get(s)
    if not tup: 
        return False
    state_name, kwargs = tup
    current_name = getattr(match.current_state, "name", None)
    if current_name == state_name:
        # allow subphase updates inside the same state
        if hasattr(match.current_state, "apply_subphase"):
            match.current_state.apply_subphase(**kwargs)
        return False

    # swap state instance
    if state_name == "open_play":
        from .open_play import OpenPlayState as S
    elif state_name == "restart":
        from .restart import RestartState as S
    elif state_name == "scrum":
        from .scrum import ScrumState as S
    elif state_name == "lineout":
        from .lineout import LineoutState as S
    elif state_name == "ruck":
        from .ruck import RuckState as S
    elif state_name == "tackle":
        from .tackle import TackleState as S
    else:
        return False

    match.current_state = S(**kwargs)
    return True
