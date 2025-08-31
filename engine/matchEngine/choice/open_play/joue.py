# choice/open_play/joue.py
from typing import List, Tuple, Optional
from choice.general.attack_choices import plan as attack_plan
from choice.general.defender_choices import plan as defend_plan
from choice.individual import ball_holder_choices as bh_choices
from choice.individual import locked_defender_choices as ld_choices
from utils.player.locked_defender import update as update_locked_defender

Do = Tuple[str, Tuple[str, Optional[str]], tuple, tuple]  # (pid, (action, subtype), from_xyz, to_xyz)

def _xyz(p) -> tuple:
    if p is None: return (0.0, 0.0, 0.0)
    if isinstance(p, (list, tuple)):
        if len(p) == 2: return (float(p[0]), float(p[1]), 0.0)
        if len(p) >= 3: return (float(p[0]), float(p[1]), float(p[2]))
    return (0.0, 0.0, 0.0)

def _holder_id(match) -> Optional[str]:
    hid = getattr(match.ball, "holder", None)
    return hid if isinstance(hid, str) and len(hid) >= 2 else None

def plan(match, state_tuple) -> List[Do]:
    tag, _loc, _ctx = state_tuple
    calls: List[Do] = []

    # 1) Ball-holder individual choice (run/kick/pass/offload/ground as your chooser decides)
    holder = _holder_id(match)
    if holder:
        h = match.get_player_by_code(holder)
        action, target = bh_choices.choose(match, holder, state_tuple)
        if action and target is not None and h is not None:
            calls.append((holder, action, _xyz(h.location), _xyz(target)))

    # 2) Lock one defender (nearest live threat) and give *their* individual choice
    ld_id = update_locked_defender(match, tag)  # sets flags and returns defender id (or None)
    if ld_id:
        d = match.get_player_by_code(ld_id)
        action, target = ld_choices.choose(match, ld_id, state_tuple)
        if action and target is not None and d is not None:
            calls.append((ld_id, action, _xyz(d.location), _xyz(target)))

    # 3) Team-level shaping (general open-play, not phase-shape)
    already = {pid for (pid, *_rest) in calls}

    team_calls: List[Do] = []
    team_calls += attack_plan(match, state_tuple) or []
    team_calls += defend_plan(match, state_tuple) or []

    for pid, action, loc_from, loc_to in team_calls:
        if pid in already:
            continue
        # refresh from current position so we don't teleport from stale loc
        pl = match.get_player_by_code(pid)
        loc_from = _xyz(pl.location) if pl else _xyz(loc_from)
        calls.append((pid, action, loc_from, loc_to))

    return calls
