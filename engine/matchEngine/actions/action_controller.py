from typing import Optional, Tuple
from . import pass_action, kick, movement, catch, ground, tackle , offload,tackled,clearout, jackal, picked # make sure these files exist

XYZ    = Tuple[float, float, float]
Action = Tuple[str, Optional[str]]  # ("section","subtype"), e.g. ("pass","flat")

_SECTION_TO_MODULE = {
    "pass":   pass_action,
    "kick":   kick,
    "move":   movement,
    "catch":  catch,
    "ground": ground,
    "tackle": tackle,  
    "offload": offload,
    "tackled": tackled,
    "clearout": clearout,
    "jackal":   jackal,
    "picked": picked,
}

def do_action(match, player_id, action, location, target):
    section, subtype = action
    mod = _SECTION_TO_MODULE[section]
    return mod.do_action(match, player_id, subtype, location, target)
