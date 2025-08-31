
# engine/matchEngine/utils/player/dh_assign.py
from typing import Optional, Tuple

def _d2(a: Tuple[float,float], b: Tuple[float,float]) -> float:
    dx, dy = a[0]-b[0], a[1]-b[1]
    return dx*dx + dy*dy

def assign_dh_for_over(match, atk: str, base_xy: Tuple[float,float]) -> Optional[str]:
    """
    If rn=9 of team in possession is on feet and NOT in ruck ⇒ DH = 9.
    Else pick nearest on-feet same-side player and assign them.
    Called in ruck.over.
    """
    bx, by = base_xy

    # clear any old DH flags
    for p in match.players:
        if p.state_flags.get("dummy_half"):
            p.state_flags["dummy_half"] = False

    # prefer 9 if available, on feet, not in ruck
    nine = next((p for p in match.players if p.team_code == atk and p.rn == 9), None)
    if nine and not nine.state_flags.get("in_ruck", False) and not nine.state_flags.get("off_feet", False):
        nine.state_flags["dummy_half"] = True
        return f"{nine.sn}{nine.team_code}"

    # else nearest same-side, on feet, not in ruck
    cand = [
        p for p in match.players
        if p.team_code == atk
        and not p.state_flags.get("in_ruck", False)
        and not p.state_flags.get("off_feet", False)
    ]
    if not cand:
        return None
    cand.sort(key=lambda p: _d2((p.location[0], p.location[1]), (bx, by)))
    cand[0].state_flags["dummy_half"] = True
    return f"{cand[0].sn}{cand[0].team_code}"
