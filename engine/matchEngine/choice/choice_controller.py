# matchEngine/choice/choice_controller.py
from typing import List, Tuple, Optional

# tuple types we pass around
XYZ    = Tuple[float, float, float]
Action = Tuple[str, Optional[str]]      # ("section","subtype")
DoCall = Tuple[str, Action, XYZ, XYZ]   # (player_id, action, location, target)

# state gate (we only act in open play + sub-tags)
from states.open_play import OPEN_PLAY_TAGS

# individual choices
from .individual import ball_holder_choices as bh_choices
from .individual import locked_defender_choices as ld_choices

# team choices
from .team.attack_choices import plan as attack_plan
from .team.defender_choices import plan as defend_plan


def _xyz(p) -> XYZ:
    if p is None: return (0.0, 0.0, 0.0)
    if isinstance(p, (list, tuple)):
        if len(p) == 2: return (float(p[0]), float(p[1]), 0.0)
        if len(p) >= 3: return (float(p[0]), float(p[1]), float(p[2]))
    return (0.0, 0.0, 0.0)

def _locked_defender_id(match) -> Optional[str]:
    for p in match.players:
        if p.state_flags.get("locked_defender", False):
            return f"{p.sn}{p.team_code}"
    return None

def _holder_id(match) -> Optional[str]:
    hid = getattr(match.ball, "holder", None)
    return hid if isinstance(hid, str) and len(hid) >= 2 else None


def select(match, state_tuple) -> List[DoCall]:
    """
    Master choice router.
      - If ball held: use ball-holder choices for that player (single DoCall)
      - Else if a locked defender exists: use locked-defender choices (single DoCall)
      - Else: combine team attack + defence plans (List[DoCall])

    Returns: List[DoCall] compatible with action_controller.do_actions(...)
    """
    tag, loc, ctx = state_tuple
    loc_xyz = _xyz(loc)

    # Only operate in open play tags; return empty list otherwise.
    if not (isinstance(tag, str) and tag in OPEN_PLAY_TAGS):
        return []

    calls: List[DoCall] = []

    # 1) Ball-holder path
    holder = _holder_id(match)
    if holder:
        action, target = bh_choices.choose(match, holder, state_tuple)
        if action and target is not None:
            ploc = match.get_player_by_code(holder).location
            calls.append((holder, action, _xyz(ploc), _xyz(target)))
        return calls

    # 2) Locked-defender path
    ld = _locked_defender_id(match)
    if ld:
        action, target = ld_choices.choose(match, ld, state_tuple)
        if action and target is not None:
            ploc = match.get_player_by_code(ld).location
            calls.append((ld, action, _xyz(ploc), _xyz(target)))
        return calls

    # 3) Team plans (attack + defence) for everyone else
    normalized = []
    for pid, action, _l, t in [*(attack_plan(match, state_tuple) or []),
                            *(defend_plan(match, state_tuple) or [])]:
        ploc = match.get_player_by_code(pid).location
        normalized.append((pid, action, _xyz(ploc), _xyz(t)))
    return normalized

