# matchEngine/choice_controller.py
from typing import List, Tuple, Optional, Any, Dict

XYZ    = Tuple[float, float, float]
Action = Tuple[str, Optional[str]]      # ("section","subtype")
DoCall = Tuple[str, Action, XYZ, XYZ]   # (player_id, action, location, target)

# All real logic lives elsewhere:
from .tactics  import for_state
from .roles    import resolve_role, team_candidates
from .availability import is_up, replace_if_down
from .choices  import choose_for_role, choose_team_instruction

def plan(match, state_tuple, tactics) -> List[DoCall]:
    """
    Coordinating loop:
      - read state+tactics
      - run individual choices first (with availability + replacement)
      - run team instructions for everyone else
      - return [(player_id, action, location_xyz, target_xyz), ...]
    Works for ANY state tag (events included). For non-in_play tags, the
    role/choice modules decide who acts and what to do; we don't rely on holder.
    """
    tag, location, ctx = state_tuple

    stx: Dict[str, Any]      = for_state(tactics, state_tuple) or {}
    individuals: Dict[str, Any] = stx.get("individual", {})
    team_cfg: Dict[str, Any]    = stx.get("team", {})
    critical_roles               = stx.get("critical_roles", [])

    used: set[str] = set()
    calls: List[DoCall] = []

    # 1) Individual roles (e.g., rn_9, rn_10)
    for role_key, role_cfg in individuals.items():
        pid = resolve_role(match, state_tuple, role_key)
        pid = replace_if_down(match, state_tuple, pid, role_key, critical_roles, used)
        if not pid or not is_up(match, pid, state_tuple):
            continue

        action, target = choose_for_role(match, pid, state_tuple, role_cfg)
        if not action or target is None:
            continue

        calls.append((pid, action, location, target))
        used.add(pid)

    # 2) Team instructions (everyone else, subject to team_cfg)
    for pid in team_candidates(match, state_tuple, exclude=list(used), cfg=team_cfg):
        if not is_up(match, pid, state_tuple):
            continue

        action, target = choose_team_instruction(match, pid, state_tuple, team_cfg)
        if not action or target is None:
            continue

        calls.append((pid, action, location, target))
        used.add(pid)

    return calls
