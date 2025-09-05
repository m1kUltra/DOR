# engine/matchEngine/choice/scrum/out.py
from typing import List, Optional, Tuple
from .common import DoCall, team_possession, other

def _pid_by_jersey(match, team_code: str, jersey: int) -> Optional[str]:
    for p in match.players:
        if p.team_code == team_code and getattr(p, "jersey", 0) == jersey:
            return getattr(p, "pid", None) or getattr(p, "id", None)
    return None

def _player_loc(match, pid: str) -> Tuple[float,float,float]:
    for p in match.players:
        if getattr(p, "pid", None) == pid or getattr(p, "id", None) == pid:
            return p.location
    return (0.0,0.0,0.0)

def plan(match, state_tuple) -> List[DoCall]:
    """
    OUT:
    - If penalty was set, do nothing here (ref layer should whistle).
    - Otherwise, SH passes or 8 picks (choose simply by tactic hint).
    - Transfer ball.holder and set your open-play action.
    """
    calls: List[DoCall] = []
    atk = team_possession(match)

    if getattr(match, "_scrum_outcome", None) in ("pen_feed", "pen_def"):
        # Leave to referee system
        return calls

    tactic = getattr(match, "scrum_tactic_out", "pass")  # "pass" or "pick8"
    pid9 = _pid_by_jersey(match, atk, 9)
    pid8 = _pid_by_jersey(match, atk, 8)

    if tactic == "pick8" and pid8:
        # 8 picks and goes
        calls.append((pid8, ("pickup", None), _player_loc(match, pid8), (0.0,0.0,0.0)))
        match.ball.holder = pid8
        match.ball.location = _player_loc(match, pid8)
        match.ball.set_action("open_play")
    elif pid9:
        # 9 passes out (to 10 by default)
        pid10 = _pid_by_jersey(match, atk, 10)
        tgt_loc = _player_loc(match, pid10) if pid10 else (0.0,0.0,0.0)
        calls.append((pid9, ("pass", pid10), _player_loc(match, pid9), tgt_loc))
        match.ball.holder = pid10 or pid9
        match.ball.location = tgt_loc if pid10 else _player_loc(match, pid9)
        match.ball.set_action("open_play")

    return calls
