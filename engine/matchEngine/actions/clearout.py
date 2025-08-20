# actions/clearout.py
from typing import Optional, Tuple
XYZ = Tuple[float, float, float]
def do_action(match, player_id: str, subtype: Optional[str], location: XYZ, target: XYZ) -> bool:
    p = match.get_player_by_code(player_id)
    if not p: return False
    # mark a flag if you like (useful for UI or later formulas)
    p.state_flags["in_ruck"] = True
    # no ball mutations; ruck resolution is in states/ruck.py
    return True
