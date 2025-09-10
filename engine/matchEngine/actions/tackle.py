
+7
-0

# matchEngine/actions/tackle_action.py
from typing import Optional, Tuple

from set_pieces.tackle import resolve_tackle

XYZ = Tuple[float, float, float]


def do_action(match, tackler_id: str, subtype: Optional[str], location: XYZ, target: XYZ) -> bool:
    """
    Start a tackle:
      - set tackler.state_flags['tackling'] = True
      - set carrier.state_flags['being_tackled'] = True
      - ball.status -> 'in_a_tackle' (carrier keeps hold)
    """
    ball = match.ball
    carrier_id = getattr(ball, "holder", None)
    if not carrier_id:
        return False

    tackler = match.get_player_by_code(tackler_id)
    carrier = match.get_player_by_code(carrier_id)
    if not tackler or not carrier:
        return False

    # ensure flags exist
    if "tackling" not in tackler.state_flags:
        tackler.state_flags["tackling"] = False
    if "being_tackled" not in carrier.state_flags:
        carrier.state_flags["being_tackled"] = False

    tackler.state_flags["tackling"] = True
    carrier.state_flags["being_tackled"] = True

    # signal to FSM
    ball.set_action("in_a_tackle")

    # Immediately resolve tackle outcome
    resolve_tackle(match, tackler, carrier)

    # do NOT release the ball; carrier retains possession during tackle start
    return True