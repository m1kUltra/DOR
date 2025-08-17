# matchEngine/utils/player/locked_defender.py

from typing import Optional
from states.open_play import OPEN_PLAY_TAGS

def _dist2(a_xy, b_xy) -> float:
    ax, ay = a_xy[0], a_xy[1]
    bx, by = b_xy[0], b_xy[1]
    dx, dy = ax - bx, ay - by
    return dx*dx + dy*dy

def _set_flag_all(match, flag: str, value: bool) -> None:
    for p in match.players:
        p.state_flags[flag] = value

def update(match, state_tag: Optional[str]) -> Optional[str]:
    """
    During open play, tag the nearest opposing player to the holder as 'locked_defender'.
    Clears the flag elsewhere.

    Returns the player_id (e.g., '7b') of the locked defender, or None.
    """
    # ensure the flag exists on all players
    for p in match.players:
        if "locked_defender" not in p.state_flags:
            p.state_flags["locked_defender"] = False

    # only active in open play
    if not (isinstance(state_tag, str) and state_tag in OPEN_PLAY_TAGS):
        _set_flag_all(match, "locked_defender", False)
        return None

    holder_id = getattr(match.ball, "holder", None)
    if not holder_id:
        _set_flag_all(match, "locked_defender", False)
        return None

    holder = match.get_player_by_code(holder_id)
    if holder is None:
        _set_flag_all(match, "locked_defender", False)
        return None

    holder_xy = (holder.location[0], holder.location[1])
    opp_code = "b" if holder.team_code == "a" else "a"

    # find nearest opponent
    nearest = None
    best_d2 = float("inf")
    for p in match.players:
        if p.team_code != opp_code:
            continue
        d2 = _dist2(holder_xy, (p.location[0], p.location[1]))
        if d2 < best_d2:
            best_d2 = d2
            nearest = p

    # clear all, then set the one
    _set_flag_all(match, "locked_defender", False)

    if nearest is None:
        return None

    nearest.state_flags["locked_defender"] = True
    return f"{nearest.sn}{nearest.team_code}"
