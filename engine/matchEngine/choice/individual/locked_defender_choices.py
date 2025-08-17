# matchEngine/choice_controller.py
from typing import Tuple, Optional

# tuples we pass around
XYZ    = Tuple[float, float, float]
Action = Tuple[str, Optional[str]]         # ("pass","flat"), ("kick","bomb"), ("run", None)
DoCall = Tuple[str, Action, XYZ, XYZ]      # (player_id, action, location, target)

# these modules do the real work (kept separate on purpose)
from .roles import resolve_actor            # resolve_actor(match, state_tuple) -> str (player_id like "10a")
from .choices import choose_for_state       # choose_for_state(match, player_id, state_tuple) -> (Action, XYZ)

def choose(match, state_tuple) -> Optional[DoCall]:
    """
    Minimal coordinator:
      - Only handles in-play states (state tag startswith 'in_play').
      - Delegates actor selection to roles.resolve_actor(...)
      - Delegates action/target selection to choices.choose_for_state(...)
      - Returns (player_id, action, location_xyz, target_xyz) for action_controller.do_action(...)
    """
    tag, loc, ctx = state_tuple

    # events are handled by set-piece shells; don't emit a do_action tuple
    if not (isinstance(tag, str) and tag.startswith("in_play")):
        return None

    # 1) who acts?
    player_id = resolve_actor(match, state_tuple)
    if not player_id:
        return None

    # 2) what do they do? (section, subtype) and where? (target xyz)
    action, target = choose_for_state(match, player_id, state_tuple)
    if not action or target is None:
        return None

    # 3) emit the call tuple
    return (player_id, action, _xyz(loc), _xyz(target))


# ---- tiny helper ----
def _xyz(p) -> XYZ:
    if p is None: return (0.0, 0.0, 0.0)
    if isinstance(p, (list, tuple)):
        if len(p) == 2: return (float(p[0]), float(p[1]), 0.0)
        if len(p) >= 3: return (float(p[0]), float(p[1]), float(p[2]))
    return (0.0, 0.0, 0.0)
