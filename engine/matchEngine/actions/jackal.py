# actions/jackal.py
from typing import Optional, Tuple
XYZ = Tuple[float, float, float]
def do_action(match, player_id: str, subtype: Optional[str], location: XYZ, target: XYZ) -> bool:
    p = match.get_player_by_code(player_id)
    if not p: return False
    
    return True
