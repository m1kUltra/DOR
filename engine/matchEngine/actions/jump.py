from typing import Optional, Tuple
import math
import random

from . import catch
from utils.actions.jump_helpers import (
    standing_jump,
    running_jump,
    total_vertical_reach,
    lateral_catch_radius,
)

XYZ = Tuple[float, float, float]


def do_action(match, player_id: str, subtype: Optional[str], location: XYZ, target: XYZ) -> bool:
    """Attempt to catch a high ball via a jump."""
    player = match.get_player_by_code(player_id)
    if not player:
        return False

    bx, by, bz = target
    px, py, _ = player.location
    dx, dy = bx - px, by - py
    offset = math.hypot(dx, dy)
    radius = lateral_catch_radius(player)

    # Choose jump height based on movement or subtype
    if subtype == "running" or getattr(player, "current_speed", 0.0) > 1.0:
        jump_h = running_jump(player)
    else:
        jump_h = standing_jump(player)

    reach = total_vertical_reach(player, jump_h)

    # Cannot reach vertically or laterally
    if bz > reach or offset > radius:
        return catch.do_action(match, player_id, "fail", location, target)

    # Difficulty scaling: farther offsets reduce success chance
    ratio = offset / radius if radius > 0 else 1.0
    base = player.norm_attributes.get("handling", 0.5)
    success_prob = max(0.0, min(1.0, base * (1.0 - ratio)))

    if random.random() <= success_prob:
        return catch.do_action(match, player_id, None, location, target)
    else:
        return catch.do_action(match, player_id, "drop", location, target)