# engine/matchEngine/set_pieces/ruck.py
from typing import List, Tuple, Optional
from actions.action_controller import do_action
from choice.ruck.start import plan as start_plan
from choice.ruck.forming import plan as forming_plan
from choice.ruck.over import plan as over_plan
from choice.ruck.out import plan as out_plan

DoCall = Tuple[str, Tuple[str, Optional[str]], Tuple[float,float,float], Tuple[float,float,float]]

def _xyz(p):
    return tuple(p) if isinstance(p, (list,tuple)) else (0.0,0.0,0.0)

def _team_possession(match) -> str:
    if getattr(match, "possession", None) in ("a","b"):
        return match.possession
    hid = getattr(match.ball, "holder", None)
    code = hid[-1] if isinstance(hid, str) and hid else "a"
    match.possession = code
    return code

def _other(code: str) -> str: return "b" if code == "a" else "a"

def handle_start(match, state_tuple) -> None:
    #TODO implment check over_line 
    """
    if over. own tryline implment goaline restart
    else its a try (call check_scoring)
    """
    bx, by, _ = _xyz(getattr(match.ball, "location", None))
    _team_possession(match)
    match.ball.holder   = None
    match.ball.location = (bx, by, 0.0)
    match.ball.set_action("ruck_forming")

     # initialise ruck state tracking
    match.ruck_state = {"time": 0.0, "won": False, "defender_engaged": False}

    calls = start_plan(match, state_tuple) or []
    for pid, action, loc, target in calls:
        do_action(match, pid, action, loc, target)

def handle_forming(match, state_tuple) -> None:
    bx, by, _ = _xyz(getattr(match.ball, "location", None))
    atk = _team_possession(match)
    deff = _other(atk)

    # ensure ruck state exists and advance timer
    rs = getattr(match, "ruck_state", None)
    if not rs:
        rs = {"time": 0.0, "won": False, "defender_engaged": False}
        match.ruck_state = rs
    rs["time"] += 1

    calls = forming_plan(match, state_tuple) or []
    for pid, action, loc, target in calls:
        do_action(match, pid, action, loc, target)

    # track defender engagement
    if not rs["defender_engaged"]:
        rs["defender_engaged"] = any(
            p.state_flags.get("in_ruck") and p.team_code == deff
            for p in match.players
        )

    # early ruck win check before defenders arrive
    if not rs["won"] and not rs["defender_engaged"]:
        attackers = [p for p in match.players if p.team_code == atk and p.state_flags.get("in_ruck")]
        if attackers:
            p = attackers[0]
            rucking = p.norm_attributes.get("rucking", 0.0)
            aggression = p.norm_attributes.get("aggression", 0.0)
            weight = getattr(p, "weight", 0.0) or 0.0
            t = rs["time"] if rs["time"] else 1e-6
            shut_down = (rucking * aggression * (weight / 150.0)) / t
            if shut_down > 1.0:
                rs["won"] = True
                for pl in match.players:
                    pl.state_flags["jackal"] = False
                    pl.state_flags["in_ruck"] = False
                match.ball.holder = None
                match.ball.location = (bx, by, 0.0)
                match.ball.set_action("ruck_over")
                return


     # contested resolution or timeout once defenders engage
    if not rs["won"]:
        threshold = 30
        resolved = rs["time"] >= threshold
        if not resolved:
            atk_score = sum(
                p.norm_attributes.get("rucking", 0.0)
                for p in match.players
                if p.team_code == atk and p.state_flags.get("in_ruck")
            )
            def_score = sum(
                p.norm_attributes.get("rucking", 0.0)
                for p in match.players
                if p.team_code == deff and p.state_flags.get("in_ruck")
            )
            resolved = atk_score != def_score
        if resolved:
            rs["won"] = True
            for pl in match.players:
                pl.state_flags["jackal"] = False
                pl.state_flags["in_ruck"] = False
            match.ball.holder = None
            match.ball.location = (bx, by, 0.0)
            match.ball.set_action("ruck_over")
            return

def handle_over(match, state_tuple) -> None:
    calls = over_plan(match, state_tuple) or []
    for pid, action, loc, target in calls:
        do_action(match, pid, action, loc, target)
    # NOTE: over_plan will issue ("picked", None) when ready/timeout

def handle_out(match, state_tuple) -> None:
    calls = out_plan(match, state_tuple) or []
    for pid, action, loc, target in calls:
        do_action(match, pid, action, loc, target)
    # NOTE: out_plan will "pass" when ready/timeout
