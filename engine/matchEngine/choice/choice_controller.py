# matchEngine/choice/choice_controller.py
from typing import List, Tuple, Optional
from utils.actions.catch_windows import best_catcher
from utils.player.locked_defender import update as update_locked_defender  # ⬅️ NEW
from choice.general.kick_chase import plan as kick_chase_plan
from states.open_play import OPEN_PLAY_TAGS
from .individual import ball_holder_choices as bh_choices
from .individual import locked_defender_choices as ld_choices
from choice.general.attack_choices import plan as attack_plan
from choice.general.defender_choices import plan as defend_plan
from choice.open_play import scramble as op_scramble
from choice.open_play import phase as op_phase
from choice.open_play import joue as op_joue
XYZ    = Tuple[float, float, float]
Action = Tuple[str, Optional[str]]
DoCall = Tuple[str, Action, XYZ, XYZ]

def _xyz(p) -> XYZ:
    if p is None: return (0.0, 0.0, 0.0)
    if isinstance(p, (list, tuple)):
        if len(p) == 2: return (float(p[0]), float(p[1]), 0.0)
        if len(p) >= 3: return (float(p[0]), float(p[1]), float(p[2]))
    return (0.0, 0.0, 0.0)

def _holder_id(match) -> Optional[str]:
    hid = getattr(match.ball, "holder", None)
    return hid if isinstance(hid, str) and len(hid) >= 2 else None

def _is(tag: object, prefix: str) -> bool:
    return isinstance(tag, str) and (tag == prefix or tag.startswith(prefix + "."))

from states.open_play import OPEN_PLAY_TAGS

def select(match, state_tuple) -> List[DoCall]:
    tag, loc, ctx = state_tuple

    # --- UNIVERSAL CATCH HOOK (before the gate) ---
    ball = match.ball
    if getattr(ball, "holder", None) is None:
        bx, by, bz = ball.location
        catcher = best_catcher(match.players, (bx, by, bz), radius=1.0, max_height=1.6)
        if catcher:
            pid = f"{catcher.sn}{catcher.team_code}"
            return [(pid, ("catch", None), _xyz(catcher.location), (bx, by, bz))]

    # --- explicit routers for open-play facets (early return) ---
    if isinstance(tag, str):
        if tag.startswith("open_play.scramble"):
            return op_scramble.plan(match, state_tuple)
        if tag.startswith("open_play.kick_chase"):
            return kick_chase_plan(match, state_tuple)
        if tag.startswith("open_play.phase_play"):
            return op_phase.plan(match, state_tuple)
        if tag.startswith("open_play.line_break"):
            return op_joue.plan(match, state_tuple)      # TODO: dedicated plan later
        if tag.startswith("open_play.turnover"):
            return op_joue.plan(match, state_tuple)      # TODO: dedicated plan later

    # --- OPEN-PLAY GATE for generic logic below ---
    if not (isinstance(tag, str) and (
        tag in OPEN_PLAY_TAGS or tag.startswith("open_play.") or tag.startswith("in_play.")
    )):
        return []

    calls: List[DoCall] = []

    # 1) Holder action (if any)
    holder = _holder_id(match)
    if holder:
        action, target = bh_choices.choose(match, holder, state_tuple)
        if action and target is not None:
            ploc = match.get_player_by_code(holder).location
            calls.append((holder, action, _xyz(ploc), _xyz(target)))

    # 2) Locked defender
    ld_id = update_locked_defender(match, tag)
    if ld_id:
        action, target = ld_choices.choose(match, ld_id, state_tuple)
        if action and target is not None:
            ploc = match.get_player_by_code(ld_id).location
            calls.append((ld_id, action, _xyz(ploc), _xyz(target)))

    # 3) Team plans
    already = {pid for (pid, *_rest) in calls}
    for pid, action, _l, t in [*(attack_plan(match, state_tuple) or []),
                               *(defend_plan(match, state_tuple) or [])]:
        if pid in already:
            continue
        ploc = match.get_player_by_code(pid).location
        # optional offside retreat (ensure your player object really has .flags)
        if getattr(match.get_player_by_code(pid), "flags", {}).get("offside", False):
            hid = _holder_id(match)
            same_team_as_holder = (hid and
                match.get_player_by_code(pid).team is match.get_player_by_code(hid).team)
            if not same_team_as_holder:
                action, t = ("move", None), (match.ball.location[0] - match.get_player_by_code(pid).team.direction*0.8,
                                             ploc[1], 0.0)
        calls.append((pid, action, _xyz(ploc), _xyz(t)))

    return calls
