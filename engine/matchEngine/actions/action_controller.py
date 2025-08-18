# matchEngine/actions/action_controller.py
from typing import Any, Optional, Tuple
from . import pass_action
from . import kick
from . import movement
from . import catch
from . import enter_contact

XYZ    = Tuple[float, float, float]
Action = Tuple[str, Optional[str]]  # ("section","subtype"), e.g. ("pass","flat")

_SECTION_TO_MODULE = {
    "pass":    pass_action,
    "kick":    kick,
    "move":     movement,
    "catch":   catch,
    "contact": enter_contact,
}

def do_action(match, player_id, action, location, target):
    """
    Minimal router. Modules do the work.
    location: (x, y, z)
    target:   (x, y, z)   ← always 3D (z=0.0 for ground targets)
    """
    section, subtype = action
    mod = _SECTION_TO_MODULE[section]
    return mod.do_action(match, player_id, subtype, location, target)



""" this will split the actions doen by players based on what is received from descions and consult the relevant module to carry them out


whole function is is run action if action == available_action
ELSE ERROR HANDLE JUST call move to target
if no target call. idle 

takes player action moves the players and runs the probalistic fromulas from here
"""

